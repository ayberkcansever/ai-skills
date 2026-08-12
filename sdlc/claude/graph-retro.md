# Graph Retro

Post-deploy retrospective on the SDLC skill chain (brainstorm → interview-plan
→ write-plan → execute-plan → thermo-nuclear-code-quality-review). Reads one
ticket's plan + spec artifacts, extracts every failure signal, attributes each
to the skill that should have prevented it, and proposes one-line amendments.

The insight: the chain already **produces** its own improvement telemetry —
drift notes, blockers, review findings, overridden recommendations — but
nothing consumes it. This skill is the feedback edge that closes the loop.

**This skill never edits skill files on its own.** Output is proposals; the
user approves each before anything is applied. Approved amendments are
committed to the skills directory with the ticket ID in the commit message —
keep that directory a git repo so every change is a reviewed, revertible
commit whose history answers "why does this rule exist".

**Announce at start:** "I'm using the graph-retro skill to retro this ticket."

## When to run

After the ticket is merged and the deploy is verified, or whenever the user
says "retro this ticket" / invokes `/graph-retro`.

## Step 1 — Locate artifacts

Resolve `<TICKET-ID>` from the branch name or ask once. Read, in order found:

- Plan file: `docs/features/<TICKET-ID>/*-implementation-plan.md`, else
  `docs/plans/<TICKET-ID>/*-implementation-plan.md`
- Spec: `docs/features/<TICKET-ID>/design.md`, else
  `docs/specs/<TICKET-ID>/spec.md`

Multi-repo tickets: check every repo in the workspace for the same
`<TICKET-ID>` paths. Missing plan AND spec → report "nothing to retro" and
stop.

## Step 2 — Extract signals

Scan the artifacts for exactly these, quoting each verbatim with its location:

| Signal | Where |
|---|---|
| `> Drift:` notes | plan file, under steps |
| `## Blockers` entries (incl. resolved) | plan file |
| Review findings from cycles > 1 | plan `## Review` section |
| Audit pass open counts > 0 at first report | plan header / audit record |
| `(overrides recommendation: ...)` | spec `## Decisions` |
| 5-attempt-cap hits | plan `## Blockers` |

Zero signals → report "clean run, no retro output" and stop. That is a valid
result, not a failure.

## Step 3 — Attribute each signal to a node

Classify with this rubric (quote the evidence, name the node):

- Review finding on behavior the spec never mentions → **interview-plan**
  (missed question / scenario axis / checklist gap)
- Drift on a symbol, signature, path, or field that discovery could have
  read → **write-plan** (unevidenced assertion; should have been grounded or
  in `Verify first`)
- Drift from genuinely unknowable environment state → **no node** (normal
  drift, skip)
- Blocker from missing preflight (env, credentials, dirty tree, absent
  dependency) → **execute-plan** (workspace/preflight gap)
- Overridden recommendation → **interview-plan** (recommendation heuristic
  wrong for this domain — capture the user's stated reason)
- Recurring domain fact (filter semantics, scoping, timezone, idempotency
  quirk) → **quirks doc** (e.g. `docs/quirks.md`), not a skill

## Step 4 — Propose amendments

For each attributed signal, one proposal:

```
Signal: <verbatim quote + location>
Node: <interview-plan | write-plan | execute-plan | review | quirks>
Amendment: <one sentence, with the target file and section it would land in>
Generalizes: <the class of future failure it prevents — not just this incident>
```

**Filter hard:** an amendment must prevent a *class*, not memorialize an
incident. Incident-shaped facts go to the repo's quirks doc instead. When
unsure, quirks — skill files must stay lean; every added line costs tokens on
every future run.

## Step 5 — Human gate, then apply

Present all proposals as one compact list. For each, the user says apply /
quirks / drop. Only then:

- Apply approved skill amendments as minimal edits to the named skill file
  sections.
- Commit to the skills repo with explicit paths only (never `git add .`),
  message `retro(<TICKET-ID>): <summary>`, and each amendment's evidence
  cited in the commit body.
- Approved quirks entries → append to the repo's quirks doc per its format.

## Anti-patterns

- Editing any skill file before explicit per-proposal approval.
- Proposing an amendment from a single incident that does not generalize.
- Re-reviewing the code diff — that was the review skill's job; retro judges
  the *process*, not the product.
- Padding output when the run was clean — "no findings" is success.
- Skipping the verbatim quote — every proposal must carry its evidence.
