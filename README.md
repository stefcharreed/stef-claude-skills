# stef-claude-skills

Claude Code skills for reviewing high-stakes decisions and vetting Claude Code repos, packaged as a plugin marketplace.

## Install

```
/plugin marketplace add stefcharreed/stef-claude-skills
/plugin install bias-council@stef-claude-skills
/plugin install repo-scan@stef-claude-skills
```

Install only the plugins you want.

| Plugin | What it does | Tested how |
|---|---|---|
| [bias-council](plugins/bias-council) | Runs a blind panel of read-only subagents against a decision, claim, plan or draft, then synthesizes a verdict | `check.py static` in CI + 10 eval prompts; eval-tested, light real-world use |
| [repo-scan](plugins/repo-scan) | Finds and scores Claude Code repos (plugins, skills, MCP servers) against a 10-factor rubric with security gates | Offline `scan.py selftest` in CI; live scans need an authenticated `gh` |

## Your profile (optional)

Skills that save notes or tailor output read `~/.config/claude-skills/profile.md`: flat `key: value` lines, never committed. See [profile.example.md](profile.example.md). Without a profile, every skill still works: it asks you, or uses `./` defaults.

## Security

- A pre-commit gate (`scripts/check_markers.py`) blocks private strings, non-RFC 5737 IPs and real MACs. Enable it with `git config core.hooksPath scripts`.
- repo-scan reads untrusted web content. See [THREAT-MODEL.md](THREAT-MODEL.md).

MIT licensed.
