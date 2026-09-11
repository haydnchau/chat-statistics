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
import threading
import time
import webbrowser
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


# Resolved full paths, filled in by check_node()/check_npm(). On Windows,
# npm/npx are .cmd shim scripts, not real executables -- subprocess can only
# launch them without shell=True if given the exact resolved path (plain
# "npm" fails with WinError 2 even though shutil.which finds it fine).
NODE_PATH = None
NPM_PATH = None


def check_node():
    global NODE_PATH
    NODE_PATH = shutil.which("node")
    if NODE_PATH is None:
        print("✗ Node.js not found.")
        print("   Fix: install from https://nodejs.org (LTS) or via nvm")
        return False
    version = _run([NODE_PATH, "--version"])  # e.g. "v20.11.0"
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
    global NPM_PATH
    NPM_PATH = shutil.which("npm")
    if NPM_PATH is None:
        print("✗ npm not found (usually ships with Node.js).")
        return False
    version = _run([NPM_PATH, "--version"])
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
        proc = subprocess.run([NPM_PATH, "install"], cwd=SITE_DIR)
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
    if not all(checks):
        print("Fix the items marked ✗ above, then re-run this script.")
        sys.exit(1)

    print("Everything looks good.")
    print("Tip: run `python3 process_chat.py` any time to add a chat --")
    print("     before or after the site starts, then just refresh the page.\n")
    launch_dev_server()


def launch_dev_server(port=5173):
    print("Starting the local site (Ctrl+C to stop)...")
    proc = subprocess.Popen([NPM_PATH, "run", "dev"], cwd=SITE_DIR)
    threading.Timer(2.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()