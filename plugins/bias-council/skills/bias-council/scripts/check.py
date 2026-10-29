#!/usr/bin/env python3
"""Deterministic checks for the bias-council skill.

  python3 scripts/check.py static              structure of SKILL.md, prompts, agent
  python3 scripts/check.py blinding <t.jsonl>  synthesizer prompt leaks task/model names
  python3 scripts/check.py saved <report.md>   saved report has only RFC 5737 IPv4s

Exit 0 = pass, 1 = fail. Functions return lists of problems; only main() prints.
"""
import ipaddress
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Plugin layout: agents/ sits at the plugin root, two levels above the skill dir.
AGENTS = ROOT.parent.parent / "agents"

# Source of truth for task ids; SKILL.md and references/prompts.md must match.
TASKS = {
    "decision": ["contrarian", "pre-mortem", "outside-view", "steelman-alternative", "assumptions-check"],
    "claim": ["contrarian", "re-derivation", "counter-evidence", "outside-view", "assumptions-check"],
    "plan": ["red-team", "pre-mortem", "simplest-alternative", "assumptions-check", "blast-radius"],
    "writing": ["contrarian", "overclaim-check", "skeptical-reader", "slant-check", "clarity-cut"],
}
PROMPT_KEYS = ["FRAMER", "MEMBER_RULES", "SYNTHESIZER", "CRITIQUE"]
LEAK_TERMS = sorted({t for ts in TASKS.values() for t in ts}
                    | {"opus", "sonnet", "haiku", "fable", "adversary", "devil's advocate"})
# Allowlists, not denylists: anything else (Bash, Write, mcp__*) fails.
AGENT_TOOLS = {
    "member": {"Read", "Grep", "Glob", "WebSearch"},  # no WebFetch: no read-then-exfiltrate path
    "judge": {"Read", "Grep", "Glob"},                # framer + synthesizer: no network at all
}
AGENT_TYPES = {"bias-council:member", "bias-council:judge"}
# Behaviour rules SKILL.md must keep; each phrase pins one rule against silent drift.
SKILL_PHRASES = {
    "Never substitute another agent type": "no fallback to an agent type outside the read-only allowlist",
    "only when the user explicitly asks": "Claude's own earlier answer stays out unless the user asks for its review",
    "never shorten": "member answers pass verbatim apart from redactions",
    "committed before the council": "prior is committed visibly before Step 1, so it can't be rewritten in hindsight",
    "no new fact": "settled refusal only for the settled item itself",
    "check.py saved": "saved report is machine-checked",
    "1 + (character count of QUESTION) mod (N − 1)": "rotation always moves answer A",
    "answers that survived": "checkpoint keyed on surviving answers",
    "rerun from Step 1": "added context goes back through the framer",
    "Never paraphrase": "MATERIAL is passed verbatim",
    "CLAIM = the user's sentence": "UNFRAMED fallback fills every field",
    "Start the report with the literal line": "report block is mandatory, not replaced by prose",
    "Steps 6 and 7 are not optional": "report and save always run",
    "quick look": "posts framed as a quick look still trigger",
}
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]


