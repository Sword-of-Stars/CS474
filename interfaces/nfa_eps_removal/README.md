NFA ε-Removal Interface

CLI wrapper for removing ε-transitions from an NFA with an explanatory PDF. Uses the project’s LaTeX templates (e_removal.tex) and solution pipeline.

Usage

- Help: `python interfaces/nfa_eps_removal/main.py --help`
- Preset example: `python interfaces/nfa_eps_removal/main.py --preset`
- From JSON: `python interfaces/nfa_eps_removal/main.py --from-file interfaces/presets/nfa_eps_sample.json`
- LaTeX only (no PDF): add `--latex-only`
- Choose output: `--out phase1/nfa_to_dfa_conversion/out/e_removal.tex`

Notes

- Figures are written to `phase1/nfa_to_dfa_conversion/out/figures/`.
- PDF output goes next to the `.tex` path unless `--latex-only` is used.

