# Gates — confirm, candidate pool, must-not-miss

Read this at **full-mode Step 5**, after triage validates. Quick mode never reads this file.

Contents:

- Contender vs landscape tiers
- Per-candidate record
- Must-not-miss checklist (12 buckets)
- Coverage gate
- Quadrant balance gate

Do not place blips until both gates pass.

## Tiers

Split surviving keeps. Confirming searches are expensive; only the top two rings need them.

**Contender tier — could plausibly reach Learn or Try.** One confirming search each (`"X in production"`, `"migrating to X"`, `"X postmortem"`, `"X GA"`). Aim **12–18** contenders; budget **≤20** confirming searches. Evidence bar: **≥2 independent dated signals from different sources** plus the confirming search. One vendor launch is not momentum.

**Landscape tier — everything else that is a real topic.** No confirming search, no cap. Watch or Skip from triage evidence. Evidence bar: **≥1 dated signal** and a defensible one-line ring reason. Typical full scan: **25–35 blips total**.

Total agent search budget per full scan (manual sweep + wildcard + confirm) stays roughly **25–35 calls**. Growing the landscape tier does not move that number.

**Skip is not a dumping ground.** A Skip blip is a topic you would hear about and wonder whether to learn — visible buzz that fails the lens. Routine releases, artifacts of another blip, and folded angles are *not* topics; they are one-liners under their quadrant (see [output.md](output.md)). If you cannot write a promote-back condition, it is not a Skip blip.

**Window exception — continuing momentum:** a landmark from 3–6 months ago stays eligible if the window still shows migration posts, GA follow-through, conference tracks, or HN recurrence.

## Per-candidate record

For each candidate in either tier:

- name + one-line what-it-is
- **quadrant** (`Techniques`, `Platforms`, `Tools`, `Languages & Frameworks`)
- category (`AI-ML`, `Infrastructure`, `Data`, `Security`, `Languages-Frameworks`, `DevTools`, `Web`, `Other`)
- **momentum evidence, dated** — to the bar of its tier
- maturity: research / early-adopter / production-adopted
- which must-not-miss bucket(s) it satisfies

## Must-not-miss checklist

Clear every bucket: ≥1 candidate **or** a one-line "cleared: quiet / not principal-leverage". Two strands of six, deliberately equal — an AI-heavy checklist manufactures the skew the balance gate then flags.

**AI strand**

1. **Agent/tool protocols** — MCP, A2A, new wire-level agent standards
2. **Agent security threat models** — lethal trifecta / permission-hungry agents / structural mitigations
3. **Evals & release control** — agent evals, online evals, CI gating quality
4. **Inference / serving infra** — Gateway API Inference, vLLM/KServe, AI gateways, GPU scheduling
5. **Coding-agent harnesses & agent state** — Agent Skills, harness engineering, spec-driven workflows, production memory layers (not chat "memory" demos)
6. **Model economics / routing** — multi-tier model strategy, open-weight vs closed tradeoffs

**Non-AI strand**

7. **Platform shifts** — K8s/CNCF graduations, edge/serverless, WASM, cloud primitives
8. **Data & storage engines** — database majors, query/analytics engines, open table formats, streaming and CDC
9. **Observability & operations** — OpenTelemetry, eBPF, continuous profiling, incident practice, SRE/DORA
10. **Security & supply chain** — CVE-class events with architectural consequences, sigstore/SLSA/SBOM, memory safety, post-quantum
11. **Techniques & practices** — architecture patterns with adoption evidence (Thoughtworks blips/themes, DORA, migration writeups)
12. **Languages, frameworks & web platform** — language majors, framework majors, TC39/stdlib, browser/build-tool primitives, notable deprecations

## Coverage gate

All of these must be true:

- every erroring feed got its fallback search
- every truncated feed got its direct search (or a raised `cap`)
- every manual feed the crawler printed was covered
- `validate_triage.py` exited 0
- every `new`-flagged item is kept or named under a drop reason
- ≥3 pool candidates come from sources other than the top HN stories
- **≥1 candidate came from something other than the consensus band** — a `disc` item, a manual source, or a wildcard hit (anti-groupthink: 400-upvote-only radars lag)

## Quadrant balance gate

- pool holds **≥3 candidates per quadrant**, or document a quadrant as genuinely quiet
- without an AI focus filter, at most **half** the pool may be `AI-ML`
- Learn ring must span **≥3 quadrants** (checked at placement; fail here if the contender set cannot support it)

Fail a gate → widen (more manual sources, second wildcard pass) and re-pass. Do not place blips until both gates pass.

Then return to [workflow.md](workflow.md) Step 6–7.
