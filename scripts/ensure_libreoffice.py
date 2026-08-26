#!/usr/bin/env python3
"""
Ensure LibreOffice (the offline PPTX -> PDF renderer) is available.
===================================================================
Called by install.py so a fresh clone gets a one-command, credential-free PDF
path. LibreOffice is a *system* package (not pip-installable), so this module
detects it and, if missing, installs it with the platform's package manager.

Design goals:
  * Never hard-fail the overall install. PDF is a desired-but-optional output;
    if LibreOffice can't be provisioned, the skill still produces PPTX + CSV and
    prints exactly how to finish the PDF path.
  * Cross-platform: apt / dnf / snap (Linux), Homebrew (macOS), winget / choco
    (Windows).
  * Honor --yes for unattended installs; otherwise ask once.

Standalone use:
    python3 scripts/ensure_libreoffice.py            # interactive
    python3 scripts/ensure_libreoffice.py --yes      # unattended
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from local_pdf import find_libreoffice, install_hint  # noqa: E402

# The deck's two primary design fonts (Poppins, DM Sans) are NOT installed by any
# OS package manager, and LibreOffice headless does not reliably use the copies
# embedded in the .pptx. So we bundle the free OFL originals in assets/fonts and
# install them into the user font directory. Without this, Poppins/DM Sans text
# silently falls back to DejaVu Sans and the PDF looks wrong.
BUNDLED_FONTS_DIR = SCRIPT_DIR.parent / "assets" / "fonts"


# Per-package-manager: the base LibreOffice package plus the two free fonts that
# are metric-compatible substitutes for the deck's only non-embedded fonts
# (Arial -> Liberation Sans, Calibri -> Carlito), and JetBrains Mono.
LINUX_MANAGERS = {
    "apt-get": {
        "update": ["apt-get", "update"],
        "install": ["apt-get", "install", "-y"],
        "packages": ["libreoffice-impress", "fonts-liberation",
                     "fonts-crosextra-carlito", "fonts-jetbrains-mono"],
    },
    "dnf": {
        "update": None,
        "install": ["dnf", "install", "-y"],
        "packages": ["libreoffice-impress", "liberation-fonts",
                     "google-carlito-fonts", "jetbrains-mono-fonts"],
    },
    "snap": {
        "update": None,
        "install": ["snap", "install"],
        "packages": ["libreoffice"],  # snap bundles its own fonts
    },
}


def _run(cmd, assume_yes):
    """Run a command, streaming output. Returns True on success."""
    print(f"    $ {' '.join(cmd)}")
    try:
        return subprocess.call(cmd) == 0
    except Exception as exc:  # pragma: no cover - defensive
        print(f"    [!] Command failed to launch: {exc}")
        return False


def _sudo_prefix(cmd):
    """Prefix sudo on POSIX when we are not already root and sudo exists."""
    if os.name == "posix" and os.geteuid() != 0 and shutil.which("sudo"):
        return ["sudo"] + cmd
    return cmd


def _confirm(assume_yes, prompt):
    if assume_yes:
        return True
    try:
        return input(prompt).strip().lower() in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _install_linux(assume_yes):
    for mgr, spec in LINUX_MANAGERS.items():
        if not shutil.which(mgr):
            continue
        print(f"[*] Using '{mgr}' to install LibreOffice + substitute fonts...")
        if spec["update"]:
            _run(_sudo_prefix(spec["update"]), assume_yes)
        cmd = _sudo_prefix(spec["install"] + spec["packages"])
        if _run(cmd, assume_yes):
            return True
        # apt sometimes needs the fonts split out if one package name drifts;
        # retry with LibreOffice alone so the core capability still lands.
        print("    [*] Retrying with LibreOffice only (fonts can be added later)...")
        core = spec["install"] + spec["packages"][:1]
        if _run(_sudo_prefix(core), assume_yes):
            return True
        return False
    print("[!] No supported Linux package manager found (apt-get / dnf / snap).")
    return False


def _install_macos(assume_yes):
    if not shutil.which("brew"):
        print("[!] Homebrew not found. Install it from https://brew.sh then re-run,")
        print("    or install LibreOffice manually from https://www.libreoffice.org/download/")
        return False
    print("[*] Using Homebrew to install LibreOffice...")
    return _run(["brew", "install", "--cask", "libreoffice"], assume_yes)


def _install_windows(assume_yes):
    if shutil.which("winget"):
        print("[*] Using winget to install LibreOffice...")
        cmd = ["winget", "install", "-e", "--id", "TheDocumentFoundation.LibreOffice",
               "--accept-package-agreements", "--accept-source-agreements"]
        if _run(cmd, assume_yes):
            return True
    if shutil.which("choco"):
        print("[*] Using Chocolatey to install LibreOffice...")
        cmd = ["choco", "install", "libreoffice-fresh", "-y"]
        if _run(cmd, assume_yes):
            return True
    print("[!] Neither winget nor Chocolatey found.")
    return False


def _user_font_dir():
    """Per-user font directory that needs no admin rights, by platform."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Fonts"
    if sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
        return Path(local) / "Microsoft" / "Windows" / "Fonts"
    return home / ".local" / "share" / "fonts"


