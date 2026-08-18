#!/usr/bin/env python3
"""
Wiz Health Assessment & Skills Installer
========================================
Installs the skills into your AI agent environment (Claude Code, Jetski,
Cursor, or the current workspace) and, when no credentials exist yet, launches
the setup wizard.

Normally invoked through the top-level installer:

    Windows          python install.py
    macOS / Linux    python3 install.py

It can also be run directly:

    python scripts/install_skills.py --target claude --yes

Options:
  --target NAME        claude, jetski, cursor, workspace, or all.
  --yes                Accept defaults; never prompt (for unattended installs).
  --skip-credentials   Do not launch the credentials wizard.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
SKILLS_DIR = REPO_DIR / "skills"

sys.path.insert(0, str(SCRIPT_DIR))

from console_compat import enable_unicode_output, prompt, python_command  # noqa: E402


def jetski_skills_dir(home):
    """Jetski keeps skills in one of two places depending on how it was set up."""
    config_dir = home / ".gemini" / "config" / "skills"
    if config_dir.parent.exists():
        return config_dir
    return home / ".gemini" / "jetski" / "customizations" / "skills"


def agent_environments():
    """Every supported target, in menu order, with a detection flag.

    Targets are always listed even when undetected: a customer may have the
    agent installed but not yet run it, so its config directory would not exist
    yet. Detected targets sort first so the default choice is the useful one.
    """
    home = Path.home()

    environments = [
        {
            "key": "claude",
            "name": "Claude Code",
            "path": home / ".claude" / "skills",
            "detected": (home / ".claude").exists() or (home / ".anthropic").exists(),
        },
        {
            "key": "jetski",
            "name": "Jetski (Google)",
            "path": jetski_skills_dir(home),
            "detected": (home / ".gemini").exists(),
        },
        {
            "key": "cursor",
            "name": "Cursor",
            "path": home / ".cursor" / "rules",
            "detected": (home / ".cursor").exists(),
        },
    ]
    environments.sort(key=lambda env: not env["detected"])

    # The workspace target always works and needs no agent installed, so it
    # stays last as the universal fallback.
    environments.append({
        "key": "workspace",
        "name": "Current repository / workspace (.agent/skills)",
        "path": REPO_DIR / ".agent" / "skills",
        "detected": True,
    })
    return environments


def available_skills():
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        (d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()),
        key=lambda d: d.name,
    )


def choose_environments(environments, args):
    """Resolve the install targets from --target, or by asking."""
    if args.target:
        wanted = args.target.strip().lower()
        if wanted == "all":
            return environments
        for env in environments:
            if env["key"] == wanted:
                return [env]
        valid = ", ".join(env["key"] for env in environments)
        print(f"[!] Unknown target '{args.target}'. Choose one of: {valid}, all")
        return []

    for idx, env in enumerate(environments, 1):
        mark = "detected" if env["detected"] else "not detected"
        print(f"  [{idx}] {env['name']} ({mark})")
        print(f"      -> {env['path']}")
    print(f"  [{len(environments) + 1}] Install to all of the above")

    if args.yes or not sys.stdin.isatty():
        print(f"\nSelecting [1] {environments[0]['name']} (non-interactive).")
        return [environments[0]]

    choice = prompt(f"\nSelect target environment [1-{len(environments) + 1}, default: 1]: ", "1")
    if not choice:
        return [environments[0]]
    if choice == str(len(environments) + 1):
        return environments
    try:
        value = int(choice)
    except ValueError:
        print(f"[*] '{choice}' is not a number; using [1] {environments[0]['name']}.")
        return [environments[0]]
    if 1 <= value <= len(environments):
        return [environments[value - 1]]
    print(f"[*] {value} is out of range; using [1] {environments[0]['name']}.")
    return [environments[0]]


def clear_destination(dest, assume_yes):
    """Remove an existing install so it can be replaced. False means skip it."""
    if not (dest.exists() or dest.is_symlink()):
        return True

    if dest.is_symlink() or dest.is_file():
        dest.unlink()
        return True

    # A real directory here is either a previous copy-install of ours or
    # something the user put there. Confirm before deleting it.
    if not assume_yes and sys.stdin.isatty():
        answer = prompt(f"    [?] Replace existing directory {dest}? [Y/n]: ", "y")
        if answer.lower().startswith("n"):
            print("    [-] Skipped.")
            return False
    shutil.rmtree(dest)
    return True


def install_to(env, skills, assume_yes):
    """Install every skill into one environment. Returns True if all landed."""
    target_dir = env["path"]
    print(f"\n[*] Installing skills into {env['name']}")
    print(f"    {target_dir}")

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"    [!] Cannot create {target_dir}: {exc}")
        return False

    all_ok = True
    copied_any = False

    for skill in skills:
        dest = target_dir / skill.name
        try:
            if not clear_destination(dest, assume_yes):
                continue
        except OSError as exc:
            print(f"    [!] Could not replace {dest}: {exc}")
            all_ok = False
            continue

        # A symlink keeps the install in sync with the repo, so prefer it.
        # Windows only permits symlinks under Developer Mode or an elevated
        # shell, so fall back to a copy rather than failing the install.
        try:
            dest.symlink_to(skill, target_is_directory=True)
            print(f"    [OK] Linked  {skill.name}")
            continue
        except (OSError, NotImplementedError):
            pass

        try:
            shutil.copytree(skill, dest)
            print(f"    [OK] Copied  {skill.name}")
            copied_any = True
        except OSError as exc:
            print(f"    [!] Failed to install {skill.name}: {exc}")
            all_ok = False

    if copied_any:
        print("    [i] Installed as copies (symlinks need Developer Mode on Windows).")
        print("        Re-run this installer after you update the repo.")
    return all_ok


def handle_credentials(args):
    print("\n[2/3] Checking credentials (.env)...")
    env_file = REPO_DIR / ".env"

    if env_file.exists():
        print(f"    [OK] Found existing .env at {env_file}")
        return

    wizard = SCRIPT_DIR / "setup_credentials.py"
    if args.skip_credentials:
        print("    [-] No .env found; skipping the wizard (--skip-credentials).")
        print(f"        Run it later: {python_command()} scripts/setup_credentials.py")
        return

    # The wizard reads a secret with getpass and needs a real terminal.
    if not sys.stdin.isatty():
        print("    [-] No .env found, and no interactive terminal to run the wizard in.")
        print(f"        Run it in your terminal: {python_command()} scripts/setup_credentials.py")
        return

    if not wizard.exists():
        print(f"    [!] Credentials wizard not found at {wizard}")
        return

    print("    No .env file found. Launching the setup wizard...")
    sys.stdout.flush()
    subprocess.call([sys.executable, str(wizard)])


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Install the Wiz Health Assessment skills into an AI agent environment.",
    )
    parser.add_argument("--target", help="claude, jetski, cursor, workspace, or all")
    parser.add_argument("--yes", action="store_true", help="accept defaults; never prompt")
    parser.add_argument(
        "--skip-credentials", action="store_true", help="do not launch the credentials wizard"
    )
    return parser.parse_args(argv)


def main(argv=None):
    enable_unicode_output()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    print("=======================================================")
    print("     WIZ HEALTH ASSESSMENT SKILLS INSTALLER            ")
    print("=======================================================")

    skills = available_skills()
    if not skills:
        print(f"\n[!] No skills found in {SKILLS_DIR}")
        print("    Run this from a full clone of the repository.")
        return 1

    print(f"\n[1/3] Detecting AI agent environments... ({len(skills)} skills to install)")
    environments = agent_environments()
    selected = choose_environments(environments, args)
    if not selected:
        return 1

    results = [install_to(env, skills, args.yes) for env in selected]

    handle_credentials(args)

    py = python_command()
    print("\n[3/3] Installation complete.")
    if not all(results):
        print("    [!] Some skills did not install; see the messages above.")
    print("\nRestart your AI assistant so it picks up the new skills, then ask:")
    print("  'Run a tenant health assessment for <Customer>'")
    print("  'Generate a PowerPoint health assessment deck for <Customer>'")
    print("  'Query open critical issues in my Wiz tenant'")
    print("\nOr run directly from the terminal:")
    print(f"  {py} scripts/generate_deck.py --customer 'Acme Corp'")
    print("=======================================================\n")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
