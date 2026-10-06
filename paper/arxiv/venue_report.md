# Paper report: arXiv preprint

## Checks (`check_paper.py --page-limit 7 --regenerate --verify-citations`)

See `checks.md`. Every check passes: no LaTeX errors, no undefined references, every number sourced
(53 macros), every figure has a generating script, regeneration reproduces all 8 generated files
exactly, and 13/13 citations are verified against arXiv and Crossref. Main text ends on page 5.

## Venue rules

arXiv sets no page limit and has no template. This uses `article` at 10 pt with 1-inch margins
(measured `\textwidth` = 469.75 pt, the width all figures are drawn at). No statements are required.

## Open TODOs (need you)

1. Author name(s) and affiliation (`main.tex`).
2. The AI-use statement: say what you reviewed and edited before release (`sections/statements.tex`).

## Things only a human can judge

- Framing: written as a reproducible tutorial study, not a novelty claim. Change the title if you prefer another angle.
- Figure 1 is a hand-drawn TikZ schematic. Polish it if it will be presented.
- The barren-plateau interpretation (50 layers too shallow for 10–12 qubits) is labelled untested.
  A deeper sweep would settle it.
- The noisy-training comparison is reported as confounded. Training with noise at 4×4 would remove the
  confound, but it was far too slow for this machine (~400 s per 64 images per epoch in a test run).
