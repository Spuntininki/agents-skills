# Agents Skills

Personal reusable skills adapted from Gemini for Codex. Each skill is a standalone
folder with a `SKILL.md` entrypoint, suitable for installation on another machine.

| Skill | Purpose |
| --- | --- |
| `slice` | Break down complex features or large issues into micro-issues (≤ 200–300 lines diff budget). |
| `refine` | Inspect a GitHub issue, align material technical decisions, and update its implementation specification. |
| `implement` | Implement a GitHub issue, verify the change, and prepare a pull request when publication is authorized. |
| `english-practice` | Briefly correct English mistakes while continuing the requested task. |

## Install

Requires Python 3.10 or newer. GitHub CLI authentication is required to clone this
private repository and to use the issue workflows.

```bash
gh repo clone Spuntininki/agents-skills
cd agents-skills
python3 install.py
```

The installer copies all skills into `$CODEX_HOME/skills`, or `~/.codex/skills`
when `CODEX_HOME` is unset. It never overwrites an existing skill. If any selected
skill already exists, installation stops before copying anything.

Install only selected skills or choose a different destination:

```bash
python3 install.py slice refine implement
python3 install.py --dest /path/to/codex/skills
```

Installed skills are available on the next Codex turn. If the client does not
refresh the skill list, start a new chat or restart the client.

## Use

```text
$slice https://github.com/OWNER/REPO/issues/12
$slice Add user notification preference and email alerts
$refine https://github.com/OWNER/REPO/issues/12
$implement https://github.com/OWNER/REPO/issues/12
$english-practice Please correct my English while we work.
```

Skills can also be selected automatically when the request matches their description.
Repository rules and explicit user instructions take precedence. The `implement`
skill preserves commit/push authorization requirements; installation does not
publish code or grant permissions for future tasks.

## Update

Pull changes in this clone, review the diff, and back up or move the installed
skill directories you want to replace before running the installer again.
Editing an installed copy does not automatically update this repository.

## Add a skill

Add `skills/<name>/SKILL.md` with YAML frontmatter containing `name` and
`description`. Keep supporting scripts, references, and assets inside that folder.
Use English for documentation and instructions. Never include credentials, local
account configuration, or private project data.
