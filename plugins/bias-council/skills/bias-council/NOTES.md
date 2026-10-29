# bias-council: notes

**Testing status: eval-tested; light real-world use.** Treat verdicts as a structured second opinion, not a validated oracle.

## What the evals cover (`evals/`, run with `claude plugin eval`)
- **High stakes, runs a council (4):** a risky change to production switches, a job-offer decision, a post containing a prompt injection, and an explicit request carrying a planted wrong lean. Graders check the `BIAS COUNCIL` report header, at least 4 Agent calls, the visible `Save failed` line (evals can't write files), lockout detection, injection resistance and lean removal.
- **Medium stakes, offers only (3):** a tool choice, a technical claim, a change to a learning plan. Graders check zero Agent calls, the one-line offer, and that the reply still answers the question.
- **None, stays silent (3):** a fact lookup, "just tell me", a mechanical rename. Graders check zero Agent calls and no mention of the council.
- Trigger graders use the report-header regex plus Agent-call counts, because a `tool_used: Skill` grader can't filter by skill name.

## Static check
`python3 scripts/check.py static` checks SKILL.md structure, the task ids shared by SKILL.md and `references/prompts.md`, the pinned behaviour rules, and the agents' tool allowlists. `check.py saved <report.md>` checks a saved report for non-RFC 5737 IPv4 addresses; `check.py blinding <transcript.jsonl>` checks a synthesizer prompt for task or model names.

## Known limits
- Same-family panel: all members are Claude, so agreement is weak evidence.
- A member's role can be inferred from its content even after redaction.
- Settled-decision handling has no automated eval: the eval sandbox can't read the user's CLAUDE.md.
- The technical-claim case is borderline; the offer line appears in most runs, not all.
- Rotation is deterministic (by question length), not a true shuffle.
- `check.py saved` checks IPv4 only; hostnames and secrets rely on the model sanitizing them.
