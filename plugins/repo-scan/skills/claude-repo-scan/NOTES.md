# claude-repo-scan: deviations log

Things that differed from the plan, logged as found. The live-run findings below were validated against the real GitHub API on 2026-10-08. The selftest only checks logic against made-up example data.

- **2026-10-08 rubric conflict.** The skill was drafted against an earlier 8-factor rubric draft. The final research report published a different 10-factor rubric. The report's rubric was adopted so scan scores line up with its leaderboard. The 4 gate regexes were kept as detectors.
- **2026-10-08 the report said "41 scored"; the actual count is 40.** Counted from the report's tables. The leaderboard header was corrected.
- **2026-10-08 first live run: about 280 false "new" repos.** The seed only captured repos the seed source's links (around 200), but the searches return about 1,000. Fix: the first run after a seed uses `run --absorb`, which records all hits as seen without scoring them.
- **2026-10-08 off-topic platforms.** Keyword searches and the `agent-skills` topic pulled in ToolJet, kubesphere and reactive-resume, which only tag or mention Claude Code. Fix: only results from the `claude-*` topics and the anthropics org are trusted; everything else must mention claude, skills, subagents or MCP in its name or description. ToolJet still passes because its description matches. Accepted.
- **2026-10-08 seed parser junk.** It picked up `api.github.com/repos/...` links and `owner/repo` placeholders. Fixed with a lookbehind and a skip list. Repos that are gone or truncated get removed on the first run.
- **2026-10-08 file cap spent on plugin.json.** In trailofbits/skills, all 15 file slots went to plugin.json files, including test fixtures, so no hooks were seen. Fix: hook and MCP config files are read first, and tests, fixtures and examples are skipped.
- **Known limit: Bash sandbox.** Under the Bash sandbox, `gh` can fail TLS verification and the scan output dir can be write-protected; see SKILL.md §1 for the `sandbox.excludedCommands` setup.
- **Known heuristic limits.** Execution surface adds up hooks across every plugin in a marketplace. Maintenance penalizes repos that don't cut releases. Adoption counts contributors only. The review step corrects all three.
