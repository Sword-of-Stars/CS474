DFA Minimization Interface

Quick CLI wrapper to run the DFA Minimization auto‑explainer. Produces a PDF with step‑by‑step explanation using the project’s LaTeX templates and solution pipeline.

Usage

- Help: `python interfaces/dfa_minimization/main.py --help`
- Preset example: `python interfaces/dfa_minimization/main.py --preset`
- From JSON: `python interfaces/dfa_minimization/main.py --from-file interfaces/presets/dfa_sample.json`
- Random DFA: `python interfaces/dfa_minimization/main.py --random --num-states 5 --num-symbols 2`
- Output base dir (optional): `--out-dir training_data` and example id via `--example-id 12`.

Notes

- PDF output is generated under the chosen base directory inside an `example_XXXX` folder.
- Uses `phase1/dfa_minimization/automate_pdfs.py` to generate figures and LaTeX and to compile the PDF.

