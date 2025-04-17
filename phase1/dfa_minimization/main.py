import os
import matplotlib.pyplot as plt
from itertools import combinations
from graphviz import Digraph
from IPython.display import display

from automata.fa.dfa import DFA
from solution import Solution

# Ensure output directory exists
os.makedirs("out/plots", exist_ok=True)

# --- 1. Build the Original DFA ---

dfa = DFA(
    states={"1","2","3","4","5","6","Z"},
    input_symbols={"a","b"},
    transitions={
        "1": {"a": "2", "b": "4"},
        "2": {"a": "4", "b": "3"},
        "3": {"a": "3", "b": "3"},
        "4": {"a": "2", "b": "5"},
        "5": {"a": "6", "b": "5"},
        "6": {"a": "4", "b": "Z"},
        "Z": {"a": "Z", "b": "Z"},
    },
    initial_state="1",
    final_states={"3"}
)

# --- 2. Table‑Filling (Indistinguishability) Steps ---

def generate_indis_steps(dfa):
    """
    Table‑filling algorithm:
      - Step 0: mark all (p,q) where one is final and the other is not.
      - Step k>0: mark (p,q) if for some symbol a, (delta(p,a),delta(q,a)) was marked in step k-1.
    Returns:
      states: sorted list of states
      steps: list of dicts mapping (p,q) pairs to bool (True=marked)
    """
    states = sorted(dfa.states)
    pairs = list(combinations(states, 2))
    table = {pair: False for pair in pairs}
    finals = set(dfa.final_states)
    # Step 0
    for p, q in pairs:
        if (p in finals) ^ (q in finals):
            table[(p, q)] = True
    steps = [table.copy()]
    # Refinement
    while True:
        prev = steps[-1]
        curr = prev.copy()
        for p, q in pairs:
            if not curr[(p, q)]:
                for a in dfa.input_symbols:
                    tp = dfa.transitions[p][a]
                    tq = dfa.transitions[q][a]
                    key = tuple(sorted((tp, tq)))
                    if prev.get(key, False):
                        curr[(p, q)] = True
                        break
        if curr == prev:
            break
        steps.append(curr.copy())
    return states, steps

# --- 3. Improved Indistinguishability‑Table Plot ---

def plot_indis_step(states, table, step_idx):
    """
    Draws the upper‑triangular indistinguishability table:
      - Columns labeled by states[0..n-2] at bottom
      - Rows labeled by states[1..n-1] on the left
      - Marked pairs shown as red 'X'
    """
    n = len(states)
    fig, ax = plt.subplots(figsize=(n, n * 0.8))
    ax.set_xlim(0, n-1)
    ax.set_ylim(0, n-1)

    # Draw cells and X marks
    for i in range(1, n):
        for j in range(i):
            x, y = j, n - 1 - i
            rect = plt.Rectangle((x, y), 1, 1,
                                 fill=False, edgecolor='black', linewidth=1.5)
            ax.add_patch(rect)
            if table[(states[j], states[i])]:
                ax.text(x + 0.5, y + 0.5, 'X',
                        ha='center', va='center',
                        fontsize=16, color='red', fontweight='bold')

    # Column labels (bottom)
    ax.set_xticks([j + 0.5 for j in range(n-1)])
    ax.set_xticklabels(states[:-1], fontsize=12)
    ax.xaxis.tick_bottom()

    # Row labels (left)
    ax.set_yticks([n - 1 - i + 0.5 for i in range(1, n)])
    ax.set_yticklabels(states[1:], fontsize=12)
    ax.yaxis.tick_left()

    ax.set_title(f"Indistinguishability Table – Step {step_idx+1}",
                 fontsize=18, pad=15)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    plt.tight_layout()

    fn = f"out/plots/indis_step{step_idx}.png"
    fig.savefig(fn, dpi=150)
    return fig

def plot_all_indis_steps(states, tables):
    return [plot_indis_step(states, tbl, idx) for idx, tbl in enumerate(tables)]

# Run indistinguishability algorithm and plot each step
indis_states, indis_tables = generate_indis_steps(dfa)
indis_plots = plot_all_indis_steps(indis_states, indis_tables)

# --- 4. Build the Minimized DFA ---

def build_minimized_dfa(dfa, final_partition):
    """
    Constructs the minimized DFA from the last partition (list of sets).
    """
    block_names = {frozenset(b): "".join(sorted(b)) for b in final_partition}
    state_to_block = {s: name for blk, name in block_names.items() for s in blk}
    new_states = set(block_names.values())
    new_initial = state_to_block[dfa.initial_state]
    new_finals = {name for blk, name in block_names.items() if blk & set(dfa.final_states)}
    new_transitions = {}
    for blk, name in block_names.items():
        rep = next(iter(blk))
        new_transitions[name] = {
            a: state_to_block[dfa.transitions[rep][a]]
            for a in dfa.input_symbols
        }
    return DFA(
        states=new_states,
        input_symbols=set(dfa.input_symbols),
        transitions=new_transitions,
        initial_state=new_initial,
        final_states=new_finals
    )

# Build minimized DFA using the final partition from generate_indis_steps
# Note: generate_indis_steps gives only marked table; use partition-refinement
# or extract unmarked pairs to form equivalence classes.
# Here for simplicity, assume you have final_partition from a separate routine.
# For example:
# final_partition = [set(c) for c in part_steps[-1]]
# min_dfa = build_minimized_dfa(dfa, final_partition)

# (If you have partition-refinement code removed, supply final_partition manually.)

# --- 5. Render the Minimized DFA with Graphviz ---

def show_minimized_dfa_graphviz(dfa, filename=None):
    dot = Digraph(format="png")
    dot.attr(rankdir="LR", size="8,5")
    for s in dfa.states:
        if s == dfa.initial_state:
            dot.node(s, shape="circle", style="bold")
        elif s in dfa.final_states:
            dot.node(s, shape="doublecircle", style="filled", fillcolor="lightgrey")
        else:
            dot.node(s, shape="circle")
    for src, trans in dfa.transitions.items():
        for a, tgt in trans.items():
            dot.edge(src, tgt, label=a)
    if filename:
        dot.render(filename, view=True)
    else:
        display(dot)

# If you have min_dfa, uncomment to render:
# show_minimized_dfa_graphviz(min_dfa, filename="out/minimized_dfa")

# --- 6. Package for LaTeX ---

data = {
    "indis_plots": indis_plots,
    "tf": dfa.transitions
}

my_Solution = Solution("templates", "out/dfa_minimization.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
