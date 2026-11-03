#!/usr/bin/env python3
"""
install.py
-------------------------------------------------------------------------------
Universal installer for agent skills.
Compatible with Antigravity, Gemini, Claude Code, Codex, and generic harnesses.
Supports copy and symlink modes, multi-target presets, and safe upgrades.
"""

import argparse
import os
from pathlib import Path
import shutil
import sys

TARGET_PRESETS = {
    "gemini": Path.home() / ".gemini" / "config" / "skills",
    "antigravity": Path.home() / ".gemini" / "config" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")) / "skills",
    "workspace": Path.cwd() / ".agents" / "skills",
}


def detect_default_destination() -> Path:
    """Detect available agent runtime environments or fall back to universal location."""
    env_home = os.environ.get("AGENT_SKILLS_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()

    if (Path.home() / ".gemini").is_dir():
        return TARGET_PRESETS["gemini"]
    if (Path.home() / ".claude").is_dir():
        return TARGET_PRESETS["claude"]
    if (Path.home() / ".codex").is_dir() or os.environ.get("CODEX_HOME"):
        return TARGET_PRESETS["codex"]

    return TARGET_PRESETS["gemini"]


def get_skill_description(skill_path: Path) -> str:
    """Extract description from SKILL.md frontmatter if available."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.is_file():
        return ""
    try:
        content = skill_file.read_text(errors="ignore")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                lines = parts[1].splitlines()
                capturing = False
                desc_lines = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("description:"):
                        val = line.split("description:", 1)[1].strip()
                        if val in (">-", "|", ">", ""):
                            capturing = True
                        else:
                            return val.strip("'\"")
                    elif capturing:
                        if line.startswith("  ") or line.startswith("\t"):
                            desc_lines.append(stripped)
                        elif stripped:
                            break
                if desc_lines:
                    return " ".join(desc_lines).strip("'\"")
    except Exception:
        pass
    return ""


def main() -> int:
    source = Path(__file__).resolve().parent / "skills"
    if not source.is_dir():
        print(f"Error: skills directory not found at {source}", file=sys.stderr)
        return 1

    available = sorted(p.name for p in source.iterdir() if (p / "SKILL.md").is_file())

    parser = argparse.ArgumentParser(
        description="Install reusable agent skills into any AI coding assistant harness."
    )
    parser.add_argument("skills", nargs="*", help="Skill names to install (defaults to all)")
    parser.add_argument(
        "--target",
        choices=list(TARGET_PRESETS.keys()),
        help=f"Preset harness destination ({', '.join(TARGET_PRESETS.keys())})",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        help="Explicit destination directory for skills",
    )
    parser.add_argument(
        "-f", "--force", "--overwrite",
        action="store_true",
        dest="overwrite",
        help="Overwrite existing skill installations",
    )
    parser.add_argument(
        "-s", "--symlink",
        action="store_true",
        help="Create symbolic links instead of copying (ideal for local skill development)",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available skills in this repository and exit",
    )

    args = parser.parse_args()

    if args.list:
        print("Available skills in repository:\n")
        for name in available:
            desc = get_skill_description(source / name)
            print(f"  • {name:18} {desc}")
        print()
        return 0

    # Resolve destination path
    if args.dest:
        destination = args.dest.expanduser().resolve()
    elif args.target:
        destination = TARGET_PRESETS[args.target].expanduser().resolve()
    else:
        destination = detect_default_destination()

    names = list(dict.fromkeys(args.skills or available))
    unknown = [name for name in names if name not in available]
    if unknown:
        parser.error(f"Unknown skills: {', '.join(unknown)}. Available: {', '.join(available)}")

    destination.mkdir(parents=True, exist_ok=True)
    print(f"===> Target destination: {destination}\n")

    conflicts = [name for name in names if os.path.lexists(destination / name)]
    if conflicts and not args.overwrite:
        print(
            f"Already installed: {', '.join(conflicts)}.\n"
            f"Use --overwrite (-f) to replace them or specify a different --dest.",
            file=sys.stderr,
        )
        return 1

    for name in names:
        src_path = source / name
        dest_path = destination / name

        if os.path.lexists(dest_path):
            if os.path.islink(dest_path) or dest_path.is_file():
                dest_path.unlink()
            else:
                shutil.rmtree(dest_path)

        if args.symlink:
            dest_path.symlink_to(src_path, target_is_directory=True)
            print(f"🔗 Linked   {name:16} -> {dest_path}")
        else:
            shutil.copytree(src_path, dest_path)
            print(f"✅ Installed {name:16} -> {dest_path}")

    print(f"\nDone! {len(names)} skill(s) ready in {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
