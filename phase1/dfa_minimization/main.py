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
    states={"1", "2", "3", "4", "5", "6", "Z"},
    input_symbols={"a", "b"},
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
    final_states={"3", }
)

# --- 2. Table‑Filling (Indistinguishability) Steps + Details ---

def record_indis_details(dfa):
    """
    Runs table‑filling algorithm and returns:
      states: sorted list of states
      tables: list of dicts mapping (p,q)->bool (True=marked)
      details: list of dicts with 'step' and 'description'
    """
    states = sorted(dfa.states)
    pairs = list(combinations(states, 2))
    finals = set(dfa.final_states)

    # Step 0
    table = {pair: False for pair in pairs}
    for p, q in pairs:
        if (p in finals) ^ (q in finals):
            table[(p, q)] = True
    tables = [table.copy()]
    details = [{
        "step": 0,
        "description": (
            "Initially marked pairs where one state is final and the other non‑final: "
            + ", ".join(f"{p},{q}" for (p, q), marked in table.items() if marked)
        )
    }]

    # Refinement
    while True:
        prev = tables[-1]
        curr = prev.copy()
        newly = []
        for p, q in pairs:
            if not curr[(p, q)]:
                for a in dfa.input_symbols:
                    tp = dfa.transitions[p][a]
                    tq = dfa.transitions[q][a]
                    key = tuple(sorted((tp, tq)))
                    if prev.get(key, False):
                        curr[(p, q)] = True
                        newly.append((p, q))
                        break
        tables.append(curr.copy())
        if not newly:
            details.append({
                "step": len(tables)-1,
                "description": "No new pairs marked; table is now stable."
            })
            break
        else:
            details.append({
                "step": len(tables)-1,
                "description": "Newly marked pairs: " + ", ".join(f"{p},{q}" for p,q in newly)
            })

    return states, tables, details

# --- 3. Improved Indistinguishability‑Table Plot ---

# --- 3. Improved Indistinguishability‑Table Plot (1‑based filenames) ---

def plot_indis_step(states, table, step_idx):
    """
    Draws the upper‑triangular indistinguishability table,
    then saves to out/plots/indis_step{step_idx+1}.png
    """
    n = len(states)
    fig, ax = plt.subplots(figsize=(n, n * 0.8))
    ax.set_xlim(0, n-1)
    ax.set_ylim(0, n-1)

    # Draw cells and X marks
    for i in range(1, n):
        for j in range(i):
            x, y = j, n - 1 - i
            ax.add_patch(plt.Rectangle((x, y), 1, 1,
                                       fill=False, edgecolor='black', linewidth=1.5))
            if table[(states[j], states[i])]:
                ax.text(x + 0.5, y + 0.5, 'X',
                        ha='center', va='center',
                        fontsize=16, color='red', fontweight='bold')

    # Column labels on bottom
    ax.set_xticks([j + 0.5 for j in range(n-1)])
    ax.set_xticklabels(states[:-1], fontsize=12)
    ax.xaxis.tick_bottom()

    # Row labels on left
    ax.set_yticks([n - 1 - i + 0.5 for i in range(1, n)])
    ax.set_yticklabels(states[1:], fontsize=12)
    ax.yaxis.tick_left()

    ax.set_title(f"Indistinguishability Table – Step {step_idx+1}",
                 fontsize=18, pad=15)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    plt.tight_layout()

    # **Use 1‑based filename** here:
    filename = f"out/plots/indis_step{step_idx+1}.png"
    fig.savefig(filename, dpi=150)
    return fig

def plot_all_indis_steps(states, tables):
    """
    Calls plot_indis_step for each table in 'tables'
    Returns list of Figure objects.
    """
    figs = []
    for idx, tbl in enumerate(tables):
        figs.append(plot_indis_step(states, tbl, idx))
    return figs

# --- Then later in your main.py ---

# 1) Generate tables + details:
indis_states, indis_tables, indis_details = record_indis_details(dfa)

# 2) Plot each step (now saves indis_step1.png … indis_stepN.png)
indis_plots = plot_all_indis_steps(indis_states, indis_tables)


# --- 4. Build the Minimized DFA from the final indistinguishability table ---

def get_equivalence_partition(states, final_table):
    """
    From the final indistinguishability table, returns a list of equivalence classes.
    Unmarked pairs are equivalent; we build connected components.
    """
    parent = {s: s for s in states}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # Union all unmarked pairs
    for (p, q), marked in final_table.items():
        if not marked:
            union(p, q)

    # Collect classes
    classes = {}
    for s in states:
        r = find(s)
        classes.setdefault(r, set()).add(s)
    return list(classes.values())

def build_minimized_dfa(dfa, partition):
    """
    Constructs a minimized DFA given the equivalence partition (list of sets).
    """
    block_names = {frozenset(b): "".join(sorted(b)) for b in partition}
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

final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
min_dfa = build_minimized_dfa(dfa, final_partition)

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

show_minimized_dfa_graphviz(min_dfa, filename="out/minimized_dfa")

# --- 6. Package for LaTeX ---

data = {
    "indis_plots": indis_plots,
    "tf": dfa.transitions,
    "indis_details": indis_details
}

my_Solution = Solution("templates", "out/dfa_minimization.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
