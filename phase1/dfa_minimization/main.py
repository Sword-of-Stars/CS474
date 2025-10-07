# -*- coding: utf-8 -*-
import os
from itertools import combinations
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import pygraphviz as pgv

from automata.fa.dfa import DFA
from solution import Solution

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
os.makedirs("out/plots", exist_ok=True)
os.makedirs("out/plots/pair_steps", exist_ok=True)

# --- Example DFA ---
dfa = DFA(
    states={"1", "2", "3", "4", "5", "6"},
    input_symbols={"a", "b"},
    transitions={
        "1": {"a": "2", "b": "4"},
        "2": {"a": "4", "b": "3"},
        "3": {"a": "3", "b": "3"},
        "4": {"a": "4", "b": "5"},
        "5": {"a": "5", "b": "5"},
        "6": {"a": "6", "b": "5"},
    },
    initial_state="1",
    final_states={"3", "5"},
)

# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def _sorted_states(states: Set[str]) -> List[str]:
    return sorted(states, key=lambda s: (len(s), s))

def _sublabel(i: int) -> str:
    alpha = "abcdefghijklmnopqrstuvwxyz"
    s = ""
    while True:
        s = alpha[i % 26] + s
        i = i // 26 - 1
        if i < 0:
            break
    return s

def get_equivalence_partition(states: List[str],
                              final_table: Dict[Tuple[str, str], bool]) -> List[Set[str]]:
    """Build equivalence classes from unmarked pairs using union-find."""
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

    for (p, q), marked in final_table.items():
        if not marked:
            union(p, q)

    classes: Dict[str, Set[str]] = {}
    for s in states:
        r = find(s)
        classes.setdefault(r, set()).add(s)

    blocks = [set(_sorted_states(block)) for block in classes.values()]
    blocks.sort(key=lambda b: (len(b), list(b)))
    return blocks

# ---------------------------------------------------------------------
# Pygraphviz-based DFA Visualization
# ---------------------------------------------------------------------
def create_dfa_visualization_pygraphviz(dfa: DFA, 
                                       table: Dict[Tuple[str, str], bool] = None,
                                       filename: str = None,
                                       title: str = None) -> Optional[str]:
    """Create DFA visualization using pygraphviz."""
    
    # Create the graph
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='14,10',
        dpi='300',
        fontsize='18',
        fontname='Arial',
        labelloc='top',
        label=title or 'DFA'
    )
    
    # Determine equivalence classes for coloring
    block_colors = ["lightblue", "lightgreen", "lightyellow", "lightpink", 
                   "lightcyan", "lavender", "mistyrose", "honeydew"]
    
    if table:
        blocks = get_equivalence_partition(_sorted_states(dfa.states), table)
        state_to_block = {}
        for i, block in enumerate(blocks):
            for state in block:
                state_to_block[state] = i
    else:
        state_to_block = {}
    
    # Add states
    for state in _sorted_states(dfa.states):
        # Determine base color from equivalence class
        if state in state_to_block:
            base_color = block_colors[state_to_block[state] % len(block_colors)]
        else:
            base_color = "lightgray"
        
        # Determine shape and style
        if state == dfa.initial_state and state in dfa.final_states:
            shape = 'doublecircle'
            style = 'bold,filled'
        elif state == dfa.initial_state:
            shape = 'circle'
            style = 'bold,filled'
        elif state in dfa.final_states:
            shape = 'doublecircle'
            style = 'filled'
        else:
            shape = 'circle'
            style = 'filled'
        
        G.add_node(state, 
                  shape=shape, 
                  style=style,
                  fillcolor=base_color,
                  fontsize='16',
                  fontname='Arial',
                  penwidth='2')
    
    # Add transitions
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            G.add_edge(src, tgt,
                      label=f'  {symbol}  ',
                      fontsize='14',
                      fontname='Arial',
                      penwidth='2')
    
    # Add initial state arrow
    G.add_node('start', shape='point', width='0.3')
    G.add_edge('start', dfa.initial_state, penwidth='3')
    
    if filename:
        G.draw(filename, prog='dot')
        return filename
    else:
        return str(G)

