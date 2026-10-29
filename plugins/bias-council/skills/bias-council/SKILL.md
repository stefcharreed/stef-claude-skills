---
name: bias-council
description: "Blind council of independent read-only Claude subagents that reduces bias in a decision, claim, plan or piece of writing. Three tiers. HIGH stakes, one-way or public (job offer or stay-vs-leave, career path change, plan about to run on production systems or live infrastructure, a post or other writing the user is about to publish or send even when framed as a quick look, spending real money): invoke this skill now. MEDIUM stakes, reversible but relied on (choosing between tools or architectures, a technical claim the user will build on, a plan change): do NOT invoke yet; answer normally, then end the reply with this exact line: 'Want a bias council check on this? (~5 agents, a few minutes)'. Invoke on yes. NONE (fact lookups, mechanical edits, quick fixes, 'just tell me', a question already settled in a DECISIONS file or CLAUDE.md): never mention it. Explicit requests always invoke: bias check, council, second opinion, devil's advocate, red team, pre-mortem, /bias-council."
---

# bias-council

Runs a blind council of independent Claude subagents to reduce bias in a decision,
claim, plan or piece of writing:
prior → neutral reframe → independent members with assigned procedures (a contrarian
every run) → rotate + anonymize → fresh synthesizer → checkpoint only on a split.

Read `references/prompts.md` before Step 1. Two agent types, and only these:
- **Members** run as `bias-council:member` (Read, Grep, Glob, WebSearch).
- **The framer and synthesizer** run as `bias-council:judge` (Read, Grep, Glob, no network).

**Never substitute another agent type.** If either type is unavailable or an Agent
call fails on it, stop and say
`Council could not run: bias-council agents not loaded (try /reload-plugins).`

The panel is one model family (Claude), so agreement is weak evidence, and every
report says so.

## When to run

| Stakes | Examples | Do |
|---|---|---|
| High: one-way door or public | job offer / stay-vs-leave, career path change, plan about to run on production systems or live infrastructure, something the user is about to publish or send (even framed as a "quick look"), spending real money | Run now. First line: `Running a bias council — <why this is high-stakes>.` 5 members. |
| Medium: reversible but relied on | tool or architecture choice, technical claim the user will build on, plan change | Answer normally, then end with: `Want a bias council check on this? (~5 agents, a few minutes)`. Run only on yes, with 3 members. |
| None | fact lookup, mechanical edit, quick fix, "just tell me" | Don't mention the skill. |

- **Settled decisions.** Refuse only when the question itself is a decision already
  recorded in a DECISIONS file or the user's CLAUDE.md, and the user brings no new
  fact. In that case, say it's settled, cite the source, and offer a council if new
  evidence appears. A new event (e.g. an actual offer arriving) is a new fact, so run.
  Related settled items go under SETTLED; they never block a run.
- **Explicit requests always run** (bias check, council, second opinion, devil's
  advocate, red team, pre-mortem, `/bias-council`): 5 members if the stakes are high
  or the user says "full", else 3.

## Step 0: Prior

Before spawning anything, print this line (right after the `Running a bias council`
line, if there is one):

`Claude's prior (committed before the council): <your verdict> — <main reason>`

It is committed here so the final comparison can't be rewritten in hindsight. Never
put it in any subagent prompt; subagents never see the conversation.

## Step 1: Frame

1. **Gather CONTEXT** the panel needs: relevant facts from the conversation, short file
   excerpts, constraints.
   - **Settled decisions:** `Glob` for `**/DECISIONS*.md` in the current project, and
     check the user's CLAUDE.md files. List matches under SETTLED with their source.
     If the exact question is a settled item and there is no new fact, stop here (see
     When to run).
   - **What's under review** is what the user asked about. Include your own earlier
     answer as MATERIAL only when the user explicitly asks to review that answer.
     Otherwise leave your prior and any recommendation you made earlier out entirely.
2. **Copy any document under review VERBATIM as MATERIAL**, for every type: plan text,
   the full writing, the source of a claim, an offer letter behind a decision.
   Never paraphrase or shorten it. With no document, MATERIAL is `none`.
