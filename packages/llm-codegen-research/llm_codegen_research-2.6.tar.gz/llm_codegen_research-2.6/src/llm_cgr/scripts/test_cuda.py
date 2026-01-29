#!/usr/bin/env python3
"""Comprehensive CUDA and PyTorch installation checker for HPC environments.

This script performs a thorough diagnostic check of PyTorch and CUDA installations,
specifically designed for HPC (High-Performance Computing) environments where GPU
availability and configuration are critical.

Usage:
    python check_cuda.py

The script checks and reports:
    - Python and system environment
    - PyTorch installation and versions
    - CUDA availability and GPU devices
    - Memory usage and functionality test
"""

import platform
import sys


def main():
    """Run all checks."""
    print("=" * 60)
    print(" PyTorch & CUDA Check")
    print("=" * 60)

    # Python environment
    print(f"\nPython: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")

    # PyTorch
    try:
        import torch  # type: ignore

        print(f"\nPyTorch: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"cuDNN version: {torch.backends.cudnn.version()}")

            device_count = torch.cuda.device_count()
            current = torch.cuda.current_device()
            print(f"\nGPUs detected: {device_count}")
            print(f"Current device: {current}")

            for i in range(device_count):
                marker = " <--" if i == current else ""
                props = torch.cuda.get_device_properties(i)
                mem_alloc = torch.cuda.memory_allocated(i) / 1024**3
                mem_total = props.total_memory / 1024**3

                print(f"\n  GPU {i}: {torch.cuda.get_device_name(i)}{marker}")
                print(f"    Compute capability: {props.major}.{props.minor}")
                print(f"    Memory: {mem_alloc:.2f} / {mem_total:.2f} GB")

            # Quick functionality test
            try:
                x = torch.randn(3, 3).cuda()
                y = x @ x.T
                print(f"\n✓ CUDA operations working ({y=})")
            except Exception as e:
                print(f"\n✗ CUDA test failed: {e}")

        else:
            print("\n⚠ CUDA not available")
            if hasattr(torch.version, "cuda") and torch.version.cuda is None:
                print("  (PyTorch built without CUDA support)")

        # Check other backends
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("\nMPS (Apple Silicon): Available")

    except ImportError as e:
        print(f"\n✗ PyTorch not installed: {e}")
        return

    finally:
        print("\n" + ("=" * 60) + "\n")


if __name__ == "__main__":
    main()
