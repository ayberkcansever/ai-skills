---
name: view-plan
description: >-
  Draw a prepare-plan plan as one page of pictures a person can take in at a
  glance: the business flows and the technical flows as simple animated
  drawings, plus the product's real screens. Use when the user runs view-plan
  or asks to see, picture, or visualize a plan (sdlc-lite chain). On demand
  only; it never changes the spec or the plan.
argument-hint: "[plan name]"
disable-model-invocation: true
---

# View Plan

Input: $ARGUMENTS

A spec is written for the agents that build it. This page is for the person
who approves it: they should understand what changes, for whom, and how it
works without reading a single decision. If they have to read prose to get a
flow, the drawing failed.

**Reads:** `<root>/docs/plans/<plan>/spec.md` and `plan.md` (`<root>` and
`<plan>` as in prepare-plan; no name → the plan from this session), the code
the spec cites, and any recorded screenshots of the product.
**Writes:** only the page's own folder (below). Never the spec or the plan.

## What goes on the page

- **The change, in one moving picture.** A hero with a before / after toggle
  that plays once on load: the thing the user will notice, in the product's
  own words.
- **Business flows**, about 3 to 5: what the user does and what happens to
  them or their money. Take them from the Goal, the `[product]` decisions and
  their `Example:` values, and the failure scenarios a user would hit.
- **Technical flows**, about 2 to 4: first "the pieces" (which parts talk to
  which, the path the data takes), then only the mechanisms the plan's safety
  or correctness hangs on — what happens on a crash, a retry, a duplicate,
  a mixed-version deploy.
- **Real screens**, where they exist. Look for recorded screenshots in the
  repo (visual-test baselines such as `__screenshots__/`, docs images); crop
  to the part that matters and let a click enlarge it. A screen the plan adds
  and nobody has recorded yet is drawn as a mock with the spec's approved
  texts, and labelled as drawn.
- A footer naming the spec as the source of truth.

Leave out decision lists, build order, tests and proof, release steps and
risks — the user reads those in the files. A small plan gets fewer flows,
never padding.

## How each drawing works

- Three to six boxes, plain words, labelled arrows, one short sentence under
  the drawing. Someone outside engineering must follow it.
- Real numbers only: the spec's own examples and verbatim user-facing texts
  (pushes, refusals, labels). Never invent a figure.
- Name things the way the product does. When the product's name differs from
  the spec's (a renamed switch, a feature called something else in the app),
  use the product's and say so under the drawing.
- Motion helps the eye follow the flow — dots travelling along arrows, steps
  lighting up in order, a bar filling — and never carries meaning alone. The
  page is complete at rest and honours reduced motion.

## Build

Copy `${CLAUDE_SKILL_DIR}/template.html` and `build.py` into the page's
folder and write the content into the copy; the template carries the look
(a pastel take on the ai-skills banner: indigo night, periwinkle, lavender,
Inter and JetBrains Mono), the components (hero toggle, flow cards, drawing
classes, notification card, phone frame with click-to-enlarge) and their
scripts. Put cropped screens in `crops/` and reference them as
`{{img:<name>}}`; `python3 build.py` inlines them into `index.html` and writes
`preview.html` for a local look.

The folder is `<plan>-view` where the user's own instructions keep
artifacts, so a later run finds it and its link; with none,
`<root>/docs/plans/<plan>/view/` — already outside git.

## Check, publish, report

Look at `preview.html` once through a local server, at desktop and phone
width: every label inside its box, nothing overlapping, no sideways scroll on
the page. Fix what you see, then publish — as a private Artifact where the
host has one (record its link in `<folder>/link.txt` and republish to that
link on later runs), else hand over the path of `preview.html`.

Report the link, what each drawing shows in a line, and anything drawing the
plan exposed: a flow the spec never decides, two decisions that disagree, a
name the product spells differently. Those are questions for the user and
for prepare-plan, not fixes to make here.
