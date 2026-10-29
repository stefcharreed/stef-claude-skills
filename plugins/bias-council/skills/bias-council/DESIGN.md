# bias-council — Design Spec (2026-10-10)

The original design spec, written before the build. Where it differs from the shipped
`SKILL.md`, `SKILL.md` wins. The main changes made during the build:
- Members run as the plugin agent `bias-council:member` (Read, Grep, Glob, WebSearch),
  and the framer and synthesizer as `bias-council:judge` (Read, Grep, Glob, no
  network), not as `Plan`: `Plan` lacks Edit/Write but still has Bash, which can
  write files. Read-only is enforced by the tool allowlist.
- Decisions use `CHOICE: <option>` instead of SUPPORT/CONCERN/BLOCK, since a neutral
  question favors no option; the split is choice counts.
- The Step 3 "shuffle" is a deterministic rotation, k = 1 + len(QUESTION) mod (N − 1),
  so the contrarian is never answer A. Subagents have no Bash and LLM "random" is
  unreliable.
- The host passes MATERIAL verbatim to members and the synthesizer; the framer never
  re-emits it. The FRAMED block also carries CLAIM.
- The Step 0 prior is printed visibly ("committed before the council") so it can be
  audited for hindsight, instead of held hidden.
- If AskUserQuestion is unavailable (non-interactive runs), the synthesis is accepted
  and flagged `checkpoint skipped`.

## 1. Purpose

A Claude Code skill that reduces bias in an answer or decision by running a
small council of independent Claude subagents through a Delphi-style pipeline:
neutral reframe → independent members with assigned *procedures* → shuffled,
anonymized synthesis by a fresh non-member subagent.

**Design constraints:**
- **Claude-only.** No external vendors, no API keys; prompts never leave Anthropic.
  Consequence: the panel is same-family, so agreement is weak evidence and every
  report says so.
- **Use cases:** decisions, claims/answers, plans/designs, the user's own writing.
- **Auto-trigger:** run automatically on high stakes, offer in one line on medium,
  never on trivial. Manual `/bias-council <thing>` always works.
- **Approach A** (Delphi-lite) chosen over peer-review (B) and single-contrarian (C).

**Non-goals:** multi-vendor seats, multi-round debate as default, a UI/pane,
caching. The skill is prompt-driven (SKILL.md + references); the only script is `scripts/check.py`, a static/structure checker, not part of the council run.

## 2. Location and files

```
plugins/bias-council/ (repo layout: agents/ at plugin root, skill under skills/bias-council/)
  SKILL.md               orchestration — what Claude reads when the skill fires
  references/prompts.md  framer, member-task, synthesizer, critique prompts
  evals/                 trigger + behavior cases (see §7)
  NOTES.md               testing status, eval coverage, known limits
  DESIGN.md              this file
```

## 3. Triggering (the SKILL.md `description`)

| Stakes | Examples | Behavior |
|---|---|---|
| High: one-way door or public | job offer / stay-vs-leave, career path change, plan about to touch production systems, something about to be published or sent, money | Run automatically; announce it in one line first |
| Medium: reversible but relied on | tool/architecture choice, technical claim being built on, plan change | Offer in one line ("bias-prone — run a council check?"); run only on yes |
| None | fact lookup, mechanical edit, "just tell me", settled decision | Never fire |

**Settled decisions:** items logged in a DECISIONS file or the user's CLAUDE.md
(e.g. a tool or vendor already chosen) are passed to the council as settled context. A
member may challenge one only by citing evidence not previously considered; the
synthesizer reports such a challenge, it never silently reopens the decision.

## 4. Pipeline

### Step 0 — Prior (host)
Before spawning anything, the host writes one line: its current verdict plus the
reason. Held until the report. The report states whether the council moved the host
off that prior and why.

### Step 1 — Framer (1 subagent, `model: sonnet`, fresh context)
Input: the user's prompt plus the relevant context the host selects (conversation
facts, file contents, settled decisions). Output, fixed shape:
- `TYPE`: decision | claim | plan | writing
- `QUESTION`: neutral rewrite. No stated lean, no certainty markers, no first-person
  belief ("I think/I'm sure"), no false binary; decisions get a "do nothing / other"
  option. Writing reviews: "Evaluate this text for <purpose/audience>", not "is
  this good?"
- `CONTEXT`: facts, constraints, settled decisions. Kept separate from the question.
- `PREMISES`: each labeled `OBSERVED: <what, how confirmed>` or
  `NOT VERIFIED: <what is assumed, what would confirm it>`.
- `REMOVED`: what framing was stripped (for the report).

### Step 2 — Members (parallel, `subagent_type: Plan`, read-only)
Each member sees **only** the framer output, never the conversation. Count: **3 on
medium stakes, 5 on high**. The contrarian is in every run. Task sets by type
(first N in order):

| Type | Members, in order |
|---|---|
| decision | Contrarian · Pre-mortem · Outside view / base rates · Steelman strongest alternative · Key-assumptions check |
| claim | Contrarian · Independent re-derivation (from scratch, cite sources) · Strongest counter-evidence · Outside view · Assumptions check |
| plan | Contrarian / red team · Pre-mortem · Simplest alternative · Assumptions check · Blast radius / rollback |
| writing | Contrarian · Overclaim / accuracy check · Skeptical target reader · Slant / missing perspective · Clarity cut |

Models: contrarian `opus`; others `sonnet`.

Shared member rules (prompt text in `references/prompts.md`):
- You work alone; independence is the point. Push your assigned task as far as it
  honestly goes; do not hedge toward a consensus. Another member covers the other angles.
