import os
import matplotlib.pyplot as plt
from itertools import combinations
from graphviz import Digraph
from IPython.display import display

from automata.fa.dfa import DFA
from solution import Solution

# Ensure output directories exist
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

# --- 2. Partition‑Refinement Minimization Steps ---

def minimize_dfa_steps(dfa):
    partitions = []
    F = set(dfa.final_states)
    Q = set(dfa.states)
    P = []
    if F:   P.append(F)
    if Q-F: P.append(Q-F)
    partitions.append(P)
    changed = True
    while changed:
        newP = []
        for block in P:
            groups = {}
            for s in block:
                key = tuple(
                    next((i for i,b in enumerate(P) if dfa.transitions[s][a] in b), None)
                    for a in dfa.input_symbols
                )
                groups.setdefault(key, set()).add(s)
            newP.extend(groups.values())
        if newP == P:
            changed = False
        else:
            P = newP
            partitions.append(P)
    return partitions

def record_detailed_minimization_steps(dfa):
    steps = minimize_dfa_steps(dfa)
    details = []
    for i, part in enumerate(steps):
        part_str = "; ".join([",".join(sorted(b)) for b in part])
        details.append({
            "step": i,
            "partition": [sorted(b) for b in part],
            "description": f"Step {i+1}: {len(part)} block(s) — {part_str}"
        })
    return steps, details

def plot_minimization_configuration(partition, step):
    fig, ax = plt.subplots(figsize=(10,3))
    x = 0; w=2; sp=0.5
    for block in partition:
        rect = plt.Rectangle((x,0),w,1,facecolor="#e0f7fa",edgecolor="black",lw=2)
        ax.add_patch(rect)
        ax.text(x+w/2,0.5, ",".join(sorted(block)),ha="center",va="center",
                fontsize=12,fontweight="bold")
        x += w+sp
    ax.set_xlim(0,x); ax.set_ylim(0,1)
    ax.axis("off")
    ax.set_title(f"Partition‑Refinement Step {step+1}",fontsize=16,pad=20)
    plt.tight_layout()
    fn = f"out/plots/partition_step{step}.png"
    fig.savefig(fn)
    return fig

def plot_all_minimization_steps(steps):
    figs=[]
    for i,part in enumerate(steps):
        figs.append(plot_minimization_configuration(part,i))
    return figs

# Run partition‑refinement
part_steps, part_details = record_detailed_minimization_steps(dfa)
part_plots = plot_all_minimization_steps(part_steps)


# --- 3. Table‑Filling (Indistinguishability) Steps ---

def generate_indis_steps(dfa):
    states = sorted(dfa.states)
    pairs = list(combinations(states,2))
    table = {p:False for p in pairs}
    finals = set(dfa.final_states)
    # Step 0
    for p,q in pairs:
        if (p in finals) ^ (q in finals):
            table[(p,q)] = True
    steps=[table.copy()]
    # refine
    while True:
        prev=steps[-1]; curr=prev.copy()
        for p,q in pairs:
            if not curr[(p,q)]:
                for a in dfa.input_symbols:
                    tp,tq=dfa.transitions[p][a],dfa.transitions[q][a]
                    key=tuple(sorted((tp,tq)))
                    if prev.get(key,False):
                        curr[(p,q)]=True; break
        if curr==prev: break
        steps.append(curr.copy())
    return states, steps

def plot_indis_step(states, tbl, idx):
    n=len(states)
    fig,ax=plt.subplots(figsize=(n,n*0.8))
    ax.set_xlim(0,n); ax.set_ylim(0,n)
    for i in range(n):
        for j in range(n):
            if j<=i:
                rect=plt.Rectangle((j,n-1-i),1,1,fill=False,edgecolor="black")
                ax.add_patch(rect)
                if j<i and tbl[(states[j],states[i])]:
                    ax.text(j+0.5,n-1-i+0.5,"X",ha="center",va="center",
                            color="red",fontsize=14)
    ax.set_xticks([k+0.5 for k in range(n)]); ax.set_xticklabels(states,rotation=90)
    ax.set_yticks([n-1-k+0.5 for k in range(n)]); ax.set_yticklabels(states)
    ax.set_title(f"Indist. Table Step {idx+1}",fontsize=16)
    ax.axis("off"); plt.tight_layout()
    fn=f"out/plots/indis_step{idx}.png"
    fig.savefig(fn)
    return fig

def plot_all_indis_steps(states, tables):
    return [plot_indis_step(states,tbl,i) for i,tbl in enumerate(tables)]

# Run indistinguishability
indis_states, indis_tables = generate_indis_steps(dfa)
indis_plots = plot_all_indis_steps(indis_states, indis_tables)


# --- 4. Build the Minimized DFA ---

def build_minimized_dfa(dfa, final_partition):
    # final_partition: list of sets
    block_names = {frozenset(b): "".join(sorted(b)) for b in final_partition}
    state_to_block = {s:name for blk,name in block_names.items() for s in blk}
    new_states = set(block_names.values())
    new_initial = state_to_block[dfa.initial_state]
    new_finals = {name for blk,name in block_names.items() if blk & set(dfa.final_states)}
    new_trans={}
    for blk,name in block_names.items():
        rep=next(iter(blk))
        new_trans[name]={a: state_to_block[dfa.transitions[rep][a]]
                          for a in dfa.input_symbols}
    return DFA(
        states=new_states,
        input_symbols=set(dfa.input_symbols),
        transitions=new_trans,
        initial_state=new_initial,
        final_states=new_finals
    )

min_dfa = build_minimized_dfa(dfa, part_steps[-1])

def show_minimized_dfa_graphviz(dfa, filename=None):
    dot=Digraph(format="png"); dot.attr(rankdir="LR",size="8,5")
    for s in dfa.states:
        if s==dfa.initial_state:
            dot.node(s,shape="circle",style="bold")
        elif s in dfa.final_states:
            dot.node(s,shape="doublecircle",style="filled",fillcolor="lightgrey")
        else:
            dot.node(s,shape="circle")
    for src,trans in dfa.transitions.items():
        for a,tgt in trans.items():
            dot.edge(src,tgt,label=a)
    if filename:
        dot.render(filename,view=True)
    else:
        display(dot)

# Render the minimized DFA
show_minimized_dfa_graphviz(min_dfa, filename="out/minimized_dfa")


# --- 5. Package for LaTeX …

data = {
    "plots": part_plots,
    "indis_plots": indis_plots,
    "tf": dfa.transitions,
    "details": part_details
}

my_Solution = Solution("templates", "out/dfa_minimization.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
