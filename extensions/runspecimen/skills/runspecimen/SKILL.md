---
name: runspecimen
description: Use when a consequential local command should be explicitly approved, bounded to one workspace execution, provenance-checked, postflighted, and issued a tamper-evident receipt. Also use for RunSpecimen contract authoring, status, diagnosis, receipt verification, or explaining what the product does (about / docs).
---

# RunSpecimen

Use the installed `runspecimen` CLI as the enforcement boundary. The CLI must be
on `PATH` (`command -v runspecimen`). Never imitate an approval, call internal
test helpers, pipe approval input, settle remote-confirm, call companion
`/v1/approve`, or weaken a contract to make a refusal disappear. Host adapters
(Codex, Cursor, Claude Code, Grok Build, Gemini CLI, Junie, Windsurf, MCP) omit
`approve` on purpose.

For a short product summary and documentation URLs, run `runspecimen about` or
point the user at the dashboard About panel (User guide and FAQ links open on
GitHub).
## Workflow

1. Run `runspecimen doctor --workspace <workspace>`.
2. Read the intended command, source roots, outputs, bounds, assertions, and
   predecessor. Create or edit a version-1 JSON contract only when the user has
   asked for it.
3. Run `runspecimen validate --workspace <workspace> --contract <contract>`.
4. Show the user the exact command, outputs, timeout, and major limitations.
5. Ask the user to run `runspecimen approve --workspace <workspace> --contract
   <contract>` in a real terminal. Pause until they confirm it completed; an
   agent must not enter `APPROVE` for them. Do **not** use the iOS companion
   remote-confirm path from an agent, and do **not** paste Mac challenges into
   chat. Optional remote human confirm is human-only (ADR-004) and is not
   equivalent to local TTY APPROVE.
6. Run sequentially:
   - `runspecimen preflight --workspace <workspace> --contract <contract>`
   - `runspecimen run --workspace <workspace> --contract <contract>`
   - `runspecimen postflight --workspace <workspace> --contract <contract>`
   Stop at the first refusal or failure and preserve the evidence.
7. Verify with the full flags (campaign and run IDs must match the contract):

```bash
runspecimen verify --workspace <workspace> --contract <contract> \
  --campaign-id <campaign_id> --run-id <run_id>
```

Report the certificate ID from the verify JSON.

Use `runspecimen status --workspace <workspace> --campaign-id <campaign_id>
--run-id <run_id>` for read-only diagnosis. Never run lifecycle steps
concurrently, reuse a terminal run ID, overwrite asserted outputs, or continue
past a missing or failed postflight. RunSpecimen is not an OS sandbox; recommend
a container or stronger isolation for untrusted payloads.

## Local dashboard

When the user asks for a visual interface, launch the contract-scoped local
dashboard with:

```bash
runspecimen dashboard --workspace <workspace> --contract <contract> --open
```

`dashboard` is a **blocking** foreground process (`serve_forever`). Agents must
background it, detach it, or run it in a separate terminal so the session stays
usable for `approve` / lifecycle commands. Do not treat a hung agent shell as a
dashboard failure.

It is loopback-only and read-only. It may show the About overview, status, and
the exact commands, but it must never be described as an approval mechanism or
used to bypass the real-TTY approval step.