def create_side_by_side_dfa_analysis(dfa: DFA, 
                                    focus_pair: Tuple[str, str],
                                    current_probe: Dict[str, Any],
                                    table: Dict[Tuple[str, str], bool],
                                    step_info: str,
                                    filename: str) -> str:
    """Create side-by-side analysis using pygraphviz."""
    
    # Create main graph with subgraphs
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='TB',
        compound='true',
        size='20,16',
        dpi='300',
        fontsize='20',
        fontname='Arial',
        labelloc='top',
        label=f'DFA Minimization Analysis\\n{step_info}'
    )
    
    # Create analysis table at the top (simplified for pygraphviz compatibility)
    if current_probe:
        p, q = focus_pair
        a = current_probe['a']
        delta_p = current_probe['delta_p']
        delta_q = current_probe['delta_q']
        witness_pair = current_probe['witness_pair']
        witness_status = "MARKED" if current_probe['witness_marked'] else "unmarked"
        
        # Create a simpler text-based analysis summary
        analysis_text = f"Analyzing Pair ({p}, {q})\\nInput: {a}\\n$\\delta$({p},{a}) = {delta_p}\\n$\\delta$({q},{a}) = {delta_q}\\nWitness: ({witness_pair[0]},{witness_pair[1]})\\nStatus: {witness_status}"
        
        G.add_node('analysis_table', 
                  label=analysis_text, 
                  shape='rectangle',
                  style='rounded,filled',
                  fillcolor='lightyellow',
                  fontsize='12',
                  fontname='Arial')
    
    # Create left subgraph - Original DFA state  
    left_subgraph = G.add_subgraph(name='cluster_0')
    left_subgraph.graph_attr.update(
        label='DFA State Space (highlighting analyzed pair)',
        style='rounded', 
        color='blue',
        fontsize='20',
        fontname='Arial',
        penwidth='2'
    )
    
    # Determine equivalence classes for coloring
    block_colors = ["lightblue", "lightgreen", "lightyellow", "lightpink"]
    if table:
        blocks = get_equivalence_partition(_sorted_states(dfa.states), table)
        state_to_block = {}
        for i, block in enumerate(blocks):
            for state in block:
                state_to_block[state] = i
    else:
        state_to_block = {}
    
    # Add states to left subgraph
    for state in _sorted_states(dfa.states):
        # Base color from equivalence class
        if state in state_to_block:
            base_color = block_colors[state_to_block[state] % len(block_colors)]
        else:
            base_color = "lightgray"
        
        # Highlight focus pair
        if focus_pair and state in focus_pair:
            base_color = "yellow"
        
        # Determine shape and style
        if state == dfa.initial_state and state in dfa.final_states:
            shape = 'doublecircle'
            style = 'bold,filled'
        elif state == dfa.initial_state:
            shape = 'circle' 
            style = 'bold,filled'
        elif state in dfa.final_states:
            shape = 'doublecircle'
            style = 'filled'
        else:
            shape = 'circle'
            style = 'filled'
        
        left_subgraph.add_node(f'orig_{state}', 
                              shape=shape,
                              style=style,
                              fillcolor=base_color,
                              penwidth='2')
    
    # Add all transitions to left subgraph
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            left_subgraph.add_edge(f'orig_{src}', f'orig_{tgt}', 
                                  label=f' {symbol} ', penwidth='2')
    
    # Add initial state arrow to left
    left_subgraph.add_node('orig_start', shape='point', width='0.3')
    left_subgraph.add_edge('orig_start', f'orig_{dfa.initial_state}', penwidth='3')
    
    # Create right subgraph - Transition Analysis
    right_subgraph = G.add_subgraph(name='cluster_1')
    right_subgraph.graph_attr.update(
        label="Transition Analysis (probing specific input)", 
        style='rounded', 
        color='red',
        fontsize='20',
        fontname='Arial',
        penwidth='2'
    )
    
    # Add states to right subgraph with special highlighting for probe targets
    for state in _sorted_states(dfa.states):
        base_color = "lightgray"
        
        if focus_pair and state in focus_pair:
            base_color = "orange"  # Source states
        elif current_probe and state in [current_probe.get('delta_p'), current_probe.get('delta_q')]:
            base_color = "lightgreen"  # Target states
        
        # Determine shape and style
        if state == dfa.initial_state and state in dfa.final_states:
            shape = 'doublecircle'
            style = 'bold,filled'
        elif state == dfa.initial_state:
            shape = 'circle'
            style = 'bold,filled'
        elif state in dfa.final_states:
            shape = 'doublecircle'
            style = 'filled'
        else:
            shape = 'circle'
            style = 'filled'
        
        right_subgraph.add_node(f'probe_{state}',
                               shape=shape,
                               style=style,
                               fillcolor=base_color,
                               penwidth='2')
    
    # Add transitions to right subgraph with highlighting for the probe
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            
            # Highlight the specific probe transition
            if (current_probe and 
                focus_pair and src in focus_pair and 
                symbol == current_probe.get('a')):
                right_subgraph.add_edge(f'probe_{src}', f'probe_{tgt}',
                                       label=f' {symbol} ',
                                       color='red',
                                       fontcolor='red',
                                       style='bold',
                                       penwidth='4')
            else:
                right_subgraph.add_edge(f'probe_{src}', f'probe_{tgt}',
                                       label=f' {symbol} ',
                                       penwidth='2')
    
    # Add initial state arrow to right
    right_subgraph.add_node('probe_start', shape='point', width='0.3')
    right_subgraph.add_edge('probe_start', f'probe_{dfa.initial_state}', penwidth='3')
    
    # Render the graph
    G.draw(filename, prog='dot')
    return filename

