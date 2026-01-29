"""Utility functions for JavaScript code analysis."""

from collections import defaultdict
from typing import Any

import esprima

from llm_cgr.analyse.languages.code_data import CodeData


NODEJS_BUILTINS = frozenset(
    {
        "assert",
        "async_hooks",
        "buffer",
        "child_process",
        "cluster",
        "console",
        "constants",
        "crypto",
        "dgram",
        "dns",
        "domain",
        "events",
        "fs",
        "http",
        "http2",
        "https",
        "inspector",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "punycode",
        "querystring",
        "readline",
        "repl",
        "stream",
        "string_decoder",
        "sys",
        "timers",
        "tls",
        "trace_events",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "wasi",
        "worker_threads",
        "zlib",
    }
)


class JavaScriptAnalyser:
    """Analyses JavaScript AST to extract import and usage information."""

    def __init__(self) -> None:
        self.std_libs: set[str] = set()
        self.ext_libs: set[str] = set()
        self.imports: dict[str, str] = {}
        self.lib_usage: defaultdict[str, list[dict]] = defaultdict(list)

    def visit(self, node: Any) -> None:
        """Recursively visit all nodes in the AST."""
        if node is None:
            return

        if isinstance(node, esprima.nodes.Node):
            node_type = node.type
            handler = getattr(self, f"visit_{node_type}", None)
            if handler:
                handler(node)

            for key in dir(node):
                if key.startswith("_"):
                    continue
                child = getattr(node, key)
                if isinstance(child, list):
                    for item in child:
                        self.visit(item)
                elif isinstance(child, esprima.nodes.Node):
                    self.visit(child)

    def visit_ImportDeclaration(self, node: Any) -> None:
        """Handle import declarations."""
        source = node.source.value
        top_level = source.split("/")[0]

        if top_level.startswith("."):
            pass
        elif top_level in NODEJS_BUILTINS or source.startswith("node:"):
            clean_name = top_level.removeprefix("node:")
            self.std_libs.add(clean_name)
        else:
            if top_level.startswith("@"):
                parts = source.split("/")
                clean_name = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
            else:
                clean_name = top_level
            self.ext_libs.add(clean_name)

        for specifier in node.specifiers:
            if specifier.type == "ImportDefaultSpecifier":
                local_name = specifier.local.name
                self.imports[local_name] = source
            elif specifier.type == "ImportSpecifier":
                local_name = specifier.local.name
                imported_name = specifier.imported.name
                self.imports[local_name] = f"{source}.{imported_name}"
            elif specifier.type == "ImportNamespaceSpecifier":
                local_name = specifier.local.name
                self.imports[local_name] = source

    def visit_CallExpression(self, node: Any) -> None:
        """Handle function call expressions."""
        full_name = self._resolve_callee(node.callee)

        if full_name:
            library, _, function = full_name.partition(".")
            arg_strs = [self._unparse_node(arg) for arg in node.arguments]

            self.lib_usage[library].append(
                {
                    "type": "call",
                    "member": function,
                    "args": arg_strs,
                    "kwargs": {},
                }
            )

    def visit_MemberExpression(self, node: Any) -> None:
        """Handle member access expressions."""
        if node.parent_is_call:
            return

        full_name = self._resolve_member(node)
        if full_name:
            library, _, member = full_name.partition(".")
            self.lib_usage[library].append(
                {
                    "type": "access",
                    "member": member,
                }
            )

    def _resolve_callee(self, node: Any) -> str | None:
        """Resolve the full name of a call expression callee."""
        if node.type == "Identifier":
            if node.name in self.imports:
                return self.imports[node.name]
            return None

        if node.type == "MemberExpression":
            return self._resolve_member(node)

        return None

    def _resolve_member(self, node: Any) -> str | None:
        """Resolve the full module path for a member expression."""
        parts: list[str] = []
        current = node

        while current.type == "MemberExpression":
            if current.computed:
                return None
            parts.append(current.property.name)
            current = current.object

        if current.type == "Identifier" and current.name in self.imports:
            base = self.imports[current.name]
            path = ".".join([base] + list(reversed(parts)))
            return path

        return None

    def _unparse_node(self, node: Any) -> str:
        """Convert an AST node back to source code representation."""
        if node.type == "Literal":
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        elif node.type == "Identifier":
            return node.name
        elif node.type == "MemberExpression":
            obj = self._unparse_node(node.object)
            prop = self._unparse_node(node.property)
            if node.computed:
                return f"{obj}[{prop}]"
            return f"{obj}.{prop}"
        elif node.type == "CallExpression":
            callee = self._unparse_node(node.callee)
            args = ", ".join(self._unparse_node(arg) for arg in node.arguments)
            return f"{callee}({args})"
        elif node.type == "ArrayExpression":
            elements = ", ".join(self._unparse_node(el) for el in node.elements if el)
            return f"[{elements}]"
        elif node.type == "ObjectExpression":
            props = []
            for prop in node.properties:
                key = self._unparse_node(prop.key)
                value = self._unparse_node(prop.value)
                props.append(f"{key}: {value}")
            return "{" + ", ".join(props) + "}"
        elif node.type == "ArrowFunctionExpression":
            return "<arrow function>"
        elif node.type == "FunctionExpression":
            return "<function>"
        elif node.type == "TemplateLiteral":
            return "<template literal>"
        elif node.type == "SpreadElement":
            return f"...{self._unparse_node(node.argument)}"

        return f"<{node.type}>"


def _mark_call_parents(node: Any, parent_is_call: bool = False) -> None:
    """Mark MemberExpression nodes that are direct callees."""
    if node is None:
        return

    if isinstance(node, esprima.nodes.Node):
        node.parent_is_call = parent_is_call

        for key in dir(node):
            if key.startswith("_"):
                continue
            child = getattr(node, key)

            is_callee = node.type == "CallExpression" and key == "callee"

            if isinstance(child, list):
                for item in child:
                    _mark_call_parents(item, False)
            elif isinstance(child, esprima.nodes.Node):
                _mark_call_parents(child, is_callee)


def analyse_javascript_code(code: str) -> CodeData:
    """
    Analyse JavaScript code to extract imports and library usage.

    Returns a CodeData object with import and usage information.
    """
    try:
        tree = esprima.parseModule(code, {"loc": True})
    except esprima.Error as e:
        return CodeData(
            valid=False,
            error=str(e),
        )

    _mark_call_parents(tree)

    analyser = JavaScriptAnalyser()
    analyser.visit(tree)

    lib_usage: dict[str, list[dict]] = {}
    for library, usage in analyser.lib_usage.items():
        lib_usage[library] = []
        all_members = [u["member"] for u in usage]
        call_members = [u["member"] for u in usage if u["type"] == "call"]
        for record in usage:
            if record["type"] == "access":
                if record["member"] in call_members or any(
                    m.startswith(f"{record['member']}.") for m in all_members
                ):
                    continue

            lib_usage[library].append(record)

    return CodeData(
        valid=True,
        std_libs=analyser.std_libs,
        ext_libs=analyser.ext_libs,
        imports=set(analyser.imports.values()),
        lib_usage=lib_usage,
    )
