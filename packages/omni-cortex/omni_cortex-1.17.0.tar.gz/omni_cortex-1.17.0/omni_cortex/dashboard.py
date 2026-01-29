"""Dashboard CLI for Omni-Cortex.

Starts the web dashboard server for viewing and managing memories.
"""

import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from time import sleep


def check_editable_install() -> bool:
    """Check if package is installed in editable (development) mode.

    Returns True if editable, False if installed from PyPI.
    """
    try:
        import importlib.metadata as metadata
        dist = metadata.distribution("omni-cortex")
        # Editable installs have a direct_url.json with editable=true
        # or are installed via .egg-link
        direct_url = dist.read_text("direct_url.json")
        if direct_url and '"editable":true' in direct_url.replace(" ", ""):
            return True
    except Exception:
        pass

    # Alternative check: see if we're running from source directory
    package_dir = Path(__file__).parent
    repo_root = package_dir.parent.parent
    if (repo_root / "pyproject.toml").exists() and (repo_root / ".git").exists():
        # We're in a repo, check if there's an egg-link or editable marker
        import site
        for site_dir in [site.getusersitepackages()] + site.getsitepackages():
            egg_link = Path(site_dir) / "omni-cortex.egg-link"
            if egg_link.exists():
                return True
            # Check for __editable__ marker (PEP 660) - any version
            for pth_file in Path(site_dir).glob("__editable__.omni_cortex*.pth"):
                return True

    return False


def warn_non_editable_install() -> None:
    """Warn if not running in editable mode during development."""
    if not check_editable_install():
        # Check if we appear to be in a development context
        package_dir = Path(__file__).parent
        repo_root = package_dir.parent.parent
        if (repo_root / "pyproject.toml").exists() and (repo_root / ".git").exists():
            print("[Dashboard] Note: Package may not be in editable mode.")
            print("[Dashboard] If you see import errors, run: pip install -e .")
            print()


def find_dashboard_dir() -> Path | None:
    """Find the dashboard directory.

    Searches in order:
    1. Development directory (cloned repo)
    2. Package shared-data (installed via pip)
    3. Site-packages share location
    """
    package_dir = Path(__file__).parent

    # Check for development directory (repo structure)
    # Go up from src/omni_cortex to repo root, then dashboard
    repo_root = package_dir.parent.parent
    dashboard_in_repo = repo_root / "dashboard"
    if dashboard_in_repo.exists() and (dashboard_in_repo / "backend" / "main.py").exists():
        return dashboard_in_repo

    # Check pip shared-data location
    # On Unix: ~/.local/share/omni-cortex/dashboard
    # On Windows: %APPDATA%/Python/share/omni-cortex/dashboard
    import site
    for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
        share_dir = Path(site_dir).parent / "share" / "omni-cortex" / "dashboard"
        if share_dir.exists() and (share_dir / "backend" / "main.py").exists():
            return share_dir

    # Check relative to sys.prefix (virtualenv)
    share_in_prefix = Path(sys.prefix) / "share" / "omni-cortex" / "dashboard"
    if share_in_prefix.exists() and (share_in_prefix / "backend" / "main.py").exists():
        return share_in_prefix

    return None


def check_dependencies() -> bool:
    """Check if dashboard dependencies are installed."""
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401
        return True
    except ImportError:
        return False


def install_dependencies() -> bool:
    """Install dashboard dependencies."""
    required_packages = ["uvicorn", "fastapi"]

    print("[Dashboard] Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *required_packages, "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def start_server(dashboard_dir: Path, host: str, port: int, no_browser: bool) -> None:
    """Start the dashboard server."""
    backend_dir = dashboard_dir / "backend"

    # Add backend to path
    sys.path.insert(0, str(backend_dir))

    # Change to backend directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(backend_dir)

    try:
        import uvicorn

        print(f"\n[Dashboard] Starting Omni-Cortex Dashboard")
        print(f"[Dashboard] URL: http://{host}:{port}")
        print(f"[Dashboard] API Docs: http://{host}:{port}/docs")
        print(f"[Dashboard] Press Ctrl+C to stop\n")

        # Open browser after short delay
        if not no_browser:
            def open_browser():
                sleep(1.5)
                webbrowser.open(f"http://{host}:{port}")

            import threading
            threading.Thread(target=open_browser, daemon=True).start()

        # Run the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point for omni-cortex dashboard command."""
    # Check for potential editable install issues early
    warn_non_editable_install()

    parser = argparse.ArgumentParser(
        description="Start the Omni-Cortex web dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  omni-cortex dashboard              Start on default port 8765
  omni-cortex dashboard --port 9000  Start on custom port
  omni-cortex dashboard --no-browser Don't auto-open browser
        """
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8765,
        help="Port to run on (default: 8765)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )

    args = parser.parse_args()

    # Find dashboard directory
    dashboard_dir = find_dashboard_dir()
    if not dashboard_dir:
        print("[Dashboard] Error: Dashboard files not found.")
        print("[Dashboard] If you installed via pip, try reinstalling:")
        print("  pip install --force-reinstall omni-cortex")
        print("\nOr clone the repository:")
        print("  git clone https://github.com/AllCytes/Omni-Cortex.git")
        sys.exit(1)

    print(f"[Dashboard] Found dashboard at: {dashboard_dir}")

    # Check/install dependencies
    if not check_dependencies():
        print("[Dashboard] Installing required dependencies...")
        if not install_dependencies():
            print("[Dashboard] Error: Failed to install dependencies.")
            print("[Dashboard] Try manually: pip install uvicorn fastapi")
            sys.exit(1)

    # Check if dist exists (built frontend)
    dist_dir = dashboard_dir / "frontend" / "dist"
    if not dist_dir.exists():
        print(f"[Dashboard] Warning: Frontend not built ({dist_dir})")
        print("[Dashboard] API will work but web UI may not be available.")
        print("[Dashboard] To build: cd dashboard/frontend && npm install && npm run build")

    # Start the server
    try:
        start_server(dashboard_dir, args.host, args.port, args.no_browser)
    except KeyboardInterrupt:
        print("\n[Dashboard] Stopped")
    except Exception as e:
        print(f"[Dashboard] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
