# Sub-workflow: integration plan + install runbook

Use this when the user asks how to *implement*, *integrate*, *combine* or *install* the scored repos.
Example asks: "how would you set these up together", "make me an install guide", "what should my
stack be now". It turns scores into one coherent setup and a runbook the user applies themselves.

Output is two notes, `Claude-Code-Integration-Plan-<date>.md` and
`Claude-Code-Install-Runbook-<date>.md`. If you saved them from an earlier run, match their
structure (read their headings, not the whole body); otherwise use the structure below:
- **Plan:** audit findings (§1), directions table and the pick (§2), owners by layer and job (§3),
  blind spots (§4), a disposition table for every scored repo (§5).
- **Runbook:** phases 0–6 (§6), each with its commands and a closing check, plus the rollback.

**Never install, uninstall or edit the user's config during this workflow.** The output is a plan
and instructions. The user applies them by hand.

## 1. Audit the live setup first

A plan that isn't mapped to the user's machine is generic advice. Run these and keep only the findings:

```bash
claude --version
claude plugin list
claude plugin marketplace list
claude mcp list                                   # health: Connected / Failed / Needs auth
for p in $(claude plugin list | awk '/❯/{print $2}'); do  # output format may vary; verify against yours
   echo "== $p"; claude plugin details "$p" | grep -E 'Hooks|Always-on'; done
python3 -I -c "import json,pathlib;d=json.loads((pathlib.Path.home()/'.claude/settings.json').read_text());print(sorted(d), sorted((d.get('hooks') or {})))"
ls ~/.claude/commands ~/.claude/skills            # things installed outside the plugin system
```

Print settings **keys only**; settings and `~/.claude.json` can hold tokens. Look for:
- **Duplicate owners:** the same MCP twice, or two planning loops.
- **Failing servers.**
- **Unpinned launches:** `npx -y pkg`, `@latest`, `uvx`.
- **Always-on token hogs:** `claude plugin details`, Always-on column. Check the user's own plugins
  too; a large personal skill pack can cost more always-on context than any third-party plugin.
- **Missing guardrails:** no `permissions.deny`, sandbox off.
- **Things installed outside the plugin system** (copied into `~/.claude/commands`), which `plugin details` can't see.

## 2. Brainstorm 3–4 genuinely different directions

Build a table with one column per direction. Rows: idea, always-on cost, security surface, fit
with how the user works, verdict. Make the directions span a real range: minimal/native, hardened
(usually the pick), builder/CI-heavy, and max-stack. Including the max stack shows why it loses.
Recommend one and say why in two or three sentences. Borrow single pieces from losing directions
when they earn it.

## 3. One owner per job

Lay out the architecture as layers × jobs, and give each job exactly one owner with a status:
have / add / fix / remove / swap / scope / conditional. The layers: core native, guardrails,
method, knowledge, domain skills, CI, observability, discovery. Two standing rules go in the plan:
- Name the job and its current owner before adding anything.
- Trial at `-s local` before user scope.

## 4. Blind-spot pass

List what a test setup won't show the user. Re-check each item against current docs rather than
copying these:
- The sandbox covers Bash only; hooks and MCP servers run unsandboxed.
- `sandbox.filesystem.denyRead` doesn't stop the Read tool, and `permissions.deny` doesn't stop
  shell commands, so the user needs both.
- The sandbox's network allowlist starts empty.
- Auto-update can change reviewed plugin code (rug pull).
- Transcripts can hold sensitive data; prefer local-only tools.
- Public-repo CI triggers are untrusted input.

Also list what the research didn't cover. For example, MCP servers specific to the user's field.

Known macOS sandbox pitfalls; carry them into any sandbox plan:
- **Go binaries (`gh`, terraform) fail TLS inside the macOS sandbox** (`x509: OSStatus -26276`). They need
  `sandbox.excludedCommands`.
- **An excluded call must match an exclusion in every command it contains.** A pipe, redirect, `cd`
  or `$(...)` keeps it sandboxed. A script that calls `gh` internally needs its own exact entry.
- **Launched from `~`, the whole home folder is writable.** Add `denyWrite` for `~/.ssh`, the shell
  rc/profile files, `~/.gitconfig` and `~/Library/LaunchAgents`.
- **Once the sandbox is on, the shell can't write `~/.claude/settings.json`, `CLAUDE.md` or
  `~/.claude/skills`.** Plan those edits for the Edit tool.

## 5. Disposition for every scored repo

Cover every row of `leaderboard.md` plus new scan results, and anything unscored found on the
user's machine. For each: score, disposition (Adopt / Have / Remove / Cond / Ref / Skip), layer,
and a one-line reason. "Each repo" doesn't mean "install each repo". Stacking is the failure mode
the report found.

## 6. Runbook: phased, verified, reversible

Write the runbook as a separate note. Order the phases:
0. backup + baseline
1. clean
2. guardrails
3. fix knowledge
4. observability
5. CI
6. conditional

Every phase ends with a concrete check, and Phase 0 gives the rollback. Rules for the commands:
- **Verify every command before writing it:** `claude <cmd> --help` for CLI syntax, the official
  docs for settings keys (docs pages are large; save and grep them rather than reading in full),
  the repo README for third-party installs. Mark anything unverified as such in the runbook.
- **Pin everything:** npm `pkg@x.y.z` (`npm view pkg version`), GitHub Actions to a commit SHA
  with the tag in a comment (`gh api repos/O/R/commits/TAG --jq .sha`), never `@latest`.
- **CI is least-privilege:** `permissions: contents: read` at workflow level, `pull_request` (not
  comment triggers) on public repos, a narrow `--allowedTools`.
- **Don't execute third-party code to verify it.** Check its `--help` text in the README, not by
  running it.
- **Test any script you hand the user** (statusline etc.) on sample JSON first, and give the test command.
- **Use plain fenced code blocks** (no `>` blockquotes, ASCII only) so blocks paste cleanly into any shell.

## 7. Save and report

Save both notes in `<notes_dir>/` (or `./` without a profile). Frontmatter is optional; if the
user's notes use it, a small set such as `description`, `created` and `tags` is enough. Only if the
profile sets them: append a plain markdown link to each note (`- [title](<path>)`) to the
`notes_index:` file, and one line on what you did to the `notes_log:` file. Tell the user, answer first: the
recommended direction, the single biggest win, what to remove, and the path to the runbook.
