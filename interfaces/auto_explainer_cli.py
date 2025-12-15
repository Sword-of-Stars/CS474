import argparse
import json
import os
import sys
from typing import Any, Dict, List, Set, Tuple

# Ensure repository root is importable when running from interfaces/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _load_json(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============== DFA Minimization ===============
def dfa_min_from_json(obj: Dict[str, Any]):
    from automata.fa.dfa import DFA
    return DFA(
        states=set(str(s) for s in obj["states"]),
        input_symbols=set(obj["input_symbols"]),
        transitions={str(s): {a: str(t) for a, t in obj["transitions"][str(s)].items()} for s in obj["states"]},
        initial_state=str(obj["initial_state"]),
        final_states=set(str(s) for s in obj["final_states"]) 
    )


def handle_dfa_min(args: argparse.Namespace):
    from phase1.dfa_minimization.automate_pdfs import DFAGenerator, process_single_dfa
    from automata.fa.dfa import DFA
    import random

    os.makedirs(args.out_dir, exist_ok=True)

    if args.from_file:
        dfa = dfa_min_from_json(_load_json(args.from_file))
    elif args.preset:
        # Simple preset DFA with a few states
        from automata.fa.dfa import DFA
        dfa = DFA(
            states={"1", "2", "3"},
            input_symbols={"a", "b"},
            transitions={
                "1": {"a": "2", "b": "1"},
                "2": {"a": "3", "b": "1"},
                "3": {"a": "3", "b": "2"},
            },
            initial_state="1",
            final_states={"3"},
        )
    elif args.random:
        gen = DFAGenerator(seed=args.seed)
        dfa = gen.generate_random_dfa(num_states=args.num_states, num_symbols=args.num_symbols)
    else:
        # Minimal interactive builder
        print("Interactive DFA builder (states as strings; symbols like a,b)")
        states = input("Enter states (comma-separated): ").strip().split(',')
        symbols = input("Enter input symbols (comma-separated): ").strip().split(',')
        initial = input("Enter initial state: ").strip()
        finals = input("Enter final states (comma-separated): ").strip().split(',')
        transitions: Dict[str, Dict[str, str]] = {}
        for s in states:
            s = s.strip()
            transitions[s] = {}
            for a in symbols:
                a = a.strip()
                t = input(f"δ({s},{a}) = ").strip()
                transitions[s][a] = t
        dfa = DFA(
            states=set(states),
            input_symbols=set(symbols),
            transitions=transitions,
            initial_state=initial,
            final_states=set(finals)
        )

    # Determine example id
    if args.example_id is not None:
        ex_id = args.example_id
    else:
        # find next available number
        existing = [d for d in os.listdir(args.out_dir) if d.startswith("example_")]
        nums = []
        for e in existing:
            try:
                nums.append(int(e.split("_")[-1]))
            except Exception:
                pass
        ex_id = (max(nums) + 1) if nums else 1

    if getattr(args, 'latex_only', False):
        print("[info] --latex-only is not supported for dfa-min; generating PDF instead.")
    ok = process_single_dfa(dfa, ex_id, base_dir=args.out_dir)
    if ok:
        pdf_path = os.path.join(args.out_dir, f"example_{ex_id:04d}", f"example_{ex_id:04d}.pdf")
        print(f"Generated: {pdf_path}")
    else:
        sys.exit(1)


# =============== NFA ε-removal ===============
def nfa_from_json(obj: Dict[str, Any]):
    from automata.fa.nfa import NFA
    # Allow numeric states or strings
    def norm_state(x):
        return x if isinstance(x, (int, float)) else (int(x) if str(x).isdigit() else x)

    states = set(norm_state(s) for s in obj["states"])
    input_symbols = set(obj["input_symbols"])
    transitions: Dict[Any, Dict[str, Set[Any]]] = {}
    for s, trans in obj["transitions"].items():
        ss = norm_state(s)
        transitions[ss] = {}
        for sym, to_list in trans.items():
            transitions[ss][sym] = set(norm_state(t) for t in to_list)
    initial_state = norm_state(obj["initial_state"])
    final_states = set(norm_state(s) for s in obj["final_states"])
    return NFA(states=states, input_symbols=input_symbols, transitions=transitions,
               initial_state=initial_state, final_states=final_states)


