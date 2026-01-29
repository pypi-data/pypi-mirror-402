#!/usr/bin/env python3
"""
Venv Health Check
=================

Diagnoses common venv issues like corrupted metadata, missing packages,
and version mismatches.

Usage:
    python scripts/check-venv.py
    python scripts/check-venv.py --fix  # Attempt auto-fix
"""

import importlib
import importlib.metadata
import sys
from pathlib import Path


def check_package(name: str, import_name: str = None) -> tuple[bool, str]:
    """Check if a package is properly installed and importable."""
    import_name = import_name or name.replace("-", "_")

    try:
        # Check if metadata is accessible
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False, f"Not installed (metadata missing)"
    except Exception as e:
        return False, f"Metadata error: {e}"

    try:
        # Check if package is importable
        module = importlib.import_module(import_name)
        module_version = getattr(module, "__version__", "unknown")
        if module_version != "unknown" and module_version != version:
            return False, f"Version mismatch: metadata={version}, module={module_version}"
        return True, f"OK (v{version})"
    except ImportError as e:
        return False, f"Import failed: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("Venv Health Check")
    print("=" * 50)
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print()

    # Core packages to check
    packages = [
        ("pydantic", "pydantic"),
        ("pydantic-core", "pydantic_core"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pyyaml", "yaml"),
        ("httpx", "httpx"),
        ("aiosqlite", "aiosqlite"),
    ]

    # Check if we're in the right project
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"

    if pyproject.exists():
        print(f"Project: {project_root}")
        # Try to check omni-cortex
        packages.insert(0, ("omni-cortex", "omni_cortex"))
    print()

    all_ok = True
    issues = []

    print("Package Status:")
    print("-" * 50)
    for pkg_name, import_name in packages:
        ok, status = check_package(pkg_name, import_name)
        symbol = "✓" if ok else "✗"
        print(f"  {symbol} {pkg_name}: {status}")
        if not ok:
            all_ok = False
            issues.append((pkg_name, status))

    print()

    if all_ok:
        print("✓ All packages healthy!")
    else:
        print("✗ Issues detected:")
        print()
        for pkg, issue in issues:
            print(f"  - {pkg}: {issue}")
        print()
        print("Suggested fixes:")
        print("  1. Try force-reinstall: uv pip install --force-reinstall <package>")
        print("  2. Rebuild venv: rm -rf .venv && uv venv && uv pip install -e .")
        print("  3. Use system pip: pip install -e . --force-reinstall")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
