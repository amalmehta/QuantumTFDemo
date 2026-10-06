PROJECT NAME: demo_with_quantumtf

META-INSTRUCTIONS:

<Read it all before acting. Ask about anything unclear, contradictory or
 underspecified — before starting and mid-build. Ask in the question widget
 (AskUserQuestion): related questions batched, concrete options, your
 recommendation first. Plain text only if the widget isn't available.>

<Don't expand scope. Anything not listed here is a proposal, including changes
 to this file — propose it, don't do it.>

<Prefer doing over describing: run the code, write the files, test it.>

<Always in scope, no proposal needed: when it goes on GitHub, a README that is
 easy to read at a glance — a line on what it is, then clear visuals
 (screenshots, a diagram or a chart), then links. Everything else goes in
 linked files: docs/INSTRUCTIONS.md (setup, run, use),
 docs/SYSTEM-DESIGN.md (see below) and docs/FILE-STRUCTURE.md (what's where). If what you're
 building is an application rather than a script, also a small unobtrusive feedback tab, and a settings
 button or tab (⌘, on the Mac) that gathers its preferences in one place.>

<If what you're building is an application, build it as a Mac app first; the
 website comes after, as its own step.>

<Name things the way a person would say them — "Goal Tracker", not
 goal_tracker — for the app, its windows, titles, files people open, repo
 descriptions and README headings. When you create the GitHub repo, name it
 with no "_" or "-": one word or joined words, e.g. GoalTracker.>

<Always in scope: a system design doc in the codebase, docs/SYSTEM-DESIGN.md,
 kept current as the build changes. Cover the architecture (with a Mermaid
 diagram), each component's job, the main flows, where data lives, the key
 design decisions and their trade-offs, how it's tested, and known limits.>

<Finish by listing every deliverable: path, what it is, how to check it works.>

<Git rules (no Claude attribution, never commit .claude/) are in
 ~/.claude/CLAUDE.md and apply on their own — nothing to repeat here.>

<Keep the changelog at the bottom current.>

CONTEXT:

create a demo with the quantum tensorflow library. run some training experiemtns

DELIVERABLES:

demo & paper

OPEN QUESTIONS / ASSUMPTIONS:

<Agent fills in: what it guessed, what it decided without asking.>

Asked and answered (2026-10-05/06):
- Demo form: Python package of experiment scripts + a Jupyter notebook (not an app, so no Mac app,
  settings or feedback tab).
- Experiments: all four (QNN on 4×4 MNIST 3-vs-6 vs classical, barren plateaus, depolarizing noise,
  hybrid quantum-classical head).
- Paper: arXiv-style LaTeX preprint, ~5 pages, built with Tectonic, every number from results/*.json.
- Git: local repo only, nothing pushed.
- Site (requested 2026-10-06): one static project page in site/, also published as a private
  claude.ai page. Experiments rerun after Docker stopped mid-run.

Decided without asking:
- Runtime: Docker with TFQ 0.7.6 / TF 2.18 is primary. Native macOS works only with TFQ 0.7.2 /
  TF 2.7 (the last macOS wheels, Intel only), after a wheel retag, single-threaded BLAS and conda
  Python 3.9. It's kept as a documented fallback and tested.
- Hybrid shares data and seeds with Experiment 1, so the QNN is trained once.
- Noise: the trained 4×4 QNNs are tested under noise (inference only). Training *with* noise uses
  3×3 images (10 qubits), because parameter-shift through noisy trajectories was ~400 s per 64
  images per epoch at 17 qubits.
- Data: contradictory images are removed before binarising, as in the TFQ tutorial. The first
  version did it after, which kept only 30% of the data and capped accuracy near 0.63.
- Hyperparameters picked from a two-setting sweep on seed 0.
- Scale of the full runs: 3,000 train / 500 test images, 4 epochs, 3 seeds; barren plateaus at 2–12
  qubits and 1–50 layers with 200 random circuits per point; noise p ∈ {0, 0.001, 0.003, 0.01, 0.03}
  with 50 trajectories.
- README, docs/INSTRUCTIONS.md and docs/FILE-STRUCTURE.md written even though nothing goes to
  GitHub yet, so the repo is ready if it does.

Still open (needed for the paper): author name(s) and affiliation.

CHANGELOG:

- 2026-10-05 — created
- 2026-09-15 — added meta-instruction: built-out applications include a small feedback tab
- 2026-09-15 — added meta-instruction: no "Claude" attribution in commits, PRs, or branches
- 2026-09-16 — added meta-instruction: always include a README when adding to GitHub
- 2026-09-16 — changed meta-instruction: ask clarifying questions in the question widget
- 2026-09-17 — added meta-instructions: Claude never a contributor; never commit .claude/
- 2026-09-26 — compressed the meta-instructions and every field prompt; git rules moved to the global instruction file
- 2026-09-27 — added meta-instruction: applications are built as a Mac app first, then a website
- 2026-09-28 — folded inputs, instructions, constraints, deliverables and done criteria into one free-form CONTEXT
- 2026-09-28 — changed meta-instruction: a README on GitHub always includes a visual
- 2026-09-28 — added meta-instruction: name things like a person would, never snake_case
- 2026-09-28 — changed meta-instruction: README leads with visuals; instructions live in a linked guide
- 2026-09-28 — changed meta-instruction: README is visuals and links; details in docs/INSTRUCTIONS.md and docs/FILE-STRUCTURE.md
- 2026-09-29 — changed meta-instruction: GitHub repo names have no "_" or "-"
- 2026-10-02 — added a DELIVERABLES field after CONTEXT
- 2026-10-02 — added meta-instruction: every project has a system design doc at docs/SYSTEM-DESIGN.md
- 2026-10-05 — added meta-instruction: applications include a settings button or tab
- 2026-10-05 — filled in OPEN QUESTIONS / ASSUMPTIONS after the setup questions
- 2026-10-06 — added deliverable: project site (site/), requested by the user
- 2026-10-06 — final full runs done; paper compiled and checked; site republished with full results