# ---------------------------------------------------------------------
# Enhanced Table-filling with Cumulative Step 1
# ---------------------------------------------------------------------
def record_indis_details_with_cumulative_step1(dfa: DFA):
    """Enhanced algorithm with cumulative Step 1 approach."""
    states = _sorted_states(dfa.states)
    pairs = [tuple(sorted(p)) for p in combinations(states, 2)]
    finals = set(dfa.final_states)
    total_pairs = len(pairs)

    # Step 0: Initial markings - CUMULATIVE APPROACH
    table: Dict[Tuple[str, str], bool] = {pair: False for pair in pairs}
    initial_reasons = []
    
    print(f"Processing Step 1 - Cumulative initial finality checks...")
    
    # Build cumulative narrative for all initial checks
    finality_analysis = []
    marked_pairs = []
    
    for i, (p, q) in enumerate(pairs):
        is_mismatch = (p in finals) ^ (q in finals)
        
        finality_status_p = "final" if p in finals else "non-final"
        finality_status_q = "final" if q in finals else "non-final"
        
        finality_analysis.append({
            "pair": (p, q),
            "p_final": p in finals,
            "q_final": q in finals,
            "mismatch": is_mismatch,
            "analysis": f"({p}, {q}): {p} is {finality_status_p}, {q} is {finality_status_q}"
        })
        
        if is_mismatch:
            table[(p, q)] = True
            marked_pairs.append((p, q))
            initial_reasons.append({
                "p": p, "q": q,
                "why": f"{p} is {finality_status_p} and {q} is {finality_status_q}."
            })

    tables = [table.copy()]
    cumulative_marked = sum(1 for v in table.values() if v)

    # Create cumulative narrative
    cumulative_narrative = (
        f"We systematically examine all {total_pairs} state pairs to identify those that differ in finality. "
        f"The final states are F = {{{', '.join(sorted(finals))}}}. "
        f"For each pair (p, q), we check whether exactly one of p or q is final. "
    )
    
    if finality_analysis:
        cumulative_narrative += "Our analysis proceeds as follows: "
        for analysis in finality_analysis:
            p, q = analysis["pair"]
            cumulative_narrative += f"{analysis['analysis']}{'→ MARK' if analysis['mismatch'] else ''}; "
        cumulative_narrative = cumulative_narrative.rstrip("; ") + ". "
    
    if marked_pairs:
        cumulative_narrative += (
            f"Therefore, we mark {len(marked_pairs)} pairs as distinguishable: "
            f"{', '.join(f'({p}, {q})' for p, q in marked_pairs)}. "
            f"These receive X marks in our indistinguishability table."
        )
    else:
        cumulative_narrative += "No pairs differ in finality, so no initial markings are made."

    details = [{
        "step": 0,
        "stage": "init",
        "description": "Initial finality-based marking phase (cumulative analysis).",
        "newly": [[p, q] for (p, q), marked in table.items() if marked],
        "reasons": {},
        "initial_reasons": initial_reasons,
        "blocks": get_equivalence_partition(states, table),
        "metrics": {
            "newly_count": len(initial_reasons),
            "cumulative_marked": cumulative_marked,
            "total_pairs": total_pairs,
            "percent_marked": (100.0 * cumulative_marked / max(1, total_pairs))
        },
        "cumulative_narrative": cumulative_narrative,
        "finality_analysis": finality_analysis,
        "final_states_list": sorted(list(finals))
    }]

    # Refinement rounds (unchanged from before)
    step_num = 1
    while True:
        print(f"Processing Step {step_num + 1} - Refinement round...")
        
        prev = tables[-1]
        curr = prev.copy()
        newly: Set[Tuple[str, str]] = set()
        reasons: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        pair_substeps: List[Dict[str, Any]] = []

        for i, (p, q) in enumerate(pairs):
            if curr[(p, q)]:
                # Already marked - just note it
                pair_substeps.append({
                    "idx": i,
                    "label": _sublabel(i),
                    "pair": [p, q],
                    "kind": "refine",
                    "narrative": (f"Pair ( {p}, {q} ) was already marked before this step; "
                                  f"no further probing is needed."),
                    "finality": None,
                    "decision": "already-marked",
                    "probes": []
                })
                continue

            # Probe each symbol
            probes_for_pair = []
            decision = "keep-unmarked"
            narrative = f"Analyze pair ( {p}, {q} ) by probing input symbols."

            for probe_idx, a in enumerate(sorted(dfa.input_symbols)):
                tp = dfa.transitions[p][a]
                tq = dfa.transitions[q][a]
                key = tuple(sorted((tp, tq)))
                witness_is_marked = prev.get(key, False)

                probe_entry = {
                    "a": a,
                    "delta_p": tp,
                    "delta_q": tq,
                    "witness_pair": [key[0], key[1]],
                    "witness_marked": bool(witness_is_marked),
                    "decision": "continue"
                }
                
                # Create side-by-side analysis for this probe
                step_info = f"Step {step_num + 1}.{_sublabel(i)}.{probe_idx+1}: Probing '{a}'"
                visual_path = create_side_by_side_dfa_analysis(
                    dfa,
                    focus_pair=(p, q),
                    current_probe=probe_entry,
                    table=prev,
                    step_info=step_info,
                    filename=f"out/plots/pair_steps/step{step_num + 1}_{_sublabel(i)}_probe{probe_idx+1}.png"
                )
                
                probe_entry["visual_path"] = f"pair_steps/step{step_num + 1}_{_sublabel(i)}_probe{probe_idx+1}.png"
                probe_entry["figure_label"] = f"fig:step{step_num + 1}_{_sublabel(i)}_probe{probe_idx+1}"

                if witness_is_marked:
                    curr[(p, q)] = True
                    newly.add((p, q))
                    probe_entry["decision"] = "mark"
                    probes_for_pair.append(probe_entry)
                    reasons.setdefault((p, q), []).append({
                        "a": a, "tp": tp, "tq": tq, "witness_pair": key
                    })
                    narrative = (f"Found witness on input {a}: $\\delta$({p},{a})={tp}, $\\delta$({q},{a})={tq}. "
                                 f"Since ( {key[0]}, {key[1]} ) is already marked, "
                                 f"we mark ( {p}, {q} ).")
                    decision = "mark"
                    break
                else:
                    probes_for_pair.append(probe_entry)

            if decision != "mark":
                narrative += " No probe led to a marked witness pair; remain unmarked this round."

            pair_substeps.append({
                "idx": i,
                "label": _sublabel(i),
                "pair": [p, q],
                "kind": "refine",
                "narrative": narrative,
                "finality": None,
                "decision": decision,
                "probes": probes_for_pair
            })

        tables.append(curr.copy())
        step_num += 1

        if not newly:
            # Fixed point
            cm = sum(1 for v in curr.values() if v)
            details.append({
                "step": len(tables) - 1,
                "stage": "refine",
                "description": "No new pairs marked; reached a fixed point.",
                "newly": [],
                "reasons": {},
                "initial_reasons": [],
                "blocks": get_equivalence_partition(states, curr),
                "metrics": {
                    "newly_count": 0,
                    "cumulative_marked": cm,
                    "total_pairs": total_pairs,
                    "percent_marked": (100.0 * cm / max(1, total_pairs))
                },
                "pair_substeps": pair_substeps
            })
            break
        else:
            cm = sum(1 for v in curr.values() if v)
            details.append({
                "step": len(tables) - 1,
                "stage": "refine", 
                "description": "Pairs marked this round because their transitions reach marked witnesses.",
                "newly": [list(x) for x in sorted(newly)],
                "reasons": { (p,q): reasons[(p,q)] for (p,q) in sorted(newly) },
                "initial_reasons": [],
                "blocks": get_equivalence_partition(states, curr),
                "metrics": {
                    "newly_count": len(newly),
                    "cumulative_marked": cm,
                    "total_pairs": total_pairs,
                    "percent_marked": (100.0 * cm / max(1, total_pairs))
                },
                "pair_substeps": pair_substeps
            })

    return states, tables, details

