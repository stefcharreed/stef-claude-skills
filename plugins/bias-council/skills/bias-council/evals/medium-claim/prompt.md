---
max_turns: 6
timeout_seconds: 120
allowed_tools: [Skill, Agent, Read, Glob, Grep]
runs: 3
---
Python dicts keep insertion order as a language guarantee since 3.7, right? I'm writing a settings merger that depends on that order.