3. **Spawn the framer:** one Agent with `subagent_type: bias-council:judge`,
   `model: sonnet`, `description: bias-council framer`. Prompt = the FRAMER section,
   with `{{INPUT}}` (the user's request verbatim), `{{CONTEXT}}` and `{{MATERIAL}}`
   filled in.
4. **Check the reply** has all headed sections: TYPE, QUESTION, OPTIONS, CLAIM,
   CONTEXT, SETTLED, PREMISES, REMOVED. If any is missing, retry once. If it fails
   again, fill the fields yourself:
   - QUESTION = the user's request; TYPE = your best guess;
   - CLAIM = the user's sentence (claims only, else `n/a`);
   - SETTLED = what Step 1.1 found;
   - OPTIONS, CONTEXT, PREMISES = `n/a`; REMOVED = `nothing`;
   - add the flag `UNFRAMED RUN — framing bias not removed`.

## Step 2: Members

Take the first N tasks (N = 5 high, 3 medium) for the TYPE. The ids match
`references/prompts.md` `### <type>/<id>`:

| TYPE | Tasks in order |
|---|---|
| decision | contrarian · pre-mortem · outside-view · steelman-alternative · assumptions-check |
| claim | contrarian · re-derivation · counter-evidence · outside-view · assumptions-check |
| plan | red-team · pre-mortem · simplest-alternative · assumptions-check · blast-radius |
| writing | contrarian · overclaim-check · skeptical-reader · slant-check · clarity-cut |

Spawn all N in ONE message so they run in parallel. Each one gets:
- `subagent_type: bias-council:member`;
- `model: opus` for the first task (contrarian / red-team), `sonnet` for the rest;
- `description: bias-council member`;
- prompt = MEMBER_RULES + the task's TASK text + this FRAMED block:

```
QUESTION: <framer QUESTION>
OPTIONS: <framer OPTIONS>
CLAIM: <framer CLAIM>
MATERIAL: <the VERBATIM text from Step 1.2, or none>
CONTEXT: <framer CONTEXT>
SETTLED: <framer SETTLED>
PREMISES: <framer PREMISES>
```

A member prompt never contains the conversation, your prior, REMOVED, or another
member's output.

Wait for all of them. Drop any member that errors or returns no final VERDICT/CHOICE
line. If fewer than 3 remain, stop and tell the user the council could not run (say
how many answered). Never present a partial result as a council.

## Step 3: Blind

1. **Rotate.** N = the number of answers that survived. Rotate left by
   k = 1 + (character count of QUESTION) mod (N − 1): move the first k answers to the
   end, keeping their order. Ceiling: this is deterministic, not a true shuffle, but
   answer A is never the first task (the contrarian).
2. **Label** the rotated answers A, B, C, D, E.
3. **Redact.** In each answer, replace any task name, model name or role
   self-description ("as the contrarian", "Pre-mortem:") with `[redacted]`. Apart from
   these redactions, pass each answer verbatim; never shorten, summarize or reorder it.
4. **Keep the label → task map** for the report only.

## Step 4: Synthesize

Spawn one Agent: `subagent_type: bias-council:judge`, `model: opus`,
`description: bias-council synthesizer`.

Prompt, in this order:
1. the SYNTHESIZER section;
2. QUESTION, OPTIONS, CLAIM, MATERIAL (verbatim), CONTEXT, SETTLED, PREMISES;
3. a line containing only `ANSWERS`;
4. the labeled answers.

Nothing else: no conversation, no prior, no label map.

If the reply uses a task id or model name as a label for an answer, add the flag
`blinding leak — synthesizer named a role/model`.

## Step 5: Checkpoint (only on a split)

Count the final lines of the answers that survived (N). Checkpoint when:
- any answer returned BLOCK;
- N is 4–5 and the most common VERDICT (or CHOICE, for decisions) holds N − 2 or fewer;
- N is 3: only on BLOCK (decisions: also when all 3 CHOICEs differ).

Ask with AskUserQuestion: "The council split (<SPLIT>). How do you want to proceed?"
Options: `Accept synthesis` (Recommended) / `Run one critique round` / `Add context first`.
- **Add context first:** add the user's addition to the CONTEXT you gathered and
  rerun from Step 1. The framer neutralizes it before members see it.
- **Critique round** (max 1):
  - For each surviving task, spawn a fresh `bias-council:member` on the same model.
    Prompt = MEMBER_RULES + that task's TASK text + the CRITIQUE section + the FRAMED
    block + a line `ANSWERS` + the same anonymized set.
  - Log each task's verdict before → after, with the CHANGED reason.
  - Re-blind (Step 3) and rerun Step 4 on the new answers.
- **AskUserQuestion unavailable** (non-interactive run): accept the synthesis and
  add the flag `checkpoint skipped`.

## Step 6: Report

Steps 6 and 7 are not optional. Start the report with the literal line
`BIAS COUNCIL — …` and print this block with its fields filled. Any plain-language
explanation goes after the block, never instead of it.

```
BIAS COUNCIL — <TYPE> · <N> members · same-family panel (agreement = weak evidence)
<flags, one per line, if any>

Verdict: <VERDICT>
Split: <SPLIT>
Claude's prior: <the committed Step-0 line>  →  <moved | held>, because <one clause comparing it with VERDICT>

Strongest dissent: <STRONGEST DISSENT>
Everyone missed: <EVERYONE MISSED>
Would flip it: <WOULD FLIP IT>
Unverified premises: <UNVERIFIED PREMISES TO CHECK FIRST>

Reframed question: <QUESTION>   (stripped: <REMOVED>)
```

Then the PER ANSWER lines. Then `Roles: A = <task>, B = <task>, …`, revealed only
now. If a critique round ran, add one `Flips: <task>: <before> → <after> — <reason>`
line per change.

## Step 7: Save

If ~/.config/claude-skills/profile.md is missing, or has no `notes_dir:` line, use `.` as
`<notes_dir>` (the run saves to `./Bias-Council/`). Otherwise read its `notes_dir:` line
(flat `key: value`), plus the optional `notes_index:` and `notes_log:` lines (file paths).

1. **Write the full run** to
   `<notes_dir>/Bias-Council/<YYYY-MM-DD>-<short-slug>.md`.
   - Frontmatter is optional. Example, if the user's notes use it: `description:` (one line), `created:`.
   - Body: the report, the framer output, MATERIAL, every member answer under its label and role, the synthesizer output, and any checkpoint or flip log.
   - Sanitize before writing: real IPs become RFC 5737 addresses (192.0.2.x, 198.51.100.x, 203.0.113.x), real hostnames become fake ones, and secrets are dropped.
2. **Index it** (only if the profile sets `notes_index:`): append a plain markdown link to that file:
   `- [Bias council: <verdict in 10 words or fewer>](<path to the saved file>)`
3. **Log it** (only if the profile sets `notes_log:`): append to that file:
   `- <YYYY-MM-DD>: bias council (<TYPE>, <N> members): <verdict in 15 words or fewer>. Saved <path to the saved file>.`
4. **Check it** if Bash is available:
   `python3 <this skill's base directory>/scripts/check.py saved <file>`.
   On FAIL, replace the flagged addresses with RFC 5737 ones, rewrite the file and
   re-run until PASS. It checks IPv4 only; hostnames and secrets rely on the
   sanitizing in step 1.
5. **If any write fails**, add `Save failed: <reason>` under the report. The chat
   report stands either way.