# ---------------------------------------------------------------------
# Enhanced Table Plot with Progressive Marking Colors
# ---------------------------------------------------------------------
def plot_indis_step_enhanced(states: List[str],
                           table: Dict[Tuple[str, str], bool],
                           newly_pairs: Set[Tuple[str, str]],
                           step_idx: int) -> str:
    """Create enhanced indistinguishability table plot with progressive marking."""
    n = len(states)
    fig, ax = plt.subplots(figsize=(max(8, n * 1.2), max(6, n)))
    ax.set_xlim(0, n - 1)
    ax.set_ylim(0, n - 1)

    for i in range(1, n):
        for j in range(i):
            x, y = j, n - 1 - i
            pair = tuple(sorted((states[j], states[i])))
            
            ax.add_patch(plt.Rectangle((x, y), 1, 1,
                                       fill=True, facecolor='white',
                                       edgecolor='black', linewidth=1.2))
            
            if table[pair]:
                # Color coding: new marks are bright red, old marks are darker
                if pair in newly_pairs:
                    color = 'red'
                    weight = 'bold'
                    alpha = 1.0
                else:
                    color = 'darkred'
                    weight = 'normal'
                    alpha = 0.6
                    
                ax.text(x + 0.5, y + 0.5, 'X',
                        ha='center', va='center',
                        fontsize=18, fontweight=weight, color=color, alpha=alpha)

    ax.set_xticks([j + 0.5 for j in range(n - 1)])
    ax.set_xticklabels(states[:-1], fontsize=14)
    ax.xaxis.tick_bottom()

    ax.set_yticks([n - 1 - i + 0.5 for i in range(1, n)])
    ax.set_yticklabels(states[1:], fontsize=14)
    ax.yaxis.tick_left()

    ax.set_title(f"Indistinguishability Table – Step {step_idx + 1}", fontsize=20, pad=20)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    
    # Add legend for mark colors
    if step_idx > 0:
        legend_elements = [
            plt.Line2D([0], [0], marker='X', color='red', linestyle='None',
                      markersize=15, label='Newly marked this step', markeredgewidth=2),
            plt.Line2D([0], [0], marker='X', color='darkred', linestyle='None',
                      markersize=15, label='Previously marked', alpha=0.6, markeredgewidth=2)
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()

    filename = f"out/plots/indis_step{step_idx + 1}.png"
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename

# Rest of the visualization functions using pygraphviz...
def create_partition_pygraphviz(dfa: DFA, blocks: List[Set[str]], 
                               filename: str = None, title: str = None) -> str:
    """Create partition visualization using pygraphviz."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='14,10',
        dpi='300',
        fontsize='18',
        fontname='Arial',
        labelloc='top',
        label=title or 'State Partition'
    )
    
    # Colors for blocks
    block_colors = ["lightblue", "lightgreen", "lightyellow", "lightpink", 
                   "lightcyan", "lavender", "mistyrose", "honeydew"]
    
    # Determine which block each state belongs to
    state_to_block = {}
    for i, block in enumerate(blocks):
        for state in block:
            state_to_block[state] = i
    
    # Add states
    for state in _sorted_states(dfa.states):
        color = block_colors[state_to_block.get(state, 0) % len(block_colors)]
        
        # Determine shape and style
        if state == dfa.initial_state and state in dfa.final_states:
            shape = 'doublecircle'
            style = 'bold,filled'
        elif state == dfa.initial_state:
            shape = 'circle'
            style = 'bold,filled'
        elif state in dfa.final_states:
            shape = 'doublecircle'
            style = 'filled'
        else:
            shape = 'circle'
            style = 'filled'
        
        G.add_node(state,
                  shape=shape,
                  style=style,
                  fillcolor=color,
                  fontsize='16',
                  fontname='Arial',
                  penwidth='2')
    
    # Add transitions
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            G.add_edge(src, tgt,
                      label=f'  {symbol}  ',
                      fontsize='14',
                      fontname='Arial',
                      penwidth='2')
    
    # Add initial state arrow
    G.add_node('start', shape='point', width='0.3')
    G.add_edge('start', dfa.initial_state, penwidth='3')
    
    if filename:
        G.draw(filename, prog='dot')
        return filename
    else:
        return str(G)

def build_minimized_dfa(dfa: DFA, partition: List[Set[str]]):
    """Build minimized DFA from equivalence partition."""
    block_names = {frozenset(b): "".join(_sorted_states(b)) for b in partition}
    state_to_block = {s: name for blk, name in block_names.items() for s in blk}
    new_states = set(block_names.values())
    new_initial = state_to_block[dfa.initial_state]
    new_finals = {name for blk, name in block_names.items()
                  if set(dfa.final_states) & set(blk)}
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

def create_minimized_dfa_pygraphviz(dfa: DFA, filename: str = None) -> str:
    """Create minimized DFA visualization using pygraphviz."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='12,8',
        dpi='300',
        fontsize='20',
        fontname='Arial',
        labelloc='top',
        label='Minimized DFA'
    )
    
    # Add states
    for state in _sorted_states(dfa.states):
        # Determine color and shape
        if state == dfa.initial_state:
            color = "lightblue"
        elif state in dfa.final_states:
            color = "lightgreen"
        else:
            color = "lightgray"
        
        if state == dfa.initial_state and state in dfa.final_states:
            shape = 'doublecircle'
            style = 'bold,filled'
        elif state == dfa.initial_state:
            shape = 'circle'
            style = 'bold,filled'
        elif state in dfa.final_states:
            shape = 'doublecircle'
            style = 'filled'
        else:
            shape = 'circle'
            style = 'filled'
        
        G.add_node(state,
                  shape=shape,
                  style=style,
                  fillcolor=color,
                  fontsize='18',
                  fontname='Arial',
                  penwidth='3')
    
    # Add transitions
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            G.add_edge(src, tgt,
                      label=f'  {symbol}  ',
                      fontsize='16',
                      fontname='Arial',
                      penwidth='3')
    
    # Add initial state arrow
    G.add_node('start', shape='point', width='0.3')
    G.add_edge('start', dfa.initial_state, penwidth='4')
    
    if filename:
        G.draw(filename, prog='dot')
        return filename
    else:
        return str(G)

