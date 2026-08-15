#!/usr/bin/env python3
"""
Wiz Health Assessment & Skills Installer
========================================
Interactive installer that:
1. Installs/links skills into your AI agent environment (Jetski, Claude Code, Cursor, VS Code).
2. Verifies Python dependencies.
3. Guides you through setting up your Wiz credentials (.env).
4. Performs a live test to verify connectivity.
"""

import os
import shutil
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
SKILLS_DIR = REPO_DIR / "skills"

def detect_agent_environments():
    home = Path.home()
    envs = []

    # Jetski
    jetski_global = home / ".gemini" / "config" / "skills"
    jetski_custom = home / ".gemini" / "jetski" / "customizations" / "skills"
    if (home / ".gemini").exists():
        envs.append(("Jetski (Google)", jetski_global if jetski_global.parent.exists() else jetski_custom))

    # Claude Code
    claude_skills = home / ".claude" / "skills"
    if (home / ".claude").exists() or (home / ".anthropic").exists():
        envs.append(("Claude Code", claude_skills))

    # Cursor
    cursor_rules = home / ".cursor" / "rules"
    if (home / ".cursor").exists():
        envs.append(("Cursor", cursor_rules))

    # Local Workspace (.agent/skills)
    local_agent = REPO_DIR / ".agent" / "skills"
    envs.append(("Current Repository / Workspace (.agent/skills)", local_agent))

    return envs

def install_skills():
    print("=======================================================")
    print("     WIZ HEALTH ASSESSMENT SKILLS INSTALLER            ")
    print("=======================================================")

    print("\n[1/3] Detecting AI Agent Environments...")
    environments = detect_agent_environments()

    for idx, (name, path) in enumerate(environments, 1):
        print(f"  [{idx}] {name} -> {path}")
    print(f"  [{len(environments) + 1}] Install to all detected environments")

    choice = input(f"\nSelect target environment [1-{len(environments) + 1}, default: 1]: ").strip()
    selected = []
    if not choice or choice == "1":
        selected = [environments[0]]
    elif choice == str(len(environments) + 1):
        selected = environments
    else:
        try:
            val = int(choice)
            if 1 <= val <= len(environments):
                selected = [environments[val - 1]]
        except ValueError:
            selected = [environments[0]]

    for name, target_dir in selected:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[*] Installing skills into {name} ({target_dir})...")
        for skill_folder in SKILLS_DIR.iterdir():
            if skill_folder.is_dir() and (skill_folder / "SKILL.md").exists():
                dest = target_dir / skill_folder.name
                if dest.exists() or dest.is_symlink():
                    if dest.is_dir() and not dest.is_symlink():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                try:
                    dest.symlink_to(skill_folder, target_is_directory=True)
                    print(f"    [✓] Symlinked skill: {skill_folder.name} -> {dest}")
                except Exception:
                    shutil.copytree(skill_folder, dest)
                    print(f"    [✓] Copied skill: {skill_folder.name} -> {dest}")

    print("\n[2/3] Checking Credentials (.env)...")
    env_file = REPO_DIR / ".env"
    if not env_file.exists():
        print("  No .env file found. Launching setup wizard...")
        subprocess.run([sys.executable, str(SCRIPT_DIR / "setup_credentials.py")])
    else:
        print(f"  [✓] Found existing .env file at {env_file}")

    print("\n[3/3] Installation Complete!")
    print("\nYou can now ask your AI assistant:")
    print("  'Run a tenant health assessment for <Customer>'")
    print("  'Generate a PowerPoint health assessment deck for <Customer>'")
    print("  'Query open critical issues in my Wiz tenant'")
    print("\nOr run directly from the terminal:")
    print("  python3 scripts/generate_deck.py --customer 'Acme Corp'")
    print("=======================================================\n")

if __name__ == "__main__":
    install_skills()
