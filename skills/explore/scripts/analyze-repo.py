#!/usr/bin/env python3
"""
analyze-repo.py
-------------------------------------------------------------------------------
Fast repository forensics for cognitive exploration.
Extracts tech stack, architectural patterns (EDA, workers, clean/hexagonal, MVC),
entrypoints, Git churn hotspots, and candidate domain files without token waste.
Zero external dependencies.
"""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

IGNORED_EXTENSIONS = {
    ".lock", ".sum", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".map", ".min.js", ".min.css", ".tar", ".gz", ".zip", ".bin",
    ".db", ".sqlite", ".pbtxt", ".log", ".csv", ".pdf"
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


def detect_stack_and_architecture(repo_dir: Path, subpath: Path = None) -> dict:
    """Detect technologies, frameworks, and architectural style cues."""
    search_root = (repo_dir / subpath) if subpath else repo_dir
    stack = []
    manifests = []
    arch_cues = set()

    # Go
    for p in search_root.glob("**/go.mod"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        content = p.read_text(errors="ignore").lower()
        ver = "Go"
        for line in content.splitlines():
            if line.startswith("go "):
                ver = f"Go {line.split()[1]}"
                break
        if ver not in stack:
            stack.append(ver)
        if any(broker in content for broker in ["kafka", "segmentio/kafka-go", "confluent"]):
            arch_cues.add("Event-Driven (Kafka)")
        if any(broker in content for broker in ["rabbitmq", "amqp"]):
            arch_cues.add("Event-Driven (RabbitMQ)")
        if "temporal" in content:
            arch_cues.add("Orchestrated Workflows (Temporal)")
        if "asynq" in content or "machinery" in content:
            arch_cues.add("Async Worker / Task Queue")
        if "grpc" in content:
            arch_cues.add("gRPC / RPC")

    # Node / JS / TS
    for p in search_root.glob("**/package.json"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        try:
            data = json.loads(p.read_text(errors="ignore"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            frameworks = [f for f in ["react", "vue", "svelte", "next", "vite", "express", "fastify", "nest", "tailwind", "vitest", "jest"] if any(f in d.lower() for d in deps)]
            label = "Node/TS" if "typescript" in deps else "Node/JS"
            if frameworks:
                label += f" ({', '.join(frameworks[:4])})"
            if label not in stack:
                stack.append(label)
            if any(k in deps for k in ["kafkajs", "amqplib", "rhea", "pulsar"]):
                arch_cues.add("Event-Driven (Broker)")
            if any(k in deps for k in ["bullmq", "bull", "agenda"]):
                arch_cues.add("Async Worker / BullMQ")
            if "temporalio" in deps:
                arch_cues.add("Orchestrated Workflows (Temporal)")
            if "@nestjs" in " ".join(deps.keys()):
                arch_cues.add("NestJS Modular / Dependency Injection")
        except Exception:
            pass

    # Python
    py_files = list(search_root.glob("**/pyproject.toml")) + list(search_root.glob("**/requirements.txt"))
    for p in py_files:
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        if "Python" not in stack:
            stack.append("Python")
        content = p.read_text(errors="ignore").lower()
        if "celery" in content:
            arch_cues.add("Async Worker (Celery)")
        if "fastapi" in content or "flask" in content or "django" in content:
            framework = "FastAPI" if "fastapi" in content else ("Django" if "django" in content else "Flask")
            stack.append(framework)
        if any(b in content for b in ["confluent-kafka", "pika", "aiokafka"]):
            arch_cues.add("Event-Driven (Broker)")

    # Rust
    for p in search_root.glob("**/Cargo.toml"):
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue
        manifests.append(str(p.relative_to(repo_dir)))
        if "Rust (Cargo)" not in stack:
            stack.append("Rust (Cargo)")

    # Structural directory inspection for architectural cues
    all_dirs = {p.name.lower() for p in search_root.glob("**/*") if p.is_dir() and not any(ign in p.parts for ign in IGNORED_PATHS)}
    if any(d in all_dirs for d in ["consumers", "workers", "subscribers", "listeners"]):
        arch_cues.add("Worker / Consumer Pool")
    if any(d in all_dirs for d in ["domain", "entities", "usecases", "ports", "adapters"]):
        arch_cues.add("Hexagonal / Clean Architecture")
    if any(d in all_dirs for d in ["events", "messages", "commands"]):
        arch_cues.add("Event/Message Driven Patterns (CQRS/EDA)")

    # Container / Orchestration
    if list(search_root.glob("**/docker-compose*.yml")) or list(search_root.glob("**/compose*.yaml")):
        stack.append("Docker Compose")
    if list(search_root.glob("**/Dockerfile")):
        stack.append("Docker")
    if list(search_root.glob("**/Makefile")):
        stack.append("Make")

    return {
        "technologies": list(dict.fromkeys(stack)),
        "architectural_style": sorted(arch_cues),
        "manifests": manifests
    }


def find_entrypoints(repo_dir: Path, subpath: Path = None) -> list:
    """Identify application entrypoints (HTTP server, CLI, Workers, Consumers, Tasks)."""
    search_root = (repo_dir / subpath) if subpath else repo_dir

    candidates = [
        # Standard HTTP & CLI
        "**/main.go", "**/server.go", "**/app.go",
        "**/main.ts", "**/main.tsx", "**/index.ts", "**/index.tsx", "**/App.tsx",
        "**/main.js", "**/index.js", "**/server.ts", "**/server.js",
        "**/main.py", "**/app.py", "**/wsgi.py", "**/asgi.py",
        "**/main.rs", "**/lib.rs",

        # Workers, Jobs & Task Queues
        "**/worker*.go", "**/worker*.py", "**/worker*.ts", "**/worker*.js",
        "**/workers/**/*.py", "**/workers/**/*.go", "**/workers/**/*.ts",
        "**/tasks/**/*.py", "**/tasks/**/*.go", "**/tasks/**/*.ts",
        "**/jobs/**/*.py", "**/jobs/**/*.go", "**/jobs/**/*.ts",
        "**/celery*.py",

        # Event Consumers & Subscribers (EDA)
        "**/consumer*.go", "**/consumer*.py", "**/consumer*.ts",
        "**/consumers/**/*.go", "**/consumers/**/*.py", "**/consumers/**/*.ts",
        "**/subscriber*.go", "**/subscriber*.py", "**/subscriber*.ts",
        "**/subscribers/**/*.go", "**/subscribers/**/*.py", "**/subscribers/**/*.ts",
        "**/listener*.go", "**/listener*.py", "**/listener*.ts",
        "**/listeners/**/*.go", "**/listeners/**/*.py", "**/listeners/**/*.ts"
    ]

    found = []
    for pattern in candidates:
        for p in search_root.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if "_test" in p.name or ".spec." in p.name or p.is_dir():
                continue
            rel = str(p.relative_to(repo_dir))
            if rel not in found:
                found.append(rel)
    return found[:12]


def git_churn_hotspots(repo_dir: Path, subpath: Path = None, max_commits: int = 200, since: str = None) -> dict:
    """Analyze commit frequency per file and aggregate by component/directory."""
    git_args = ["log", f"-n{max_commits}", "--format=", "--name-only"]
    if since:
        git_args.append(f"--since={since}")

    if subpath:
        git_args.extend(["--", str(subpath)])

    raw = run_git(repo_dir, *git_args)
    if not raw:
        return {"file_hotspots": [], "component_hotspots": []}

    file_counter = Counter()
    comp_counter = Counter()

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if p.suffix in IGNORED_EXTENSIONS:
            continue
        if any(ign in p.parts for ign in IGNORED_PATHS):
            continue

        full_path = repo_dir / p
        if full_path.is_file():
            rel_str = str(p)
            file_counter[rel_str] += 1
            # Group by top 2 directory levels (e.g. backend/internal/practice)
            parts = p.parts
            if len(parts) >= 2:
                comp = "/".join(parts[:2]) if len(parts) == 2 else "/".join(parts[:3])
                comp_counter[comp] += 1

    file_hotspots = [{"file": path, "changes": count} for path, count in file_counter.most_common(12)]
    component_hotspots = [{"component": comp, "changes": count} for comp, count in comp_counter.most_common(6)]

    return {
        "file_hotspots": file_hotspots,
        "component_hotspots": component_hotspots
    }


def detect_domain_candidates(repo_dir: Path, subpath: Path = None) -> list:
    """Detect core domain entities, events, schemas, and contract models."""
    search_root = (repo_dir / subpath) if subpath else repo_dir

    patterns = [
        # Domain Models & Entities
        "**/domain/**/*.go", "**/domain/**/*.ts", "**/domain/**/*.py",
        "**/models/**/*.go", "**/models/**/*.ts", "**/models/**/*.py",
        "**/entities/**/*.go", "**/entities/**/*.ts", "**/entities/**/*.py",

        # Event-Driven Schemas, Contracts & Messages
        "**/events/**/*.go", "**/events/**/*.ts", "**/events/**/*.py",
        "**/messages/**/*.go", "**/messages/**/*.ts", "**/messages/**/*.py",
        "**/commands/**/*.go", "**/commands/**/*.ts", "**/commands/**/*.py",
        "**/queries/**/*.go", "**/queries/**/*.ts",
        "**/*.proto", "**/*.avro",

        # Database Schemas & Migrations
        "**/schema*.prisma", "**/schema*.sql", "**/migrations/*.sql"
    ]

    candidates = []
    for pattern in patterns:
        for p in search_root.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if p.suffix in IGNORED_EXTENSIONS or "_test" in p.name or ".spec." in p.name or p.is_dir():
                continue
            rel = str(p.relative_to(repo_dir))
            if rel not in candidates:
                candidates.append(rel)
    return candidates[:12]


def detect_e2e_or_smoke_tests(repo_dir: Path, subpath: Path = None) -> list:
    """Find primary end-to-end or integration tests that serve as living docs."""
    search_root = (repo_dir / subpath) if subpath else repo_dir

    patterns = [
        "**/e2e*.*", "**/*smoke*.*", "**/integration*.*", "**/test_api*.*"
    ]
    tests = []
    for pattern in patterns:
        for p in search_root.glob(pattern):
            if any(ign in p.parts for ign in IGNORED_PATHS):
                continue
            if p.is_file() and p.suffix not in IGNORED_EXTENSIONS:
                rel = str(p.relative_to(repo_dir))
                if rel not in tests:
                    tests.append(rel)
    return tests[:6]


def main():
    parser = argparse.ArgumentParser(description="Fast repository forensics for cognitive exploration.")
    parser.add_argument("path", nargs="?", default=".", help="Target repository directory (default: current directory)")
    parser.add_argument("--subpath", help="Focus analysis on a specific subfolder or module (e.g. backend, services/worker)")
    parser.add_argument("--max-commits", type=int, default=200, help="Number of recent commits to analyze for churn (default: 200)")
    parser.add_argument("--since", help="Time window for commit churn (e.g. '3 months ago', '2026-01-01')")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (json or text)")

    args = parser.parse_args()

    repo_dir = Path(args.path).resolve()
    if not repo_dir.is_dir():
        print(json.dumps({"error": f"Directory not found: {repo_dir}"}))
        sys.exit(1)

    subpath_obj = Path(args.subpath) if args.subpath else None

    result = {
        "root": str(repo_dir),
        "subpath": str(subpath_obj) if subpath_obj else None,
        "stack_and_architecture": detect_stack_and_architecture(repo_dir, subpath_obj),
        "entrypoints": find_entrypoints(repo_dir, subpath_obj),
        "git_hotspots": git_churn_hotspots(repo_dir, subpath_obj, max_commits=args.max_commits, since=args.since),
        "domain_and_event_candidates": detect_domain_candidates(repo_dir, subpath_obj),
        "living_tests": detect_e2e_or_smoke_tests(repo_dir, subpath_obj)
    }

    if args.format == "text":
        print(f"\n🧭 Repository Forensics: {repo_dir.name}")
        if subpath_obj:
            print(f"   Subpath: {subpath_obj}")
        print("-" * 60)
        print("📦 Stack & Architecture:")
        print(f"   Technologies: {', '.join(result['stack_and_architecture']['technologies']) or 'None detected'}")
        print(f"   Patterns:     {', '.join(result['stack_and_architecture']['architectural_style']) or 'General'}")
        print("\n🚪 Entrypoints (HTTP, Workers, Consumers, CLI):")
        for ep in result["entrypoints"]:
            print(f"   • {ep}")
        print("\n🔥 Component Churn Hotspots:")
        for comp in result["git_hotspots"]["component_hotspots"]:
            print(f"   • {comp['component']:30} ({comp['changes']} commits)")
        print("\n📄 Top File Hotspots:")
        for fh in result["git_hotspots"]["file_hotspots"][:6]:
            print(f"   • {fh['file']:40} ({fh['changes']} commits)")
        print("\n🧩 Domain Models & Event Schemas:")
        for dc in result["domain_and_event_candidates"][:6]:
            print(f"   • {dc}")
        print("\n🧪 Living Tests:")
        for lt in result["living_tests"]:
            print(f"   • {lt}")
        print("-" * 60 + "\n")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
