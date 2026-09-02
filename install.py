#!/usr/bin/env python3
"""
Wiz Health Assessment & Skills - cross-platform installer.

This is the single entry point for every platform:

    Windows          python install.py
    macOS / Linux    python3 install.py

install.sh (bash) and install.ps1 (PowerShell) are thin wrappers that locate a
suitable interpreter and delegate here, so all three routes behave identically.

Steps:
  1. Verify the running Python is new enough.
  2. Install the Python dependencies into *this* interpreter.
  3. Hand off to scripts/install_skills.py to install the skills and, if
     needed, launch the credentials wizard.

Options:
  --skip-deps            Do not install Python dependencies.
  --skip-libreoffice     Do not install LibreOffice (offline PDF renderer).
  --target NAME          Skill target: claude, jetski, cursor, workspace, all.
  --yes                  Accept defaults; never prompt (for unattended installs).
  --skip-credentials     Do not launch the credentials wizard.
"""

import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from console_compat import enable_unicode_output, python_command  # noqa: E402

MIN_PYTHON = (3, 8)


def check_python_version():
    if sys.version_info < MIN_PYTHON:
        current = ".".join(str(p) for p in sys.version_info[:3])
        needed = ".".join(str(p) for p in MIN_PYTHON)
        print(f"[!] Python {needed}+ is required, but this is Python {current}.")
        print(f"    Interpreter: {sys.executable}")
        print("    Install a newer Python from https://www.python.org/downloads/")
        return False
    return True


def run_pip(args):
    """Run pip for the current interpreter. Returns (ok, combined_output)."""
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as exc:
        return False, str(exc)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def install_dependencies():
    """Install requirements.txt into the interpreter that will run the scripts.

    Deliberately uses `sys.executable -m pip` rather than a bare `pip`/`pip3`:
    on machines with several Pythons those can resolve to a different
    interpreter, installing the libraries where the scripts will never see them.
    """
    requirements = REPO_DIR / "requirements.txt"
    if not requirements.exists():
        print(f"[!] requirements.txt not found at {requirements} - skipping dependencies.")
        return True

    # The tool is pure standard library. If requirements.txt has no actual
    # package lines (comments/blank only), there is nothing to install - don't
    # invoke pip (which would be a no-op and can prompt on PEP 668 systems).
    pkg_lines = [
        ln.strip() for ln in requirements.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not pkg_lines:
        print("[*] No Python dependencies to install (tool uses the standard library only).")
        return True

    print("[*] Installing Python dependencies...")
    print(f"    Interpreter: {sys.executable}")

    ok, output = run_pip(["-r", str(requirements)])
    if ok:
        print("    [OK] Dependencies installed.")
        return True

    # Debian/Ubuntu and Homebrew mark their system Python as externally managed
    # (PEP 668) and refuse a plain install. A per-user install is the normal
    # way through, and it keeps us out of the system site-packages.
    if "externally-managed-environment" in output or "Permission denied" in output:
        print("    [*] System Python is protected; retrying as a per-user install...")
        ok, output = run_pip(["--user", "-r", str(requirements)])
        if ok:
            print("    [OK] Dependencies installed for the current user.")
            return True

    print("    [!] Could not install dependencies automatically.")
    for line in output.strip().splitlines()[-8:]:
        print(f"        {line}")
    print()
    print("    The skills will still install. To finish the dependencies, either")
    print("    install them for your user:")
    print(f"        {sys.executable} -m pip install --user -r requirements.txt")
    print("    or use a virtual environment:")
    if sys.platform == "win32":
        print(f"        {python_command()} -m venv .venv")
        print("        .venv\\Scripts\\activate")
    else:
        print(f"        {python_command()} -m venv .venv")
        print("        source .venv/bin/activate")
    print("        pip install -r requirements.txt")
    return False


def main():
    enable_unicode_output()

    print("=======================================================")
    print("     WIZ HEALTH ASSESSMENT & SKILLS INSTALLER          ")
    print("=======================================================")

    if not check_python_version():
        return 1

    args = sys.argv[1:]
    assume_yes = "--yes" in args or "-y" in args

    if "--skip-deps" in args:
        args = [a for a in args if a != "--skip-deps"]
        print("[*] Skipping dependency installation (--skip-deps).")
    else:
        install_dependencies()

    # LibreOffice is the offline (Google-free) PPTX -> PDF renderer. It is a
    # system package, so it is provisioned here rather than via requirements.txt.
    # Consumed locally and NOT forwarded to install_skills.py.
    if "--skip-libreoffice" in args:
        args = [a for a in args if a != "--skip-libreoffice"]
        print("[*] Skipping LibreOffice install (--skip-libreoffice).")
    else:
        print()
        try:
            from ensure_libreoffice import ensure_libreoffice  # noqa: E402
            ensure_libreoffice(assume_yes=assume_yes)
        except Exception as exc:
            print(f"[!] LibreOffice provisioning skipped ({exc}). PPTX + CSV still work.")

    installer = SCRIPTS_DIR / "install_skills.py"
    if not installer.exists():
        print(f"[!] Installer not found at {installer}")
        return 1

    print()
    # Flush first: when stdout is a pipe or a log file it is block-buffered, so
    # without this our output would appear after the child's.
    sys.stdout.flush()
    return subprocess.call([sys.executable, str(installer)] + args)


if __name__ == "__main__":
    sys.exit(main())
