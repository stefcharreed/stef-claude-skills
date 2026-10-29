# My Claude Code workflow

Everything I run in Claude Code day to day. My own skills come first; the official plugins support them.

## How it fits together

1. Before a one-way-door decision or a risky change plan: **bias-council**.
2. Before installing a new plugin, skill or MCP server: **repo-scan**.
3. Building: brainstorm and plan with **superpowers**, write tests first, look up library docs with **context7**.
4. While editing: **pyright-lsp** and **security-guidance** flag problems as they happen.
5. Before merging: **code-review** and **pr-review-toolkit**.

## My skills

| Plugin | What it does for me | What it could do for you |
|---|---|---|
| [bias-council](plugins/bias-council) | Pressure-tests my plans and decisions before I commit. Catches what I'm too close to see. | A blind second opinion on any decision, claim, plan or draft. |
| [repo-scan](plugins/repo-scan) | Vets Claude Code repos before I install them. | Spot remote-exec hooks and credential access before they run on your machine. |

## Official plugins I run alongside

All from `claude-plugins-official`: `/plugin install <name>@claude-plugins-official`.

| Plugin | What it does for me | What it could do for you |
|---|---|---|
| superpowers | Brainstorm, plan, test-first, verify. Keeps me from coding before thinking. | A build discipline that ships working code instead of fast guesses. |
| context7 | Current library and API docs, not stale training data. | Fewer wrong function signatures. |
| pyright-lsp | Type errors on every Python edit. Catches what passing tests miss. | Type checking without leaving the session. |
| security-guidance | Warns on insecure code as it's written and reviews commits. | Catch secrets and injection before they're committed. |
| code-review | Reviews a diff or PR for bugs before merge. | A second reviewer on every change. |
| pr-review-toolkit | Focused reviewers: tests, error handling, comments, types. | Deeper review where a general pass skims. |
| feature-dev | Explores the codebase and designs a feature before building. | Fit new features to existing patterns. |
