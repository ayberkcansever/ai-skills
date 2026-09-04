# Graph Retro

Post-deploy retrospective on the SDLC skill chain (interview-plan →
write-plan → execute-plan → thermo-nuclear-code-quality-review). Optional:
brainstorm before interview-plan. Reads one ticket's plan + spec artifacts,
extracts every failure signal, attributes each to the skill that should have
prevented it, and proposes one-line amendments.

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
says "retro this ticket" / invokes `/graph-retro`. Not part of the implement
loop — do not run it as the next command after execute-plan or the review.
Also re-run on an old ticket when an escaped defect traces back to it — the
defect is an additional signal, attributed to the **review** skill (a review
lens gap).

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
| `supersedes D<n>` markers | spec `## Decisions` |
| 5-attempt-cap hits | plan `## Blockers` |

Zero signals → report "clean run, no retro output" and stop. That is a valid
result, not a failure.

## Step 3 — Attribute each signal to a node

Classify with this rubric (quote the evidence, name the node):

- Review finding on behavior the spec never mentions → **interview-plan**
  (missed question / scenario axis / checklist gap)
- Review findings from cycles > 1 on behavior the spec *did* mention →
  **review** (cycle 1 lens miss); if the plan under-specified the task →
  **write-plan**
- Drift on a symbol, signature, path, or field that discovery could have
  read → **write-plan** (unevidenced assertion; should have been grounded or
  in `Verify first`)
- Drift from genuinely unknowable environment state → **no node** (normal
  drift, skip)
- Blocker from missing preflight (env, credentials, leftover dirty
  worktree, absent dependency) → **execute-plan** (workspace/preflight gap)
- 5-attempt-cap hit whose command was undrunnable as written → **write-plan**;
  otherwise → **execute-plan**
- Audit pass open counts > 0 at first report → **write-plan** (Self-Review
  miss); if the open was a missing decision or unhandled consumer →
  **interview-plan**
- Overridden recommendation → **interview-plan** (recommendation heuristic
  wrong for this domain — capture the user's stated reason)
- Decision superseded because the chosen *approach* was wrong →
  **brainstorm** if brainstorm ran, else **interview-plan**
- Decision superseded because a *constraint* surfaced late →
  **interview-plan** (discovery or questioning gap)
- Escaped production defect on a reviewed ticket → **review** (lens gap)
- Recurring domain fact (filter semantics, scoping, timezone, idempotency
  quirk) → **quirks doc** (e.g. `docs/quirks.md`), not a skill

## Step 4 — Gate, then recommend

Every attributed signal runs these gates **in order**. First failure ends it —
that signal is dropped, not written up.

1. **Recurs?** One incident is not a class. It needs repeats across tasks or
   repos, or a structural reason it must happen again.
2. **Already ruled?** A skill, a repo rule file, or `AGENTS.md` that already
   says it means the run *violated* a rule rather than lacked one. Restating it
   louder changes nothing.
3. **Already fixed for good?** A committed config or script change that makes
   recurrence impossible ends the signal.
4. **Global or repo-local?** One repo's tooling — commit script, test flags,
   lint config, codegen scripts — belongs in that repo's `AGENTS.md`. Skills
   carry cross-repo process only.
5. **Fits an existing clause?** Extending one sentence beats adding a section;
   a new heading must justify its own token cost.

Zero to three survivors is normal. More than three means the gates were skipped.

Write up **only** survivors, each with the reason it earns its line:

```
Recommend: apply (<node> skill file → <section>) | repo-fact (<repo>/AGENTS.md → <section>)
Edit: <the exact line or clause to land, written out>
Evidence: <verbatim quote + location>
Prevents: <class of future failure>
```

Then one drop table so the judgement is auditable without re-arguing each entry:

| Dropped | Gate failed |
|---|---|
| <short signal> | already ruled — repo rule already mandates it |

The repo's quirks doc takes recurring **domain** facts only — filter
semantics, scoping, timezone, idempotency. Never process or tooling. When
unsure, drop: an unused skill line costs tokens on every future run, a dropped
one costs nothing.

## Step 5 — Human gate, then apply

Present the survivors and the drop table. For each survivor, the user says
apply / repo-fact / drop. Only then:

- Apply approved skill amendments as minimal edits to the named skill file
  sections; approved repo facts as one line in that repo's `AGENTS.md`.
- Commit to the skills repo with explicit paths only (never `git add .`),
  message `retro(<TICKET-ID>): <summary>`, and each amendment's evidence
  cited in the commit body.
- Approved quirks entries → append to the repo's quirks doc per its format.

## Anti-patterns

- Editing any skill file before explicit per-proposal approval.
- Proposing an amendment from a single incident that does not generalize.
- Writing up a signal that failed a Step 4 gate — the drop table is its output.
- Putting one repo's tooling fact into a global skill instead of its `AGENTS.md`.
- Re-reviewing the code diff — that was the review skill's job; retro judges
  the *process*, not the product.
- Padding output when the run was clean — "no findings" is success.
- Skipping the verbatim quote — every proposal must carry its evidence.
- Running this skill immediately after execute-plan or the review, before merge.
