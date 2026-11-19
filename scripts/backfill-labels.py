#!/usr/bin/env python3
"""
backfill-labels.py
-------------------------------------------------------------------------------
Scans issues in a GitHub repository, classifies them according to standard
taxonomy rules, and optionally applies the labels via `gh issue edit`.

Usage:
  python3 scripts/backfill-labels.py --repo Spuntininki/mimirflow --limit 10
  python3 scripts/backfill-labels.py --repo Spuntininki/mimirflow --apply --limit 5
"""

import argparse
import json
import re
import subprocess
import sys


def classify_issue(title: str, body: str, cur_labels: list[str]) -> list[str]:
    title_lower = title.lower()
    body_lower = body.lower()
    proposed = []

    # 1. Type
    if title_lower.startswith("epic"):
        proposed.append("type:epic")
    elif title_lower.startswith("fix") or "bug" in cur_labels:
        proposed.append("type:bug")
    elif title_lower.startswith("feat"):
        proposed.append("type:feat")
    elif title_lower.startswith("refactor"):
        proposed.append("type:refactor")
    elif title_lower.startswith(("test", "docs", "chore", "ci")):
        proposed.append("type:chore")

    # 2. Execution Mode
    if "⚡" in body or "parallel" in body_lower:
        proposed.append("exec:parallel")
    elif "🔒" in body or "serial" in body_lower:
        proposed.append("exec:serial")

    # 3. Area & Preview
    is_front = False
    frontend_keywords = ["(web)", "(ui)", "(frontend)", "apps/web", "components/", ".tsx", ".vue", ".svelte", "pages/"]
    if any(k in title_lower or k in body_lower for k in frontend_keywords):
        proposed.append("area:frontend")
        is_front = True

    backend_keywords = ["(bot)", "(rag)", "(worker)", "(api)", "(digest)", "(schema)", "apps/bot", "apps/api", "services/", "models/"]
    if any(k in title_lower or k in body_lower for k in backend_keywords):
        proposed.append("area:backend")

    if is_front and any(k in body_lower for k in ["component", "page", "modal", "button", "view", "card", "css"]):
        proposed.append("needs:preview")

    return proposed


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill and update GitHub issues with standard labels.")
    parser.add_argument("-R", "--repo", help="Target GitHub repository (owner/repo). Default is current repo.")
    parser.add_argument("--limit", type=int, default=20, help="Max issues to inspect (default: 20).")
    parser.add_argument("--apply", action="store_true", help="Actually apply the changes to GitHub (default is dry-run).")
    parser.add_argument("--state", default="all", choices=["open", "closed", "all"], help="Issue state filter.")
    args = parser.parse_args()

    repo_args = ["-R", args.repo] if args.repo else []

    cmd = ["gh", "issue", "list"] + repo_args + [
        "--limit", str(args.limit),
        "--state", args.state,
        "--json", "number,title,labels,body"
    ]

    try:
        raw = subprocess.check_output(cmd)
        issues = json.loads(raw)
    except Exception as e:
        print(f"Error fetching issues: {e}", file=sys.stderr)
        return 1

    if not issues:
        print("No issues found.")
        return 0

    print(f"Inspecting {len(issues)} issues {'(DRY RUN)' if not args.apply else '(APPLY MODE)'}...\n")
    print(f"{'Issue':<6} | {'Title':<45} | {'Current Labels':<18} | {'Proposed Labels'}")
    print("-" * 110)

    for iss in issues:
        num = iss["number"]
        title = iss["title"]
        short_title = (title[:42] + "...") if len(title) > 45 else title
        body = iss.get("body") or ""
        cur_labels = [l["name"] for l in iss.get("labels", [])]

        proposed = classify_issue(title, body, cur_labels)
        labels_str = ", ".join(proposed) if proposed else "(none)"
        cur_str = ", ".join(cur_labels) if cur_labels else "[]"

        print(f"#{num:<5} | {short_title:<45} | {cur_str:<18} | {labels_str}")

        if args.apply and proposed:
            edit_cmd = ["gh", "issue", "edit", str(num)] + repo_args
            for p in proposed:
                edit_cmd += ["--add-label", p]
            # remove legacy generic "bug" if upgrading to type:bug
            if "bug" in cur_labels:
                edit_cmd += ["--remove-label", "bug"]
            try:
                subprocess.check_call(edit_cmd, stdout=subprocess.DEVNULL)
            except Exception as err:
                print(f"  ❌ Error updating #{num}: {err}", file=sys.stderr)

    if not args.apply:
        print("\n💡 Run with --apply to write these changes to GitHub.")
    else:
        print("\n✅ Issues updated successfully on GitHub.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
