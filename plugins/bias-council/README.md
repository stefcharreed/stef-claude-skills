# bias-council

A blind council of independent read-only subagents (framer, panel members, synthesizer) for high-stakes decisions, claims, plans and drafts. Members never see each other or the model names. The synthesizer weighs the answers blind.

- Design and the reasoning behind it: `skills/bias-council/DESIGN.md`
- Tests: `python3 skills/bias-council/scripts/check.py static` (structure and tool allowlists) plus 10 eval prompts in `skills/bias-council/evals/`
- Saved runs go to `<notes_dir>/Bias-Council/` (`notes_dir` from your profile), or `./Bias-Council/` without one.