def _preset_nfa():
    from automata.fa.nfa import NFA
    return NFA(
        states={1, 2, 3, 4, 5},
        input_symbols={"a", "b"},
        transitions={
            1: {"a": {2}, "": {3}},
            2: {"a": {3, 4}, "b": {2}},
            3: {"a": {5}, "b": {1, 2, 5}},
            4: {"b": {3, 5}, "": {3}},
            5: {}
        },
        initial_state=1,
        final_states={5},
    )


def handle_nfa_eps(args: argparse.Namespace):
    from phase1.part_a.solution import create_latex_solution
    from phase1.nfa_to_dfa_conversion import partc
    import shutil

    nfa = _preset_nfa() if args.preset else nfa_from_json(_load_json(args.from_file))

    # Ensure figures dir exists and set for partc
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # The LaTeX template e_removal.tex references figures under
    # phase1/part_c/out/figures, so ensure we render there.
    figures_dir = os.path.join(repo_root, "phase1", "part_c", "out", "figures")
    os.makedirs(figures_dir, exist_ok=True)
    partc.OUT_PATH = figures_dir

    # Draw original NFA diagram used by the template
    nfa.show_diagram(layout_method="circo", path=os.path.join(figures_dir, "original.png"))

    data = partc.remove_e_transitions_from_NFA(nfa)

    out_tex = args.out or os.path.join(repo_root, "phase1", "nfa_to_dfa_conversion", "out", "e_removal.tex")
    os.makedirs(os.path.dirname(out_tex), exist_ok=True)

    # Mirror figures to the LaTeX output folder under a simple `figures/` directory
    # so the template can find them relative to the generated .tex file.
    out_dir = os.path.dirname(out_tex)
    target_fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(target_fig_dir, exist_ok=True)
    for name in os.listdir(figures_dir):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
            src = os.path.join(figures_dir, name)
            dst = os.path.join(target_fig_dir, name)
            try:
                shutil.copyfile(src, dst)
            except Exception:
                pass
    templates = os.path.join(repo_root, "phase1", "nfa_to_dfa_conversion", "templates")
    sol = create_latex_solution(format_path=templates, outfile=out_tex)
    sol.add_dynamic_content("e_removal.tex", data)
    if getattr(args, 'latex_only', False):
        sol.generate_latex()
        print(f"Generated LaTeX: {out_tex}")
    else:
        sol.generate_pdf()
        print(f"Generated: {os.path.splitext(out_tex)[0]}.pdf")


# =============== CNF converter (wrapper) ===============
# We reuse core logic similar to phase2/chomsky_converter/main.py without importing it
def cnf_transform_grammar(grammar: Dict[str, List[str]]) -> Dict[str, List[str]]:
    transformed: Dict[str, List[str]] = {}
    for variable, rules in grammar.items():
        transformed_rules: List[str] = []
        for rule in rules:
            tr = ""
            i = 0
            while i < len(rule):
                if (i + 3 < len(rule) and rule[i] == '[' and rule[i+3] == ']'):
                    tr += rule[i+1] + '_' + rule[i+2]
                    i += 4
                else:
                    tr += rule[i]
                    i += 1
            transformed_rules.append(tr)
        transformed[variable] = transformed_rules
    return transformed


def cnf_analyze_nullable_rules(grammar: Dict[str, List[str]], nullable_vars: List[str]):
    import itertools
    analysis = []
    for variable, rules in grammar.items():
        for rule in rules:
            if rule == 'e':
                continue
            nullable_in_rule = []
            positions = []
            for i, ch in enumerate(rule):
                if ch in nullable_vars:
                    nullable_in_rule.append(ch)
                    positions.append(i)
            if nullable_in_rule:
                new_rules = []
                for r in range(1, len(positions)+1):
                    for combo in itertools.combinations(range(len(positions)), r):
                        new_rule = list(rule)
                        for idx in sorted(combo, reverse=True):
                            new_rule[positions[idx]] = ''
                        result = ''.join(new_rule)
                        if result and result != rule:
                            new_rules.append({'rule': result, 'removed': [nullable_in_rule[i] for i in combo]})
                analysis.append({
                    'variable': variable,
                    'original_rule': rule,
                    'nullable_vars': nullable_in_rule,
                    'positions': positions,
                    'new_rules': new_rules,
                    'has_nullable': True
                })
    return analysis


