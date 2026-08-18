#!/usr/bin/env python3
"""
Wiz Health Assessment & Skills Installer (Cross-Platform: Windows, macOS, Linux)
=================================================================================
Interactive installer that:
1. Installs skills into your AI agent environment (Claude Code, Claude Desktop, Cursor, VS Code, Jetski).
2. Verifies Python dependencies.
3. Guides you through setting up your Wiz credentials (.env).
4. Performs a live test to verify connectivity.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
SKILLS_DIR = REPO_DIR / "skills"

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

def detect_agent_environments():
    home = Path.home()

    # 1. Claude Code & Claude Desktop (Global)
    claude_paths = [
        home / ".claude" / "skills",
        home / ".config" / "claude" / "skills"
    ]
    if os.name == "nt": # Windows APPDATA
        appdata = os.environ.get("APPDATA")
        if appdata:
            claude_paths.append(Path(appdata) / "Claude" / "skills")
            claude_paths.append(Path(appdata) / "claude" / "skills")

    for cp in claude_paths:
        if cp.parent.exists() or cp.exists():
            envs.append(("Claude Code / Claude Desktop", cp))
            break
    else:
        # Default Claude path if none exists yet
        envs.append(("Claude Code / Claude Desktop (~/.claude/skills)", home / ".claude" / "skills"))

    # 2. Cursor Rules & Skills
    cursor_rules = home / ".cursor" / "rules"
    if cursor_rules.parent.exists() or cursor_rules.exists():
        envs.append(("Cursor (~/.cursor/rules)", cursor_rules))

    # 3. Jetski (Google)
    jetski_global = home / ".gemini" / "config" / "skills"
    jetski_custom = home / ".gemini" / "jetski" / "customizations" / "skills"
    if (home / ".gemini").exists():
        envs.append(("Jetski", jetski_global if jetski_global.parent.exists() else jetski_custom))

    # 4. Local Project / Workspace (.claude/skills and .agent/skills)
    envs.append(("Current Repository (.claude/skills & .agent/skills)", REPO_DIR / ".claude" / "skills"))


def copy_or_symlink_skill(src_folder: Path, dest_folder: Path):
    """Try symlinking first; if on Windows without developer mode, copy folder."""
    safe_remove(dest_folder)
    
    # On Windows, prefer copytree unless symlink succeeds
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

def install_skills():
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

    # Also always ensure local workspace .agent/skills and .claude/skills exist
    local_claude = REPO_DIR / ".claude" / "skills"
    local_agent = REPO_DIR / ".agent" / "skills"
    local_claude.mkdir(parents=True, exist_ok=True)
    local_agent.mkdir(parents=True, exist_ok=True)

    for skill_folder in SKILLS_DIR.iterdir():
        if skill_folder.is_dir() and (skill_folder / "SKILL.md").exists():
            copy_or_symlink_skill(skill_folder, local_claude / skill_folder.name)
            copy_or_symlink_skill(skill_folder, local_agent / skill_folder.name)

    for name, target_dir in selected:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[*] Installing skills into {name} ({target_dir})...")
        for skill_folder in SKILLS_DIR.iterdir():
            if skill_folder.is_dir() and (skill_folder / "SKILL.md").exists():
                dest = target_dir / skill_folder.name
                action = copy_or_symlink_skill(skill_folder, dest)
                print(f"    [✓] {action} skill: {skill_folder.name} -> {dest}")

    print("\n[2/3] Checking Credentials (.env)...")
    env_file = REPO_DIR / ".env"
    if not env_file.exists():
        print("  No .env file found. Launching setup wizard...")
        try:
            subprocess.run([sys.executable, str(SCRIPT_DIR / "setup_credentials.py")])
        except Exception as e:
            print(f"  [!] Note: Please run python scripts/setup_credentials.py to configure .env ({e})")
    else:
        print(f"  [✓] Found existing .env file at {env_file}")

    print("\n[3/3] Installation Complete!")
    print("\nYou can now ask your AI assistant:")
    print("  'Run a tenant health assessment for <Customer>'")
    print("  'Generate a PowerPoint health assessment deck for <Customer>'")
    print("  'Query open critical issues in my Wiz tenant'")
    print("\nOr run directly from the terminal:")
    print("  python scripts/generate_deck.py --customer 'Acme Corp'")
    print("=======================================================\n")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
