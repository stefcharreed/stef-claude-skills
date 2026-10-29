# Claude Code repo rubric (canonical)

Source: an unpublished research report, section "Ten factors, two hard gates". Adopted for this skill 2026-10-08 over an earlier 8-factor draft, so scan scores stay comparable to the report leaderboard. Weights are judgment, not empirically validated.

Two **hard gates** apply before any scoring. A repo fails if (1) its hooks, `bin/` or MCP entrypoints contain obfuscated code or fetch-and-execute remote code at runtime, or (2) it reads credentials (`~/.ssh`, `~/.aws`, `.env`) or sends data to undocumented hosts. Unpinned `npx pkg@latest` launches and unexplained maintainer changes are red flags that cost points on Security. None of the scored repos was confirmed to fail a gate, but none was code-audited either.

| Factor (weight) | 5 = | 0–1 = |
|---|---|---|
| Popularity & velocity (5) | ≥100k★ | <5k★. A † marks star velocity far above the cohort, which counts as a flag, not a bonus |
| Verifiable adoption (10) | >100k weekly downloads or >200 contributors | <10 contributors, or unknown |
| Maintenance health (10) | Weekly releases, small backlog | Archived, or no push in 6+ months |
| Provenance (10) | Anthropic official | Anonymous author, or borrows another brand's name |
| License (5) | MIT / Apache-2.0 | None or NOASSERTION (a risk for work use) |
| Execution surface & install friction (15) | No code: docs, or skills invoked on demand | Many hooks plus background services, or skip-permissions recommended |
| Security & supply chain (15) | Official, local-only, disclosure process | Sends code or transcripts off-box by default, or ToS risk |
| Token/context cost (10) | Zero always-on cost | Documented token multiplier (N agents, 6× workflows) |
| Redundancy with native (10) | Nothing native covers it | Native feature covers its core job |
| Fit for you (10) | Directly serves the user's work (profile `fit:` line, or ask) | Irrelevant or conflicts with the user's workflow |

Score = Σ(factor × weight) ÷ 5, out of 100. All metrics are live GitHub API values from 2026-10-08.


## Script gate detectors (scan.py `GATES`)
- `remote-exec`, `obfuscation` → hard gate 1. `credential-path` → hard gate 2. A hit means *read the file*, not auto-reject: regexes match docs/comments too.
- `unpinned-remote` (`npx pkg` / `@latest` / unpinned `uvx`) → Security red flag, not a gate.
- Maintainer/publisher change → check by hand (commit authors, npm maintainers); not automated.