def cnf_visualize_unit_rule_graph(edges: List[Tuple[str, str]], grammar: Dict[str, List[str]], output_path: str):
    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.DiGraph()
    G.add_edges_from(edges)
    all_vars = set(grammar.keys())
    for var in all_vars:
        if var not in G:
            G.add_node(var)
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    try:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    except Exception:
        pos = nx.spring_layout(G, seed=42)
    nodes_with_outgoing = set([e[0] for e in edges])
    nodes_with_incoming = set([e[1] for e in edges])
    isolated_nodes = all_vars - nodes_with_outgoing - nodes_with_incoming
    nx.draw_networkx_nodes(G, pos, nodelist=list(isolated_nodes), node_color='#E8F4F8', node_size=1800,
                          edgecolors='#2E86AB', linewidths=2, ax=ax)
    if (nodes_with_outgoing | nodes_with_incoming):
        nx.draw_networkx_nodes(G, pos, nodelist=list(nodes_with_outgoing | nodes_with_incoming),
                              node_color='#A7C7E7', node_size=1800,
                              edgecolors='#1B5E88', linewidths=2.5, ax=ax)
    if edges:
        nx.draw_networkx_edges(G, pos, edge_color='#2E86AB', arrows=True, arrowsize=20, arrowstyle='-|>',
                              width=2.5, connectionstyle='arc3,rad=0.1', min_source_margin=15, min_target_margin=15, ax=ax)
    labels = {node: ('$S_0$' if node == 'S_0' else node) for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=14, font_weight='bold', font_family='sans-serif', ax=ax)
    ax.set_title("Unit Rule Dependency Graph", fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    return G


def cnf_compute_unit_rule_closure(grammar, node_graph):
    import networkx as nx
    closure = {}
    for v1 in grammar.keys():
        closure[v1] = {}
        for v2 in grammar.keys():
            if v1 == v2:
                closure[v1][v2] = {'reachable': True, 'distance': 0}
            elif nx.has_path(node_graph, v1, v2):
                path = nx.shortest_path(node_graph, v1, v2)
                closure[v1][v2] = {'reachable': True, 'distance': len(path)-1, 'path': path}
            else:
                closure[v1][v2] = {'reachable': False, 'distance': float('inf')}
    return closure


def cnf_eliminate_unit_rules_with_explanation(grammar, node_graph):
    from copy import deepcopy
    closure = cnf_compute_unit_rule_closure(grammar, node_graph)
    steps = []
    new_grammar = deepcopy(grammar)
    unit_rules_to_remove = {v: [r for r in rules if r in grammar.keys()] for v, rules in grammar.items()}
    for v1 in grammar.keys():
        added = []
        for v2 in grammar.keys():
            if v1 != v2 and closure[v1][v2]['reachable']:
                non_unit = [r for r in grammar[v2] if r not in grammar.keys()]
                if non_unit:
                    steps.append({'from': v1, 'to': v2, 'path': closure[v1][v2].get('path', []),
                                  'distance': closure[v1][v2]['distance'], 'rules_added': non_unit})
                    new_grammar[v1].extend(non_unit)
                    added.extend(non_unit)
        new_grammar[v1] = list(set(new_grammar[v1]))
    for v in new_grammar.keys():
        new_grammar[v] = [r for r in new_grammar[v] if r not in grammar.keys()]
    return new_grammar, steps, unit_rules_to_remove


def handle_cnf(args: argparse.Namespace):
    """Run the original CNF pipeline, then ensure PDF via phase2.solution.Solution.

    - Invokes phase2/chomsky_converter/main.py to build LaTeX.
    - Copies outputs to a custom destination if provided.
    - Compiles the chosen .tex to PDF using phase2/solution.py logic.
    """
    import subprocess, shutil
    from phase2.solution import Solution
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    script = os.path.join(repo_root, 'phase2', 'chomsky_converter', 'main.py')

    # Run the original script which renders templates and builds PDF.
    # Do not raise on non-zero exit so the GUI doesn't crash; we'll copy
    # any generated files and print guidance to check the log.
    run = subprocess.run([sys.executable, script], cwd=repo_root)
    if run.returncode != 0:
        print("Warning: CNF pipeline exited with errors. Check phase2/out/cnf_converter.log for details.")

    # Default produced files
    produced_tex = os.path.join(repo_root, 'phase2', 'out', 'cnf_converter.tex')
    produced_pdf = os.path.join(repo_root, 'phase2', 'out', 'cnf_converter.pdf')

    # If a custom out is provided, copy the generated files there (if exist)
    compile_tex = None
    compile_pdf = None

    if args.out:
        dest_tex = args.out
        dest_pdf = os.path.splitext(dest_tex)[0] + '.pdf'
        os.makedirs(os.path.dirname(dest_tex), exist_ok=True)
        if os.path.exists(produced_tex):
            shutil.copyfile(produced_tex, dest_tex)
        if not getattr(args, 'latex_only', False) and os.path.exists(produced_pdf):
            shutil.copyfile(produced_pdf, dest_pdf)
        # Prefer compiling/certifying the destination .tex if present
        if os.path.exists(dest_tex):
            compile_tex = dest_tex
            compile_pdf = dest_pdf
        # Messaging deferred until after (re)compile
    else:
        if os.path.exists(produced_tex):
            compile_tex = produced_tex
            compile_pdf = produced_pdf
        else:
            print("CNF pipeline produced no output files. See phase2/out/cnf_converter.log for errors.")
            return

    # Compile to PDF using phase2/solution.py code if requested
    if not getattr(args, 'latex_only', False) and compile_tex:
        try:
            templates = os.path.join(repo_root, 'phase2', 'templates')
            sol = Solution(templates, compile_tex)
            # We already have the LaTeX file; avoid regenerating it
            sol.has_generated_latex = True
            sol.generate_pdf()
            if compile_pdf and os.path.exists(compile_pdf):
                print(f"Generated: {compile_pdf}")
            else:
                # Fallback message
                print(f"Generated PDF alongside: {compile_tex}")
        except Exception as e:
            print(f"PDF compilation failed via phase2.solution: {e}")
            print("See the LaTeX log near the .tex file for details.")
    else:
        # LaTeX only
        print(f"Generated LaTeX: {compile_tex}")


# =============== Turing Machine explainer ===============
class TuringMachine:
    def __init__(self, tape_string, blank_symbol, initial_state, accept_state, reject_state, transition_function):
        self.tape = {i: ch for i, ch in enumerate(tape_string)}
        self.blank_symbol = blank_symbol
        self.head = 0
        self.current_state = initial_state
        self.accept_state = accept_state
        self.reject_state = reject_state
        self.transition_function = transition_function

    def step(self):
        sym = self.tape.get(self.head, self.blank_symbol)
        key = (self.current_state, sym)
        if key not in self.transition_function:
            return False
        new_sym, direction, new_state = self.transition_function[key]
        self.tape[self.head] = new_sym
        if direction == 'R':
            self.head += 1
        elif direction == 'L':
            self.head -= 1
        self.current_state = new_state
        return True

    def is_halted(self):
        return self.current_state in {self.accept_state, self.reject_state}


def tm_format_state_latex(state):
    if not isinstance(state, str):
        return str(state)
    if state.startswith('q') and len(state) > 1:
        if state == 'qaccept':
            return 'q_{\text{accept}}'
        elif state == 'qreject':
            return 'q_{\text{reject}}'
        else:
            num = state[1:]
            return f'q_{{{num}}}'
    return state


def tm_create_transition_table(transition_function, blank_symbol='⊔'):
    import pandas as pd
    states = sorted(set(key[0] for key in transition_function.keys()))
    symbols = sorted(set(key[1] for key in transition_function.keys()))
    table_data = []
    for state in states:
        row = {'State': tm_format_state_latex(state)}
        for symbol in symbols:
            key = (state, symbol)
            if key in transition_function:
                write_sym, direction, new_state = transition_function[key]
                formatted_state = tm_format_state_latex(new_state)
                if write_sym == '#':
                    write_sym_display = r'\#'
                elif write_sym == blank_symbol:
                    write_sym_display = r'\sqcup'
                else:
                    write_sym_display = write_sym
                if symbol == '#':
                    symbol_key = r'\#'
                elif symbol == blank_symbol:
                    symbol_key = r'\sqcup'
                else:
                    symbol_key = symbol
                row[symbol_key] = f'({write_sym_display}, {direction}, {formatted_state})'
            else:
                if symbol == '#':
                    symbol_key = r'\#'
                elif symbol == blank_symbol:
                    symbol_key = r'\sqcup'
                else:
                    symbol_key = symbol
                row[symbol_key] = '---'
        table_data.append(row)
    import pandas as pd
    return pd.DataFrame(table_data)


def tm_record_detailed_configurations(tm, max_steps=200):
    configs = []
    details = []
    configs.append((dict(tm.tape), tm.head, tm.current_state))
    details.append({
        "head_position": tm.head,
        "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
        "written_symbol": None,
        "new_state": tm.current_state,
        "current_transition": None
    })
    for _ in range(max_steps):
        if tm.is_halted():
            break
        curr_state = tm.current_state
        curr_head = tm.head
        read_sym = tm.tape.get(curr_head, tm.blank_symbol)
        key = (curr_state, read_sym)
        if key not in tm.transition_function:
            break
        write_sym, direction, next_state = tm.transition_function[key]
        tm.step()
        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": curr_head,
            "read_symbol": read_sym,
            "written_symbol": write_sym,
            "new_state": next_state,
            "current_transition": (curr_state, read_sym, write_sym, direction, next_state),
            "current_state_raw": curr_state
        })
    if not configs or configs[-1][2] not in {tm.accept_state, tm.reject_state}:
        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": tm.head,
            "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
            "written_symbol": None,
            "new_state": tm.current_state,
            "current_transition": None,
            "current_state_raw": tm.current_state
        })
    return configs, details


