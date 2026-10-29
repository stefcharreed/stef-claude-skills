---
type: llm
focus: last_message
---
Pass if the report identifies the lockout risk (applying a restrictive ACL to the management interface over SSH with no console or out-of-band access) and recommends a safeguard such as a timed rollback (reload in / configure confirm / commit confirmed), confirming the source address is permitted first, or securing console access. Fail if it approves the plan without naming the lockout risk.
