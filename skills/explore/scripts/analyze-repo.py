#!/usr/bin/env python3
"""
analyze-repo.py
-------------------------------------------------------------------------------
Fast repository forensics for cognitive exploration.
Extracts tech stack, entrypoints, Git churn hotspots, and candidate domain files
without consuming LLM tokens. Zero external dependencies.
"""

from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

IGNORED_EXTENSIONS = {
    ".lock", ".sum", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".map", ".min.js", ".min.css", ".tar", ".gz", ".zip", ".bin",
    ".db", ".sqlite", ".pbtxt", ".log"
}

IGNORED_PATHS = {
    ".git", ".worktrees", "node_modules", "vendor", "dist", "build", ".cache",
    ".idea", ".vscode", "tmp", "coverage", ".next", "out"
}


def run_git(repo_dir: Path, *args: str) -> str:
    """Run git command and return stripped stdout or empty string on failure."""
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_dir)] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return ""


def detect_stack(repo_dir: Path) -> dict:
    """Detect technologies, language manifests, and services."""
    stack = []
    manifests = []

    # Go (root or subfolder)
    for p in repo_dir.glob("**/go.mod"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        go_mod = p.read_text(errors="ignore")
        ver = "Go"
        for line in go_mod.splitlines():
            if line.startswith("go "):
                ver = f"Go {line.split()[1]}"
                break
        if ver not in stack:
            stack.append(ver)

    # Node / JS / TS
    for p in repo_dir.glob("**/package.json"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        try:
            data = json.loads(p.read_text(errors="ignore"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            frameworks = [f for f in ["react", "vue", "svelte", "next", "vite", "express", "fastify", "tailwind", "vitest", "jest"] if any(f in d.lower() for d in deps)]
            label = "Node/TS" if "typescript" in deps else "Node/JS"
            if frameworks:
                label += f" ({', '.join(frameworks[:4])})"
            if label not in stack:
                stack.append(label)
        except Exception:
            pass

    # Python
    for p in list(repo_dir.glob("**/pyproject.toml")) + list(repo_dir.glob("**/requirements.txt")):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        if "Python" not in stack:
            stack.append("Python")

    # Rust
    for p in repo_dir.glob("**/Cargo.toml"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        if "Rust (Cargo)" not in stack:
            stack.append("Rust (Cargo)")

    # Container / Orchestration
    if list(repo_dir.glob("**/docker-compose*.yml")) or list(repo_dir.glob("**/compose*.yaml")):
        stack.append("Docker Compose")
    if list(repo_dir.glob("**/Dockerfile")):
        stack.append("Docker")
    if list(repo_dir.glob("**/Makefile")):
        stack.append("Make")

    return {"technologies": stack, "manifests": manifests}


def find_entrypoints(repo_dir: Path) -> list:
    """Identify application entrypoints (HTTP server, CLI, frontend main)."""
    candidates = [
        "**/main.go", "**/server.go", "**/app.go",
        "**/main.ts", "**/main.tsx", "**/index.ts", "**/index.tsx", "**/App.tsx",
        "**/main.js", "**/index.js", "**/server.ts", "**/server.js",
        "**/main.py", "**/app.py", "**/wsgi.py", "**/asgi.py",
        "**/main.rs", "**/lib.rs"
    ]
    found = []
    for pattern in candidates:
        for p in repo_dir.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if "_test" in p.name or ".spec." in p.name:
                continue
            rel = str(p.relative_to(repo_dir))
            if rel not in found:
                found.append(rel)
    return found[:8]


def git_churn_hotspots(repo_dir: Path, max_commits: int = 150) -> list:
    """Analyze commit frequency per file over recent commits."""
    raw = run_git(repo_dir, "log", f"-n{max_commits}", "--format=", "--name-only")
    if not raw:
        return []

    counter = Counter()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if p.suffix in IGNORED_EXTENSIONS:
            continue
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        # Check if file still exists on disk
        if (repo_dir / p).is_file():
            counter[str(p)] += 1

    return [{"file": path, "changes": count} for path, count in counter.most_common(12)]


def detect_domain_candidates(repo_dir: Path) -> list:
    """Detect core domain entities, schemas, and contract models."""
    patterns = [
        "**/domain/**/*.go", "**/domain/**/*.ts", "**/domain/**/*.py",
        "**/models/**/*.go", "**/models/**/*.ts", "**/models/**/*.py",
        "**/entities/**/*.go", "**/entities/**/*.ts",
        "**/schema*.prisma", "**/schema*.sql", "**/migrations/*.sql"
    ]
    candidates = []
    for pattern in patterns:
        for p in repo_dir.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if p.suffix in IGNORED_EXTENSIONS or "_test" in p.name or ".spec." in p.name:
                continue
            rel = str(p.relative_to(repo_dir))
            if rel not in candidates:
                candidates.append(rel)
    return candidates[:10]


def detect_e2e_or_smoke_tests(repo_dir: Path) -> list:
    """Find primary end-to-end or integration tests that serve as living docs."""
    patterns = [
        "**/e2e*.*", "**/*smoke*.*", "**/integration*.*", "**/test_api*.*"
    ]
    tests = []
    for pattern in patterns:
        for p in repo_dir.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if p.is_file() and p.suffix not in IGNORED_EXTENSIONS:
                rel = str(p.relative_to(repo_dir))
                if rel not in tests:
                    tests.append(rel)
    return tests[:6]


def main():
    target_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not target_dir.is_dir():
        print(json.dumps({"error": f"Directory not found: {target_dir}"}))
        sys.exit(1)

    result = {
        "root": str(target_dir),
        "stack": detect_stack(target_dir),
        "entrypoints": find_entrypoints(target_dir),
        "git_hotspots": git_churn_hotspots(target_dir),
        "domain_candidates": detect_domain_candidates(target_dir),
        "living_tests": detect_e2e_or_smoke_tests(target_dir)
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
