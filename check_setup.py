#!/usr/bin/env python3
"""
Run this first: python3 check_setup.py

Verifies the machine has what's needed to process chats and run the
React stats site, and offers to fix anything missing.
"""
import importlib.util
import json
import platform
import shlex
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

SITE_DIR = Path(__file__).parent / "site"
CONFIG_PATH = Path(__file__).parent / ".chatstats_config.json"

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


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def check_inbox_path():
    """
    Asks once for the path to the person's downloaded Instagram export and
    remembers it in .chatstats_config.json, so process_chat.py doesn't need
    the path typed/pasted in on every single run afterward.
    """
    config = load_config()
    saved = config.get("inbox_path")

    if saved and Path(saved).expanduser().exists():
        print(f"✓ Instagram export path saved: {saved}")
        answer = input("   Change it? [y/N] ").strip().lower()
        if answer != "y":
            return True
    elif saved:
        print(f"✗ Saved Instagram export path no longer exists: {saved}")

    path = input(
        "\nPaste the path to your downloaded Instagram export\n"
        "(the folder containing messages/inbox, or the inbox folder itself.\n"
        "Leave blank to skip and enter it manually later): "
    ).strip()

    if not path:
        print("   Skipped. You'll need to pass the path to process_chat.py yourself.")
        return True

    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        print(f"✗ That path doesn't exist: {resolved}")
        return False

    config["inbox_path"] = str(resolved)
    save_config(config)
    print(f"✓ Saved. process_chat.py will use this automatically from now on.")
    return True


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

    print("Everything looks good.\n")
    check_inbox_path()

    print("\nTip: run `python3 process_chat.py` any time to add a chat --")
    print("     before or after the site starts, then just refresh the page.\n")
    launch_dev_server()


def launch_dev_server(port=5173):
    system = platform.system()
    npm_cmd = f"{shlex.quote(NPM_PATH)} run dev"
    site_dir = str(SITE_DIR)

    try:
        if system == "Windows":
            # Launch npm.cmd directly in a brand-new console window. This
            # avoids shelling out through `cmd /k "..."` entirely, which was
            # breaking silently: shlex.quote() (used below for macOS/Linux)
            # produces POSIX-style single-quoting, but cmd.exe doesn't
            # understand single quotes -- any path with a space in it
            # (e.g. under "Program Files") broke the whole command.
            subprocess.Popen(
                [NPM_PATH, "run", "dev"],
                cwd=site_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        elif system == "Darwin":
            script = f"cd {shlex.quote(site_dir)} && {npm_cmd}"
            osa = f'tell application "Terminal" to do script "{script}"'
            subprocess.Popen(["osascript", "-e", osa])

        else:  # Linux / other Unix
            inner = f"cd {shlex.quote(site_dir)} && {npm_cmd}; exec $SHELL"
            terminal = next(
                (t for t in ["x-terminal-emulator", "gnome-terminal", "konsole",
                              "xfce4-terminal", "xterm"] if shutil.which(t)),
                None,
            )
            if terminal is None:
                raise RuntimeError("no terminal emulator found on this system")
            if terminal == "gnome-terminal":
                subprocess.Popen([terminal, "--", "bash", "-c", inner])
            else:
                subprocess.Popen([terminal, "-e", f"bash -c {shlex.quote(inner)}"])

    except Exception as e:
        print(f"✗ Couldn't open a new terminal window automatically ({e}).")
        print("   Starting it here instead -- this terminal will stay busy while it runs.")
        proc = subprocess.Popen([NPM_PATH, "run", "dev"], cwd=SITE_DIR)
        threading.Timer(2.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
        return

    print(f"✓ Site starting in a new window (http://localhost:{port}).")
    print("  This terminal is free -- you can run process_chat.py here now.")
    threading.Timer(3.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    time.sleep(3.5)  # give the browser-open timer a moment to fire before exiting


if __name__ == "__main__":
    main()