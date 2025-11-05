Chomsky Normal Form Converter Interface

CLI wrapper to convert a grammar to CNF with an explanatory PDF using the project’s LaTeX templates.

Usage

- Help: `python interfaces/cnf_converter/main.py --help`
- Preset example: `python interfaces/cnf_converter/main.py --preset`
- From JSON: `python interfaces/cnf_converter/main.py --from-file interfaces/presets/grammar_sample.json`
- Set output tex (and pdf): `--out phase2/out/cnf_converter.tex`
- LaTeX only: `--latex-only`

Notes

- Produces a dependency graph PNG at `phase2/chomsky_converter/out/directed_graph.png`.
- Uses `phase2/templates` and `phase2/solution.py` under the hood.