def install_bundled_fonts():
    """
    Install the bundled design fonts (Poppins, DM Sans) so LibreOffice renders the
    deck faithfully instead of substituting DejaVu Sans. Idempotent. Never raises.
    Returns the number of font files installed (0 if none/failed).
    """
    if not BUNDLED_FONTS_DIR.exists():
        return 0
    ttfs = sorted(BUNDLED_FONTS_DIR.glob("*.ttf")) + sorted(BUNDLED_FONTS_DIR.glob("*.otf"))
    if not ttfs:
        return 0

    dest = _user_font_dir() / "wiz-deck"
    try:
        dest.mkdir(parents=True, exist_ok=True)
        installed = 0
        for f in ttfs:
            try:
                shutil.copy2(f, dest / f.name)
                installed += 1
            except Exception:
                pass
        # Refresh the font cache so LibreOffice sees them immediately (Linux/macOS).
        if os.name == "posix" and shutil.which("fc-cache"):
            subprocess.run(["fc-cache", "-f", str(_user_font_dir())],
                           capture_output=True)
        print(f"[OK] Installed {installed} bundled design font(s) (Poppins, DM Sans) into {dest}")
        return installed
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[!] Could not install bundled fonts ({exc}). PDF may fall back to DejaVu Sans.")
        return 0


def ensure_libreoffice(assume_yes=False):
    """
    Guarantee a LibreOffice binary is available for offline PDF rendering.
    Returns True if present (already or after install), False otherwise.
    Never raises.
    """
    existing = find_libreoffice()
    if existing:
        print(f"[OK] LibreOffice already present: {existing}")
        install_bundled_fonts()  # ensure design fonts even if LibreOffice pre-existed
        return True

    print("[*] LibreOffice is required for the offline (Google-free) PDF export.")
    print("    It is free, needs no account, and runs fully offline.")
    if not _confirm(assume_yes, "    Install it now? [Y/n]: "):
        print("[*] Skipping LibreOffice install. PPTX + CSV will still be generated.")
        print("    To enable PDF later, install LibreOffice:\n")
        print(f"    {install_hint()}\n")
        return False

    try:
        if sys.platform == "darwin":
            ok = _install_macos(assume_yes)
        elif sys.platform.startswith("win"):
            ok = _install_windows(assume_yes)
        else:
            ok = _install_linux(assume_yes)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[!] LibreOffice install raised: {exc}")
        ok = False

    if ok and find_libreoffice():
        print(f"[OK] LibreOffice installed: {find_libreoffice()}")
        install_bundled_fonts()  # design fonts so the PDF renders faithfully
        return True

    print("[!] Could not install LibreOffice automatically.")
    print("    The skill will still produce PPTX + CSV. To enable the PDF path, run:\n")
    print(f"    {install_hint()}\n")
    return False


if __name__ == "__main__":
    assume_yes = "--yes" in sys.argv or "-y" in sys.argv
    sys.exit(0 if ensure_libreoffice(assume_yes=assume_yes) else 1)
