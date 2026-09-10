#!/usr/bin/env python3
"""
Run this first: python3 check_setup.py

Verifies the machine has what's needed to process chats and run the
React stats site, and offers to fix anything missing.
"""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

SITE_DIR = Path(__file__).parent / "site"

# Stdlib-only for now -- process_chat.py doesn't need third-party packages.
# Keep this list here so it's easy to extend later (e.g. nltk, wordfreq).
REQUIRED_PY_PACKAGES = []

MIN_NODE_MAJOR = 18


def check_python_packages():
    missing = []
    for pkg in REQUIRED_PY_PACKAGES:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        print(f"✗ Missing Python packages: {', '.join(missing)}")
        print(f"   Fix: pip install {' '.join(missing)}")
        return False
    print("✓ Python packages OK" + (" (none required yet)" if not REQUIRED_PY_PACKAGES else ""))
    return True


def _run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def check_node():
    if shutil.which("node") is None:
        print("✗ Node.js not found.")
        print("   Fix: install from https://nodejs.org (LTS) or via nvm")
        return False
    version = _run(["node", "--version"])  # e.g. "v20.11.0"
    if not version:
        print("✗ Could not run `node --version`")
        return False
    major = int(version.lstrip("v").split(".")[0])
    if major < MIN_NODE_MAJOR:
        print(f"✗ Node {version} found, but {MIN_NODE_MAJOR}+ is required.")
        return False
    print(f"✓ Node {version} OK")
    return True


def check_npm():
    if shutil.which("npm") is None:
        print("✗ npm not found (usually ships with Node.js).")
        return False
    version = _run(["npm", "--version"])
    print(f"✓ npm {version} OK")
    return True


def check_site_deps():
    if not SITE_DIR.exists():
        print("✗ site/ folder not found -- is this script in the project root?")
        return False
    node_modules = SITE_DIR / "node_modules"
    if node_modules.exists():
        print("✓ site/node_modules already installed")
        return True
    print("✗ site/node_modules missing (React app dependencies not installed)")
    answer = input("   Run `npm install` in site/ now? [y/N] ").strip().lower()
    if answer == "y":
        proc = subprocess.run(["npm", "install"], cwd=SITE_DIR)
        if proc.returncode == 0:
            print("✓ npm install succeeded")
            return True
        print("✗ npm install failed -- see output above")
        return False
    print("   Skipped. Run `npm install` inside site/ manually before starting the site.")
    return False


def main():
    print("Checking your setup...\n")
    checks = [
        check_python_packages(),
        check_node(),
        check_npm(),
    ]
    # Only bother checking/installing JS deps if node+npm exist
    if checks[1] and checks[2]:
        checks.append(check_site_deps())

    print()
    if all(checks):
        print("Everything looks good. Next steps:")
        print("  1. python3 process_chat.py     # pick a chat, generate its stats")
        print("  2. cd site && npm run dev      # launch the local site")
    else:
        print("Fix the items marked ✗ above, then re-run this script.")
        sys.exit(1)


if __name__ == "__main__":
    main()
