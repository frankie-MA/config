---
description: Investigate a Graph incident read-only with graded evidence
agent: incident
subagent: true
---

Investigate this Graph/ai-fura incident in read-only mode:

<incident>
$ARGUMENTS
</incident>

Use the `incident` agent's safety rules. Do not modify files, run shell
commands, run `tests/test_live_*.py`, access Jira/GigaChat/IDP, send messages,
or change deployment state.

Read the repository instructions first. Work from the bounded scope supplied by
the user; if it is empty, ask the parent session for a precise incident scope
instead of scanning the whole repository.

The report must distinguish current source evidence, local evidence, historical
evidence, deployment evidence, and closed-segment/live evidence. It must list
confirmed facts separately from hypotheses and must not call the incident fixed
or production-ready without authoritative closed-segment evidence.
