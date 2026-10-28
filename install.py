#!/usr/bin/env python3
"""Install repository skills without overwriting existing installations."""

import argparse
import os
from pathlib import Path
import shutil
import sys


def main() -> int:
    source = Path(__file__).resolve().parent / "skills"
    available = sorted(p.name for p in source.iterdir() if (p / "SKILL.md").is_file())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills", nargs="*", help="Skill names; defaults to all skills")
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    parser.add_argument("--dest", type=Path, default=codex_home / "skills")
    args = parser.parse_args()
    names = list(dict.fromkeys(args.skills or available))
    unknown = [name for name in names if name not in available]
    if unknown:
        parser.error(f"Unknown skills: {', '.join(unknown)}. Available: {', '.join(available)}")
    destination = args.dest.expanduser().resolve()
    conflicts = [name for name in names if os.path.lexists(destination / name)]
    if conflicts:
        print(f"Already installed: {', '.join(conflicts)}. Back up or move these folders first.", file=sys.stderr)
        return 1
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copytree(source / name, destination / name)
        print(f"Installed {name} -> {destination / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