def tm_plot_all_configs(configs, details, fixed_left, fixed_right, blank_symbol='⊔', out_dir=None):
    import matplotlib.pyplot as plt
    if out_dir is None:
        out_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                               'phase3', 'turing_machines', 'out')
    plots_dir = os.path.join(out_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    saved = []
    for idx, (tape, head, state) in enumerate(configs):
        if idx == 0:
            fig, ax = plt.subplots(figsize=(10, 2))
            for i in range(fixed_left, fixed_right+1):
                sym = tape.get(i, blank_symbol)
                rect = plt.Rectangle((i,0), 1, 1, fill=False, edgecolor='black')
                ax.add_patch(rect)
                ax.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12)
                ax.text(i+0.5, 1.3, str(i), ha='center', va='center', fontsize=8, color='gray')
            ax.annotate("", xy=(head+0.5, 0), xytext=(head+0.5, -0.7), arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
            ax.set_xlim(fixed_left-2, fixed_right+2)
            ax.set_ylim(-1, 2)
            ax.axis('off')
            fig.savefig(os.path.join(plots_dir, f"plot{idx+1}.png"), dpi=150)
            plt.close(fig)
            saved.append(os.path.join(plots_dir, f"plot{idx+1}.png"))
        else:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 4))
            tape_before = configs[idx-1][0]
            tape_after = tape
            head_before = configs[idx-1][1]
            head_after = head
            changed_positions = set()
            if details[idx].get('current_transition'):
                changed_positions.add(details[idx]['head_position'])
            def draw(ax, tdict, hpos, highlight=False):
                for i in range(fixed_left, fixed_right+1):
                    sym = tdict.get(i, blank_symbol)
                    if highlight and i in changed_positions:
                        rect = plt.Rectangle((i,0), 1, 1, fill=True, facecolor='lightgreen', edgecolor='green', linewidth=2)
                    else:
                        rect = plt.Rectangle((i,0), 1, 1, fill=False, edgecolor='black')
                    ax.add_patch(rect)
                    ax.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12)
                ax.annotate("", xy=(hpos+0.5, 0), xytext=(hpos+0.5, -0.7), arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
                ax.set_xlim(fixed_left-2, fixed_right+2)
                ax.set_ylim(-1, 1.5)
                ax.axis('off')
            draw(ax1, tape_before, head_before, highlight=False)
            draw(ax2, tape_after, head_after, highlight=True)
            fig.savefig(os.path.join(plots_dir, f"plot{idx+1}.png"), dpi=150)
            plt.close(fig)
            saved.append(os.path.join(plots_dir, f"plot{idx+1}.png"))
    return saved


def _preset_tm():
    blank = '⊔'
    transition_function = {
        ('q1', '0'): ('x', 'R', 'q2'),
        ('q1', '1'): ('x', 'R', 'q8'),
        ('q1', '#'): ('#', 'R', 'q4'),
        ('q1', 'x'): ('x', 'R', 'q1'),
        ('q2', '0'): ('0', 'R', 'q2'),
        ('q2', '1'): ('1', 'R', 'q2'),
        ('q2', '#'): ('#', 'R', 'q4'),
        ('q8', '0'): ('0', 'R', 'q8'),
        ('q8', '1'): ('1', 'R', 'q8'),
        ('q8', '#'): ('#', 'R', 'q3'),
        ('q4', 'x'): ('x', 'R', 'q4'),
        ('q4', '0'): ('x', 'L', 'q6'),
        ('q4', blank): (blank, 'S', 'qaccept'),
        ('q3', 'x'): ('x', 'R', 'q3'),
        ('q3', '1'): ('x', 'L', 'q6'),
        ('q3', '0'): ('0', 'R', 'qreject'),
        ('q3', blank): (blank, 'S', 'qaccept'),
        ('q5', 'x'): ('x', 'R', 'q5'),
        ('q5', '0'): ('0', 'R', 'q5'),
        ('q5', '1'): ('1', 'R', 'q5'),
        ('q6', '0'): ('0', 'L', 'q6'),
        ('q6', '1'): ('1', 'L', 'q6'),
        ('q6', 'x'): ('x', 'L', 'q6'),
        ('q6', '#'): ('#', 'L', 'q7'),
        ('q7', '0'): ('0', 'L', 'q7'),
        ('q7', '1'): ('1', 'L', 'q7'),
        ('q7', 'x'): ('x', 'R', 'q1'),
    }
    return {
        'tape_string': "0101#0101",
        'blank_symbol': blank,
        'initial_state': 'q1',
        'accept_state': 'qaccept',
        'reject_state': 'qreject',
        'transition_function': transition_function,
    }


def tm_from_json(obj: Dict[str, Any]):
    # Parse transition function from either dict of tuple-keys or nested mapping
    tf = {}
    for k, v in obj["transition_function"].items():
        if isinstance(k, str) and k.startswith('(') and k.endswith(')'):
            # "(q1,0)": ["x","R","q2"]
            inner = k[1:-1]
            parts = inner.split(',')
            state = parts[0].strip()
            sym = parts[1].strip()
        else:
            # {state: {sym: [write,dir,new]}}
            # normalize into tuple form
            raise ValueError("Unsupported TM transition format; use string tuple keys '(state,symbol)'.")
        write, direction, new_state = v
        tf[(state, sym)] = (write, direction, new_state)
    return {
        'tape_string': obj['tape_string'],
        'blank_symbol': obj.get('blank_symbol', '⊔'),
        'initial_state': obj['initial_state'],
        'accept_state': obj['accept_state'],
        'reject_state': obj['reject_state'],
        'transition_function': tf,
    }


def handle_tm(args: argparse.Namespace):
    from phase3.turing_machines.solution import Solution

    spec = _preset_tm() if args.preset else tm_from_json(_load_json(args.from_file))
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(repo_root, "phase3", "turing_machines", "out"), exist_ok=True)
    tm = TuringMachine(
        tape_string=spec['tape_string'],
        blank_symbol=spec['blank_symbol'],
        initial_state=spec['initial_state'],
        accept_state=spec['accept_state'],
        reject_state=spec['reject_state'],
        transition_function=spec['transition_function']
    )
    configs, details = tm_record_detailed_configurations(tm, max_steps=args.max_steps)
    out_tex = args.out or os.path.join(repo_root, "phase3", "turing_machines", "out", "tm_steps.tex")
    out_dir = os.path.dirname(out_tex)
    os.makedirs(os.path.join(out_dir, 'plots'), exist_ok=True)
    figs = tm_plot_all_configs(configs, details,
                               fixed_left=args.left, fixed_right=args.right,
                               blank_symbol=spec['blank_symbol'], out_dir=out_dir)
    transition_table = tm_create_transition_table(spec['transition_function'], blank_symbol=spec['blank_symbol'])
    data = {
        'plots': figs,
        'tf': spec['transition_function'],
        'details': details,
        'transition_table': transition_table,
        'blank': spec['blank_symbol']
    }
    os.makedirs(os.path.dirname(out_tex), exist_ok=True)
    templates = os.path.join(repo_root, "phase3", "turing_machines", "templates")
    sol = Solution(templates, out_tex)
    sol.add_dynamic_content("body.tex", data)
    if getattr(args, 'latex_only', False):
        sol.generate_latex()
        print(f"Generated LaTeX: {out_tex}")
    else:
        sol.generate_latex()
        sol.generate_pdf()
        print(f"Generated: {os.path.splitext(out_tex)[0]}.pdf")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Unified CLI for auto-explainers (DFA, NFA ε-removal, CNF, TM)")
    sub = p.add_subparsers(dest='cmd', required=True)

    # DFA Minimization
    pd = sub.add_parser('dfa-min', help='DFA Minimization explainer')
    pd.add_argument('--from-file', help='Path to DFA JSON input')
    pd.add_argument('--preset', action='store_true', help='Use preset example DFA')
    pd.add_argument('--random', action='store_true', help='Generate a random DFA')
    pd.add_argument('--seed', type=int, default=42, help='Random seed')
    pd.add_argument('--num-states', type=int, default=None, help='Number of states for random DFA')
    pd.add_argument('--num-symbols', type=int, default=2, help='Alphabet size for random DFA')
    pd.add_argument('--out-dir', default='training_data', help='Base output directory')
    pd.add_argument('--example-id', type=int, help='Example id number (padded to 4)')
    pd.add_argument('--latex-only', action='store_true', help='Generate LaTeX only (not supported; will generate PDF)')
    pd.set_defaults(func=handle_dfa_min)

    # NFA ε-removal
    pn = sub.add_parser('nfa-eps', help='NFA ε-removal explainer')
    pn.add_argument('--from-file', help='Path to NFA JSON input')
    pn.add_argument('--preset', action='store_true', help='Use preset example NFA')
    pn.add_argument('--out', help='Custom output tex path (default phase1/nfa_to_dfa_conversion/out/e_removal.tex)')
    pn.add_argument('--latex-only', action='store_true', help='Generate LaTeX only (skip PDF)')
    pn.set_defaults(func=handle_nfa_eps)

    # CNF converter
    pc = sub.add_parser('cnf', help='Chomsky Normal Form converter explainer')
    pc.add_argument('--from-file', help='Path to grammar JSON input')
    pc.add_argument('--preset', action='store_true', help='Use preset example grammar')
    pc.add_argument('--out', help='Custom output tex path (default phase2/out/cnf_converter.tex)')
    pc.add_argument('--latex-only', action='store_true', help='Generate LaTeX only (skip PDF)')
    pc.set_defaults(func=handle_cnf)

    # Turing Machine
    pt = sub.add_parser('tm', help='Turing Machine steps explainer')
    pt.add_argument('--from-file', help='Path to TM JSON input')
    pt.add_argument('--preset', action='store_true', help='Use preset example TM')
    pt.add_argument('--out', help='Custom output tex path (default phase3/turing_machines/out/tm_steps.tex)')
    pt.add_argument('--left', type=int, default=-5, help='Left bound index for plots')
    pt.add_argument('--right', type=int, default=15, help='Right bound index for plots')
    pt.add_argument('--max-steps', type=int, default=500, help='Maximum TM steps to simulate')
    pt.add_argument('--latex-only', action='store_true', help='Generate LaTeX only (skip PDF)')
    pt.set_defaults(func=handle_tm)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    # Basic validation for commands that need input
    if args.cmd in {"nfa-eps", "cnf", "tm"} and not getattr(args, 'preset', False):
        if not getattr(args, 'from_file', None):
            parser.error(f"{args.cmd} requires --from-file or --preset")
    args.func(args)


if __name__ == '__main__':
    main()
