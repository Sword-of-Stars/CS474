import os
import matplotlib.pyplot as plt
from itertools import combinations
from graphviz import Digraph
from IPython.display import display

from automata.fa.dfa import DFA
from solution import Solution

# Ensure output directory exists
os.makedirs("out/plots", exist_ok=True)

# --- 1. Build the Original DFA with Multiple Finals ---

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
    final_states={"3", "5"}    # now two accept states!
)

# --- 2. Table‑Filling (Indistinguishability) Algorithm + Details ---

def record_indis_details(dfa):
    """
    Runs table‑filling algorithm and returns:
      states: sorted list of states
      tables: list of dicts mapping (p,q)->bool (True=marked)
      details: list of dicts with 'step' and 'description'
    """
    states = sorted(dfa.states)
    pairs  = list(combinations(states, 2))
    finals = set(dfa.final_states)

    # Step 0: mark pairs where exactly one is final
    table = {pair: False for pair in pairs}
    for p, q in pairs:
        if (p in finals) ^ (q in finals):
            table[(p, q)] = True

    tables  = [table.copy()]
    details = [{
        "step": 0,
        "description": (
            "Initially marked pairs where one state is final and the other is non-final: "
            + ", ".join(f"{p},{q}" for (p, q), marked in table.items() if marked)
        )
    }]

    # Refinement iterations
    while True:
        prev  = tables[-1]
        curr  = prev.copy()
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
                "description": "No new pairs marked; algorithm has converged."
            })
            break
        else:
            details.append({
                "step": len(tables)-1,
                "description": "Newly marked pairs: " + ", ".join(f"{p},{q}" for p,q in newly)
            })

    return states, tables, details

# --- 3. Plotting the Indistinguishability Tables ---

def plot_indis_step(states, table, step_idx):
    n = len(states)
    fig, ax = plt.subplots(figsize=(n, n*0.8))
    ax.set_xlim(0, n-1)
    ax.set_ylim(0, n-1)

    # draw upper triangle
    for i in range(1, n):
        for j in range(i):
            x, y = j, n-1-i
            ax.add_patch(plt.Rectangle((x, y), 1, 1, fill=False, edgecolor='black', linewidth=1.5))
            if table[(states[j], states[i])]:
                ax.text(x+0.5, y+0.5, 'X', ha='center', va='center', color='red', fontsize=16, fontweight='bold')

    # labels
    ax.set_xticks([j+0.5 for j in range(n-1)])
    ax.set_xticklabels(states[:-1], fontsize=12)
    ax.xaxis.tick_bottom()
    ax.set_yticks([n-1-i+0.5 for i in range(1,n)])
    ax.set_yticklabels(states[1:], fontsize=12)
    ax.yaxis.tick_left()

    ax.set_title(f"Indistinguishability Table – Step {step_idx+1}", fontsize=18, pad=15)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    plt.tight_layout()

    fn = f"out/plots/indis_step{step_idx+1}.png"
    fig.savefig(fn, dpi=150)
    return fig

def plot_all_indis_steps(states, tables):
    return [plot_indis_step(states, tbl, idx) for idx, tbl in enumerate(tables)]

# --- Run the algorithm and plot ---

indis_states, indis_tables, indis_details = record_indis_details(dfa)
indis_plots = plot_all_indis_steps(indis_states, indis_tables)

# --- 4. Build the Minimized DFA from the final table ---

def get_equivalence_partition(states, final_table):
    parent = {s:s for s in states}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra!=rb:
            parent[rb]=ra

    # union every unmarked pair
    for (p,q), marked in final_table.items():
        if not marked:
            union(p, q)

    # collect blocks
    blocks = {}
    for s in states:
        r = find(s)
        blocks.setdefault(r, set()).add(s)
    return list(blocks.values())

def build_minimized_dfa(dfa, partition):
    block_names = {frozenset(b): "".join(sorted(b)) for b in partition}
    state_to_block = {s:name for blk,name in block_names.items() for s in blk}

    new_states = set(block_names.values())
    new_initial = state_to_block[dfa.initial_state]
    new_finals  = {
        name for blk,name in block_names.items()
        if blk & set(dfa.final_states)  # block intersects any original final
    }

    new_trans = {}
    for blk,name in block_names.items():
        rep = next(iter(blk))
        new_trans[name] = {a: state_to_block[dfa.transitions[rep][a]] for a in dfa.input_symbols}

    return DFA(
        states=new_states,
        input_symbols=set(dfa.input_symbols),
        transitions=new_trans,
        initial_state=new_initial,
        final_states=new_finals
    )

final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
min_dfa = build_minimized_dfa(dfa, final_partition)

# --- 5. Render the Minimized DFA with Graphviz ---

def show_minimized_dfa_graphviz(dfa, filename=None):
    dot = Digraph(format='png')
    dot.attr(rankdir='LR', size='8,5')
    for s in dfa.states:
        if s == dfa.initial_state:
            dot.node(s, shape='circle', style='bold')
        elif s in dfa.final_states:
            dot.node(s, shape='doublecircle', style='filled', fillcolor='lightgrey')
        else:
            dot.node(s, shape='circle')
    for src,trans in dfa.transitions.items():
        for a,tgt in trans.items():
            dot.edge(src, tgt, label=a)
    if filename:
        dot.render(filename, view=True)
    else:
        display(dot)

show_minimized_dfa_graphviz(min_dfa, filename='out/minimized_dfa')

# --- 6. Package for LaTeX ---

data = {
    'indis_plots': indis_plots,
    'tf': dfa.transitions,
    'indis_details': indis_details
}

my_Solution = Solution('templates', 'out/dfa_minimization.tex')
my_Solution.add_dynamic_content('body.tex', data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
