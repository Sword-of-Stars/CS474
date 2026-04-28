Turing Machine Explainer Interface

CLI wrapper to generate a step‑by‑step Turing Machine explainer as PDF using the project’s LaTeX templates and solution pipeline.

Usage

- Help: `python interfaces/tm_explainer/main.py --help`
- Preset example: `python interfaces/tm_explainer/main.py --preset`
- From JSON: `python interfaces/tm_explainer/main.py --from-file interfaces/presets/tm_sample.json`
- Output tex path: `--out phase3/turing_machines/out/tm_steps.tex`
- LaTeX only: `--latex-only`

Notes

- Uses `phase3/turing_machines/main.py`, `templates/format.tex`, `introduction.tex`, `body.tex`, `conclusion.tex`, and `solution.py`.

