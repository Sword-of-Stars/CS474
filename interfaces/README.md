Interfaces for Auto-Explainers

This folder contains a unified command-line interface to run the auto-explainers with either user-specified inputs (via JSON) or convenience modes (random/preset). Output PDFs are generated using the existing solution pipelines in each phase.

Usage

- Run the CLI:
  - `python interfaces/auto_explainer_cli.py --help`
  - Or open the GUI: `python interfaces/gui.py`

Subcommands

- `dfa-min` — DFA Minimization explainer
  - From JSON: `python interfaces/auto_explainer_cli.py dfa-min --from-file path/to/dfa.json`
  - Random: `python interfaces/auto_explainer_cli.py dfa-min --random --num-states 5 --num-symbols 2`
  - Output goes to `training_data/example_XXXX/example_XXXX.pdf`.

- `nfa-eps` — Remove ε-transitions and explain
  - From JSON: `python interfaces/auto_explainer_cli.py nfa-eps --from-file path/to/nfa.json`
  - Preset example: `python interfaces/auto_explainer_cli.py nfa-eps --preset`
  - Output defaults to `phase1/nfa_to_dfa_conversion/out/e_removal.pdf`. Override with `--out`.

- `cnf` — Chomsky Normal Form converter explainer
  - From JSON: `python interfaces/auto_explainer_cli.py cnf --from-file path/to/grammar.json`
  - Preset example: `python interfaces/auto_explainer_cli.py cnf --preset`
  - Output defaults to `phase2/out/cnf_converter.pdf`. Override with `--out`.

- `tm` — Turing Machine step-by-step explainer
  - From JSON: `python interfaces/auto_explainer_cli.py tm --from-file path/to/tm.json`
  - Preset example: `python interfaces/auto_explainer_cli.py tm --preset`
  - Output defaults to `phase3/turing_machines/out/tm_steps.pdf`. Override with `--out`.

Input JSON Schemas

- DFA (dfa-min):
  {
    "states": ["1","2","3"],
    "input_symbols": ["a","b"],
    "transitions": {"1": {"a":"2","b":"3"}, "2": {"a":"2","b":"1"}, "3": {"a":"3","b":"3"}},
    "initial_state": "1",
    "final_states": ["3"]
  }

- NFA (nfa-eps):
  {
    "states": [1,2,3,4,5],
    "input_symbols": ["a","b"],
    "transitions": {"1": {"a": [2], "": [3]}, "2": {"a": [3,4], "b": [2]}, "3": {"a": [5], "b": [1,2,5]}, "4": {"b": [3,5], "": [3]}, "5": {}},
    "initial_state": 1,
    "final_states": [5]
  }
  - Use empty string "" for ε.

- Grammar (cnf):
  {"S": ["AaB", "b", "S"], "A": ["S", "e", "AB"], "B": ["bbb", "ASA"]}
  - Use "e" for ε.

- Turing Machine (tm):
  {
    "tape_string": "0101#0101",
    "blank_symbol": "⊔",
    "initial_state": "q1",
    "accept_state": "qaccept",
    "reject_state": "qreject",
    "transition_function": {
      "(q1,0)": ["x","R","q2"],
      "(q1,1)": ["x","R","q8"],
      "(q1,#)": ["#","R","q4"],
      "(q1,x)": ["x","R","q1"]
      // ... add the rest
    }
  }
  - Keys are tuples serialized as strings: "(state,symbol)": [write, direction, new_state]

Notes

- These interfaces rely on `pdflatex` and graphing backends present in your environment.
- For CNF, a dependency graph PNG is written to `phase2/chomsky_converter/out/directed_graph.png` and referenced in the PDF.

GUI

- Start with: `python interfaces/gui.py`
- Choose an explainer from the dropdown, pick a mode (preset/from JSON/random where applicable), adjust parameters, and click Run.
- Use “Open Output Folder” to quickly navigate to the latest outputs.
- Click “Show Example JSON” for a ready-to-use input example; “Load Example” fills the file path with a sample under `interfaces/presets/` that you can edit/copy.
- For NFA/CNF/TM, you can set an output folder and filename; the tool writes both the `.tex` and `.pdf` (if enabled) there.

JSON Examples

- Samples are provided in `interfaces/presets/`:
  - DFA: `interfaces/presets/dfa_sample.json`
  - NFA (ε-removal): `interfaces/presets/nfa_eps_sample.json`
  - Grammar (CNF): `interfaces/presets/grammar_sample.json`
  - Turing Machine: `interfaces/presets/tm_sample.json`

Web UI Visual Automata Editor

- Start with: `python interfaces/web_ui.py` (or use the Docker entrypoint used by this repo).
- DFA and NFA tabs now use the visual editor path for UI creation:
  - Add/Delete/Clear states from toolbar buttons
  - Drag states to reposition
  - Set start state and accept states in sidebar
  - Add transitions by dragging on canvas or via manual transition form
  - Edit transition labels (comma-separated symbols; use `ε` for epsilon in NFA mode)
  - Import JSON and re-render graph from the JSON
  - Export preview shows the exact explainer JSON payload

Explainer JSON Contract Used by Visual Editor

- DFA output:
  - `states`, `input_symbols`, `transitions`, `initial_state`, `final_states`
  - `transitions[state][symbol] = target_state`
- NFA output:
  - `states`, `input_symbols`, `transitions`, `initial_state`, `final_states`
  - `transitions[state][symbol] = [target_state, ...]`
  - Use empty string `""` internally for epsilon.