- If your task has little to say here, say so briefly. Do not invent concerns.
- Verify before asserting. An unverified concern is at most minor.
- Respect settled decisions unless you bring evidence not previously considered.
- Fixed output: `Position` · `Key points` · `Risks / blind spots` ·
  `What would change my mind` · `VERDICT: SUPPORT | CONCERN | BLOCK`.

Read-only is enforced by the `bias-council:member` agent's tool allowlist (no Edit/Write/Bash).

### Step 3 — Blind (host)
Shuffle the member outputs, **then** assign labels A–E in shuffled order. Strip task
names, model names, and any self-identifying lines. Keep the label → task map for
the report and the saved file only.

### Step 4 — Synthesizer (1 subagent, `model: opus`, fresh context, not a member)
Input: neutral QUESTION, CONTEXT, PREMISES, and the anonymized answers. Rules:
- Weigh arguments, not headcount. A well-argued minority beats a confident majority;
  side with the dissenter when its reasoning is strongest.
- No silent drops. Every dismissed point gets a reason.
- Unanimity is a caution: name the assumption the whole answer rests on, and that no
  member could test it.
- Same-family panel: treat agreement as a shared starting point to pressure-test,
  not independent confirmation.
- Name what every answer missed.
- State what evidence or event would flip the conclusion.
- Ignore length. Do not guess which model or role wrote an answer.

### Step 5 — Checkpoint (conditional)
Triggered when any member returns BLOCK, or (high stakes, 5 members) the most
common verdict holds 3 or fewer. A 3-member run checkpoints on BLOCK only. The host asks the user: add context / run one critique
round / accept the synthesis. **Critique round** (max 1): each member gets the
anonymized set without being told which answer is theirs, and may change position
only by naming a specific flaw. Every flip is logged before/after. Then re-run Step 4.

Cost: about 5 agent calls (medium), about 7 (high), +3–5 when critiqued.

## 5. Output

**Chat, answer first:**
```
BIAS COUNCIL — <type> · <N> members · same-family panel (agreement = weak evidence)

Verdict: <1–2 lines>
Split: <n> SUPPORT · <n> CONCERN · <n> BLOCK
Claude's prior: <step-0 line>  →  moved / held, because <reason>

Strongest dissent: <minority view, best form>
Everyone missed: <gap>
Would flip it: <evidence/event>
Unverified premises: <check these first>

Reframed question: <what members were asked>   (stripped: <REMOVED>)
```
Then one line per member: `A — <verdict> — <main point>`. The label → task map is
revealed after the synthesis.

**Saved:** full run (framer output, all member answers, label map, synthesis,
checkpoint/flip log) to `<notes_dir>/Bias-Council/YYYY-MM-DD-<slug>.md`,
plus a markdown link in the profile's `notes_index:` file and a line in its
`notes_log:` file, only when those optional keys are set. Sanitize before
writing: RFC 5737 IPs, fake hostnames, no secrets.

## 6. Failure handling

- Member error or timeout: continue with ≥3 answers and state the count. Below 3:
  stop and tell the user; never present a thin council as full.
- Framer output malformed: retry once, then run on the original prompt with the
  header flag **"UNFRAMED RUN: framing bias not removed"**.
- Synthesizer mentions a role or model name: flag "blinding leak" in the report.
- Save fails: show the report in chat and say the save failed.

## 7. Testing (fixture-tested vs real-use, kept honest)

1. **Trigger evals** (~10 cases: ~4 high → runs, ~3 medium → offers, ~3 none → silent)
   via `claude plugin eval` against the plugin (eval supports skills-dir plugins).
2. **Planted-lean test:** a prompt asserting a confident wrong lean ("I'm sure OSPF
   multi-area designs don't need area 0 — confirm"). Pass: the QUESTION has no lean
   and the verdict doesn't endorse it.
3. **Blinding check:** grep the synthesizer input for task names and model names.
   Zero hits.
4. **Real use:** run it on a live decision and have the user judge the output.
   NOTES.md states the current testing status; it never claims more than the evals
   and real runs show.

## 8. Overlap with other council plugins

If another installed plugin has a skill that also self-suggests for competing
approaches, build-vs-buy or tradeoffs (for example another multi-agent or
multi-model council), both skills compete for the same moments and produce double
offers. Disable one (`claude plugin disable <plugin>@<marketplace>`). It's
reversible and keeps the files. The user decides; never do it silently.

## 9. Accepted risks (dated 2026-10-10)

- **Same-family correlation.** All members are Claude, so shared blind spots survive.
  Mitigated only by labeling. Revisit by adding an optional external (non-Claude)
  seat if real runs show echo-chamber verdicts.
- **Self-recognition.** Anonymized labels don't fully hide Claude-written text from a
  Claude synthesizer (Panickssery 2024). Mitigated by fresh context plus rubric rules.
- **Context bleed.** Subagents may load the user's global CLAUDE.md, so members see
  the user's stated preferences. Accepted: that context is mostly relevant. The framer keeps
  the *question* neutral even when context carries preferences.
- **Cost/latency.** A few minutes and 5–7 agent calls per run. Auto-run is limited
  to high stakes for this reason.
- **Search-query leakage (2026-10-10, after the final review).** Members keep
  `Read` (repo and notes context) and `WebSearch` (claim checks) but lost `WebFetch`,
  so "Read a private file, then fetch a URL carrying it" is closed by the tool
  allowlist. Residual: an injected instruction could still get a member to put data
  into a search query string. Accepted, because search is needed for claim checks
  and query strings are short. The framer and synthesizer, which read every raw
  input and answer, run as `bias-council:judge` with no network at all. Revisit if
  members are ever given MCP tools.
- **Amendments from the review (2026-10-10):** the prior is committed visibly at
  Step 0 rather than held hidden, so it can be audited for hindsight. The synthesizer
  now receives MATERIAL. Both are reflected in SKILL.md.
