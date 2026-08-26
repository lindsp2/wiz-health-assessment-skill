#!/usr/bin/env python3
"""
Wiz Health Assessment & Skills Installer (Cross-Platform: Windows, macOS, Linux)
=================================================================================
Registers the bundled skills into your AI agent environment(s) so the agent can
discover them, then optionally launches the credentials wizard.

Installed for these agents when detected:
  * Claude Code / Claude Desktop  (~/.claude/skills)
  * Cursor                        (~/.cursor/rules)
  * Jetski (Gemini)              (~/.gemini/.../skills)
  * The current repository        (.claude/skills & .agent/skills) - always

Options:
  --target NAME          claude | cursor | jetski | workspace | all (default: all detected)
  --yes                  Accept defaults; never prompt.
  --skip-credentials     Do not launch the credentials wizard.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
SKILLS_DIR = REPO_DIR / "skills"

# Maps a --target keyword to the substring of the environment label it selects.
TARGET_ALIASES = {
    "claude": "Claude",
    "cursor": "Cursor",
    "jetski": "Jetski",
    "workspace": "Current Repository",
}


def safe_remove(path: Path):
    """Safely remove a file, symlink, or directory across Windows, macOS, and Linux."""
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        try:
            path.unlink()
        except OSError:
            try:
                os.rmdir(path)
            except OSError:
                pass
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def available_skills():
    """Return the skill folders (each containing a SKILL.md) bundled in this repo."""
    if not SKILLS_DIR.exists():
        return []
    return [p for p in sorted(SKILLS_DIR.iterdir())
            if p.is_dir() and (p / "SKILL.md").exists()]


def detect_agent_environments():
    """Return a list of (label, skills_target_dir) for agent environments present."""
    home = Path.home()
    envs = []

    # 1. Claude Code & Claude Desktop (global)
    claude_paths = [home / ".claude" / "skills", home / ".config" / "claude" / "skills"]
    if os.name == "nt":  # Windows APPDATA
        appdata = os.environ.get("APPDATA")
        if appdata:
            claude_paths.append(Path(appdata) / "Claude" / "skills")
            claude_paths.append(Path(appdata) / "claude" / "skills")
    for cp in claude_paths:
        if cp.parent.exists() or cp.exists():
            envs.append(("Claude Code / Claude Desktop", cp))
            break
    else:
        envs.append(("Claude Code / Claude Desktop (~/.claude/skills)", home / ".claude" / "skills"))

    # 2. Cursor
    cursor_rules = home / ".cursor" / "rules"
    if cursor_rules.parent.exists() or cursor_rules.exists():
        envs.append(("Cursor (~/.cursor/rules)", cursor_rules))

    # 3. Jetski (Gemini)
    jetski_global = home / ".gemini" / "config" / "skills"
    jetski_custom = home / ".gemini" / "jetski" / "customizations" / "skills"
    if (home / ".gemini").exists():
        envs.append(("Jetski", jetski_global if jetski_global.parent.exists() else jetski_custom))

    return envs


def copy_or_symlink_skill(src_folder: Path, dest_folder: Path):
    """Try symlinking first; if on Windows without developer mode, copy the folder."""
    safe_remove(dest_folder)
    dest_folder.parent.mkdir(parents=True, exist_ok=True)
    try:
        if os.name != "nt":
            dest_folder.symlink_to(src_folder, target_is_directory=True)
            return "Symlinked"
    except Exception:
        pass
    try:
        shutil.copytree(src_folder, dest_folder, dirs_exist_ok=True)
        return "Copied"
    except Exception as e:
        return f"Error: {e}"


def select_targets(environments, target):
    """Filter detected environments by the --target keyword (default: all)."""
    if not target or target == "all":
        return environments
    if target.lower() == "workspace":
        # Repo-local install always happens separately; select no global env.
        return []
    needle = TARGET_ALIASES.get(target.lower())
    if not needle:
        print(f"[!] Unknown --target '{target}'. Using all detected environments.")
        return environments
    picked = [(label, path) for (label, path) in environments if needle in label]
    if not picked:
        print(f"[!] No detected environment matched --target '{target}'.")
    return picked


def install_to(env, skills):
    """Install every skill folder into one environment dir. Returns True on full success."""
    label, target_dir = env
    print(f"\n[*] Installing {len(skills)} skill(s) into {label} ({target_dir})...")
    ok = True
    for skill in skills:
        dest = target_dir / skill.name
        action = copy_or_symlink_skill(skill, dest)
        if action.startswith("Error"):
            ok = False
        print(f"    [{'✓' if not action.startswith('Error') else '!'}] {action} skill: {skill.name} -> {dest}")
    return ok


def parse_args(argv):
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--target", default="all")
    p.add_argument("--yes", "-y", action="store_true")
    p.add_argument("--skip-credentials", action="store_true")
    # Tolerate any extra flags forwarded by install.py without failing.
    args, _unknown = p.parse_known_args(argv)
    return args


def install_skills(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    print("=======================================================")
    print("     WIZ HEALTH ASSESSMENT SKILLS INSTALLER            ")
    print("=======================================================")

    skills = available_skills()
    if not skills:
        print(f"\n[!] No skills found in {SKILLS_DIR}")
        print("    Run this from a full clone of the repository.")
        return 1

    print(f"\n[1/3] Detecting AI agent environments... ({len(skills)} skills to install)")
    environments = select_targets(detect_agent_environments(), args.target)

    results = [install_to(env, skills) for env in environments]

    # Always install into the local workspace so the repo itself is self-describing.
    local_targets = [REPO_DIR / ".claude" / "skills", REPO_DIR / ".agent" / "skills"]
    print("\n[*] Installing into the current repository (.claude/skills & .agent/skills)...")
    for base in local_targets:
        for skill in skills:
            action = copy_or_symlink_skill(skill, base / skill.name)
            results.append(not action.startswith("Error"))
    print(f"    [✓] Local workspace skills installed.")

    print("\n[2/3] Checking Credentials (.env)...")
    env_file = REPO_DIR / ".env"
    if env_file.exists():
        print(f"  [✓] Found existing .env file at {env_file}")
    elif args.skip_credentials:
        print("  [*] Skipping credentials wizard (--skip-credentials).")
        print("      Configure later with: python scripts/setup_credentials.py")
    else:
        print("  No .env file found. Launching setup wizard...")
        try:
            subprocess.run([sys.executable, str(SCRIPT_DIR / "setup_credentials.py")])
        except Exception as e:
            print(f"  [!] Please run 'python scripts/setup_credentials.py' to configure .env ({e})")

    print("\n[3/3] Installation Complete!")
    print("\nYou can now ask your AI assistant:")
    print("  'Run a health assessment for my Wiz tenant and generate my files'")
    print("\nOr run directly from the terminal:")
    print("  python scripts/generate_deck.py --format pdf --customer 'Acme Corp'   # PDF deck")
    print("  python scripts/generate_deck.py --format csv --customer 'Acme Corp'   # CSV for your TAM")
    print("=======================================================\n")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(install_skills())
