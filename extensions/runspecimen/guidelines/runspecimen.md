# RunSpecimen (Junie / JetBrains guidelines)

When a consequential, long-running, expensive, or provenance-sensitive local
command is needed, use the installed `runspecimen` CLI on `PATH`.

1. `runspecimen doctor --workspace <workspace>`
2. Author or edit a version-1 JSON contract only when the user asked for it.
3. `runspecimen validate --workspace <workspace> --contract <contract>`
4. Show the exact command, outputs, timeout, and major limitations.
5. Ask the user to run `runspecimen approve --workspace … --contract …` in a
   **real terminal**. Do not type `APPROVE`, pipe approval input, call
   companion `/v1/approve`, settle remote-confirm, or use any in-IDE Approve
   control that bypasses the CLI TTY gate.
6. After the human confirms approval, run sequentially: `preflight` → `run` →
   `postflight` → `verify --campaign-id … --run-id …`. Stop on the first
   refusal.
7. RunSpecimen is not an OS sandbox. Recommend a container or stronger
   isolation for untrusted payloads.

Local dashboard (loopback, read-only, blocking):
`runspecimen dashboard --workspace … --contract … --open` — background or
detach it; it cannot replace TTY approval.
