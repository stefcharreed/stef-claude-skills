# Threat model (2026-10-27)

## Assets
- A contributor's private context: names, employers, locations, note paths, emails.
- Git history: once pushed it is permanent, so private strings must never be committed.

## Who would attack, and how
- The public reading the repo: private context leaking into skills, docs or history.
- Prompt injection: claude-repo-scan fetches READMEs and repo files from GitHub. That content is untrusted data and must never be followed as instructions.

## Trust boundaries
- Repo (public) vs. `~/.config/claude-skills/profile.md` (private, never committed).
- Model vs. web content: fetched text is untrusted.
- bias-council agents are read-only (Read, Grep, Glob, and WebSearch for members).

## Controls
- `scripts/pre-commit` runs `scripts/check_markers.py` on staged files: private markers (from the gitignored `private-markers.txt`), non-RFC 5737 IPv4, and non-documentation MACs.
- Before the first push: `git log -p --all | python3 scripts/check_markers.py --stdin`.
- CI: `permissions: contents: read`, pinned actions, no `pull_request_target`.

## Accepted risks (2026-10-27)
- CI can't see private markers (the file is gitignored), so it checks IPs/MACs only. The local hook and the pre-push history scan are the marker gate.
- A marker the list doesn't name can still leak. Mitigation: the diff gets a human review before every publish.
