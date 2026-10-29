# stef-claude-skills

Claude Code plugins for pressure-testing decisions and vetting Claude Code repos.

## Install

```
/plugin marketplace add stefcharreed/stef-claude-skills
/plugin install bias-council@stef-claude-skills
/plugin install repo-scan@stef-claude-skills
```

| Plugin | What it does | Tested |
|---|---|---|
| [bias-council](plugins/bias-council) | Blind panel of subagents reviews a decision, plan or draft, then gives a verdict | CI static check + 10 evals |
| [repo-scan](plugins/repo-scan) | Scores Claude Code repos on a 10-factor rubric with security gates | CI offline selftest; live scans need `gh` auth |

## Profile (optional)

`~/.config/claude-skills/profile.md`, `key: value` lines. See [profile.example.md](profile.example.md). Skills work without it.

## Security

- Pre-commit gate blocks private strings, real IPs and MACs: `git config core.hooksPath scripts`
- repo-scan reads untrusted web content: [THREAT-MODEL.md](THREAT-MODEL.md)

MIT