def frontmatter(text):
    """Flat key: value pairs between the first two '---' lines (one-line values only)."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fields = {}
    for line in parts[1].strip().splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields


def section(text, key):
    """Body of a '## KEY' section up to the next '## ' heading."""
    match = re.search(rf"^## {re.escape(key)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def leak_pattern(term):
    # 'pre-mortem' should also catch 'pre mortem'
    return re.compile(r"\b" + re.escape(term).replace(r"\-", r"[-\s]") + r"\b", re.I)


def check_static(root=ROOT):
    problems = []
    paths = {
        "skill": root / "SKILL.md",
        "prompts": root / "references" / "prompts.md",
        "member": AGENTS / "member.md",
        "judge": AGENTS / "judge.md",
    }
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        return [f"missing file: {m}" for m in missing]
    skill, prompts = paths["skill"].read_text(), paths["prompts"].read_text()

    fm = frontmatter(skill)
    if fm.get("name") != "bias-council":
        problems.append("SKILL.md: name must be 'bias-council'")
    desc = fm.get("description", "")
    if not desc:
        problems.append("SKILL.md: missing one-line description")
    elif len(desc) > 1024:
        problems.append(f"SKILL.md: description is {len(desc)} chars (max 1024)")
    for phrase, why in SKILL_PHRASES.items():
        if phrase not in skill:
            problems.append(f"SKILL.md: missing rule '{phrase}' ({why})")
    if skill.count("subagent_type: bias-council:judge") < 2:
        problems.append("SKILL.md: framer and synthesizer must use bias-council:judge")
    if "MATERIAL" not in section(skill, "Step 4: Synthesize"):
        problems.append("SKILL.md: Step 4 must pass MATERIAL to the synthesizer")
    if "CLAIM: <" not in skill:
        problems.append("SKILL.md: FRAMED block must carry a CLAIM line")

    for key in PROMPT_KEYS:
        if not section(prompts, key).strip():
            problems.append(f"prompts.md: missing or empty '## {key}'")
    for typ, ids in TASKS.items():
        for task in ids:
            if f"### {typ}/{task}" not in prompts:
                problems.append(f"prompts.md: missing '### {typ}/{task}'")
        if " · ".join(ids) not in skill:
            problems.append(f"SKILL.md: task row for '{typ}' must list: {' · '.join(ids)}")

    synth = section(prompts, "SYNTHESIZER")
    for term in LEAK_TERMS:
        if leak_pattern(term).search(synth):
            problems.append(f"prompts.md: SYNTHESIZER prompt itself contains leak term '{term}'")
    if "MATERIAL" not in synth:
        problems.append("prompts.md: SYNTHESIZER data list must include MATERIAL")
    if "MATERIAL" in section(prompts, "FRAMER").split("Output exactly", 1)[-1]:
        problems.append("prompts.md: FRAMER must not output a MATERIAL section (host passes it verbatim)")
    if "WebFetch" in section(prompts, "MEMBER_RULES"):
        problems.append("prompts.md: MEMBER_RULES must not offer WebFetch")

    for name in AGENT_TOOLS:
        afm = frontmatter(paths[name].read_text())
        tools = {t.strip() for t in afm.get("tools", "").split(",") if t.strip()}
        if not tools:
            problems.append(f"agents/{name}.md: no tools allowlist (missing = ALL tools)")
        elif not tools <= AGENT_TOOLS[name]:
            problems.append(f"agents/{name}.md: tools outside allowlist {sorted(tools - AGENT_TOOLS[name])}")

    for key, path in paths.items():
        if re.search(r"\b(TODO|TBD)\b", path.read_text()):
            problems.append(f"{path.name}: contains TODO/TBD")
    return problems


def council_agent_calls(jsonl_path):
    """Agent tool_use inputs whose description starts with 'bias-council'."""
    calls = []
    for line in Path(jsonl_path).read_text().splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Real eval traces mix record shapes: some are not dicts, some carry a string message.
        message = record.get("message") if isinstance(record, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "tool_use" or item.get("name") != "Agent":
                continue
            inp = item.get("input") or {}
            if str(inp.get("description", "")).lower().startswith("bias-council"):
                calls.append(inp)
    return calls


def check_blinding(jsonl_path):
    calls = council_agent_calls(jsonl_path)
    problems = [f"Agent call '{c.get('description')}' used subagent_type '{c.get('subagent_type')}'"
                for c in calls if c.get("subagent_type") not in AGENT_TYPES]
    prompts = [str(c.get("prompt", "")) for c in calls if "synthesizer" in str(c.get("description", "")).lower()]
    if not prompts:
        return problems + ["no 'bias-council synthesizer' Agent call found in transcript"]
    for i, prompt in enumerate(prompts, 1):
        # Scan everything after the fixed template (its last spec line is PER ANSWER:)
        # so leaks in CONTEXT/PREMISES count too, not just in the answers.
        body = prompt.split("PER ANSWER:", 1)[1] if "PER ANSWER:" in prompt else prompt
        for term in LEAK_TERMS:
            if leak_pattern(term).search(body):
                problems.append(f"synthesizer call {i}: possible leak '{term}' (inspect; may be a plain word)")
    return problems


def check_saved(report_path):
    problems = []
    for raw in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", Path(report_path).read_text()):
        try:
            ip = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if not any(ip in net for net in DOC_NETS):
            problems.append(f"non-RFC5737 IPv4 in saved report: {raw}")
    return problems


def main(argv):
    if len(argv) < 2 or argv[1] not in ("static", "blinding", "saved"):
        print(__doc__)
        return 2
    mode = argv[1]
    if mode == "static":
        problems = check_static()
    elif len(argv) < 3:
        print(f"usage: check.py {mode} <path>")
        return 2
    else:
        problems = check_blinding(argv[2]) if mode == "blinding" else check_saved(argv[2])
    for p in problems:
        print(f"FAIL {p}")
    print("PASS" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
