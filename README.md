# Agents Skills

Universal, production-ready agent skills for autonomous AI coding assistants (Antigravity, Claude Code, Codex, Cursor, and Agent Skill standard-compliant harnesses).

Each skill is a self-contained folder with a `SKILL.md` entrypoint, executable scripts, and zero unnecessary dependencies.

| Skill | Purpose |
| --- | --- |
| `explore` | Onboard onto unfamiliar codebases with a guided cognitive reading path, architectural map, and Git churn hotspots. |
| `slice` | Decompose complex features into independent, vertically sliced micro-issues with parallel/serial execution modes. |
| `orchestrate` | Supervise multi-issue epics using isolated Git worktrees, concurrent subagents for parallel slices, and an Epic Integration Branch. |
| `refine` | Interactively inspect an issue, align material technical decisions, and enrich implementation specifications. |
| `implement` | Implement a GitHub issue end-to-end with clean code, verified dependencies, real tests, and a human-centric PR guide. |
| `diagnose` | Perform Root Cause Analysis (RCA) via isolated subagent, create GitHub bug issue(s), and register in Epics for orchestration. |
| `revise` | Address code review feedback and requested changes on an open PR or branch with surgical fixes and atomic verification. |
| `english-practice` | Maintain language practice with concise, non-disruptive inline corrections while continuing technical tasks. |

---

## Installation

Requires Python 3.10+. The installer supports auto-detection, multi-harness presets, symlinking, and safe upgrades:

```bash
git clone https://github.com/Spuntininki/agents-skills.git
cd agents-skills

# Auto-detects installed harness and installs all skills
python3 install.py
```

### Target Presets

Install to a specific agent harness environment:

```bash
python3 install.py --target antigravity   # ~/.gemini/config/skills
python3 install.py --target claude        # ~/.claude/skills
python3 install.py --target codex         # ~/.codex/skills
python3 install.py --target workspace     # ./.agents/skills (current project)
python3 install.py --dest /custom/path    # Any custom directory
```

### Useful Options

```bash
# Upgrade existing installations without manual deletion
python3 install.py --overwrite

# Symlink skills instead of copying (ideal for active skill development)
python3 install.py --symlink

# Install only selected skills
python3 install.py explore slice orchestrate

# List available skills with descriptions
python3 install.py --list
```

Installed skills become available on the agent's next turn or session restart.

---

## Usage

Trigger skills via slash commands (`/` or `$`, depending on your harness UI):

```text
/explore .
/explore /path/to/unfamiliar-repo
/slice Add user notification preference and email alerts
/slice https://github.com/OWNER/REPO/issues/12
/orchestrate https://github.com/OWNER/REPO/issues/18
/refine https://github.com/OWNER/REPO/issues/12
/implement https://github.com/OWNER/REPO/issues/12
/revise 14 "Rename CustomerDTO and add edge case test for null email"
/diagnose "Worker fails with deadlock when processing batch refund events" --epic 18
/english-practice Please correct my English while we work.
```

Skills are also selected automatically by the agent's router when a user prompt matches their purpose.

---

## Contributing & Adding Skills

Create a new folder under `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: >-
  Concise summary of what the skill does and when to activate it.
---
```

Place helper scripts inside `skills/<name>/scripts/`. Keep skills client-agnostic, portable, and free of hardcoded paths or credentials.
