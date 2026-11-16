---
description: Run tests and an independent review for the current implementation
agent: build
subagent: false
---

Finish the current implementation safely.

Scope: $ARGUMENTS

Follow this sequence:

1. Inspect the current git status and diff. If the scope is empty, use the current working-tree changes.
2. Identify the smallest relevant test or validation commands from the repository instructions and existing project tooling.
3. Run the focused tests first. If they fail, stop the workflow, do not change source files, and report the failures with the exact commands and likely cause.
4. If focused tests pass, run broader checks only when they are clearly supported by the project and reasonably bounded.
5. After tests pass, invoke the `review` subagent to review the current diff for correctness, regressions, security concerns, and missing tests. The reviewer must not edit files.
6. Return a concise report with changed files, tests run and outcomes, reviewer findings, remaining risks, and a suggested commit message.

Safety rules:

- Do not commit, push, merge, reset, clean, deploy, or delete files.
- Do not modify source files, tests, manifests, or documentation during this verification workflow.
- Ask for permission when a command requires it; do not use auto-approval.
- Never print secrets, tokens, credentials, or `.env` values.