# ---------------------------------------------------------------------
# Main execution with pygraphviz visualizations
# ---------------------------------------------------------------------
def main():
    print("Starting DFA minimization with pygraphviz visualizations...")
    
    # Generate detailed analysis using pygraphviz with cumulative Step 1
    indis_states, indis_tables, indis_details = record_indis_details_with_cumulative_step1(dfa)
    
    # Create table plots (keep matplotlib for these)
    print("Creating indistinguishability table plots...")
    indis_plot_paths = []
    for idx, tbl in enumerate(indis_tables):
        newly = set(map(tuple, indis_details[idx]["newly"])) if indis_details[idx]["newly"] else set()
        path = plot_indis_step_enhanced(indis_states, tbl, newly, idx)
        indis_plot_paths.append(path)
    
    # Create partition timeline using pygraphviz
    print("Creating partition timeline...")
    blocks_plot_paths = []
    for i, tbl in enumerate(indis_tables):
        blocks = get_equivalence_partition(indis_states, tbl)
        title = f"Partition After Step {i+1}"
        filename = f"out/plots/blocks_step{i+1}.png"
        path = create_partition_pygraphviz(dfa, blocks, filename=filename, title=title)
        blocks_plot_paths.append(path)
    
    # Create minimized DFA using pygraphviz
    print("Creating minimized DFA...")
    final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
    min_dfa = build_minimized_dfa(dfa, final_partition)
    final_min_png = create_minimized_dfa_pygraphviz(min_dfa, filename="out/minimized_dfa.png")
    
    # Package data for LaTeX
    print("Preparing data for LaTeX generation...")
    data = {
        "indis_plots": [path.replace("out/plots/", "plots/") for path in indis_plot_paths],
        "blocks_plots": [path.replace("out/plots/", "plots/") for path in blocks_plot_paths],
        "tf": dfa.transitions,
        "indis_details": indis_details,
        "minimized_dfa_png": final_min_png.replace("out/", "") if final_min_png else None
    }
    
    # Generate LaTeX and PDF
    try:
        print("Generating LaTeX document...")
        my_Solution = Solution()
        my_Solution.add_dynamic_content("body.tex", data)
        my_Solution.generate_latex()
        
        print("Generating PDF...")
        my_Solution.generate_pdf()
        
        print("✓ Enhanced DFA minimization visualization complete!")
        
        # Summary statistics
        total_pair_visuals = sum(len(detail.get('pair_substeps', [])) for detail in indis_details)
        total_probe_visuals = sum(
            len(ps.get('probes', [])) for detail in indis_details
            for ps in detail.get('pair_substeps', [])
        )
        
        print(f"Generated cumulative Step 1 analysis")
        print(f"Generated {total_pair_visuals} pair-level analyses for refinement steps")
        print(f"Generated {total_probe_visuals} individual probe visualizations")
        print(f"Check out/plots/pair_steps/ for detailed step-by-step DFA visualizations")
        print(f"Main document: out/dfa_minimization.pdf")
        
    except Exception as e:
        print(f"Error generating LaTeX/PDF: {e}")
        print("Data has been prepared successfully, but document generation failed.")
        return data
    
    return data

if __name__ == "__main__":
    result = main()