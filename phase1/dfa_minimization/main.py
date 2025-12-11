import os
from itertools import combinations
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import pygraphviz as pgv

from automata.fa.dfa import DFA
from .solution import Solution

os.makedirs("phase1/dfa_minimization/out/plots", exist_ok=True)
os.makedirs("phase1/dfa_minimization/out/plots/pair_steps", exist_ok=True)

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

def create_dfa_visualization_pygraphviz(dfa: DFA, 
                                       table: Dict[Tuple[str, str], bool] = None,
                                       filename: str = None,
                                       title: str = None) -> Optional[str]:
    """Create clean, modern DFA visualization with dark grid background."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='14,10',
        dpi='300',
        fontsize='20',
        fontname='Arial',
        labelloc='top',
        label=title or '',
        bgcolor='#1a1f2e', 
        pad='0.8',
        nodesep='1.2',
        ranksep='1.5'
    )
    
    block_colors = [
        "#00bcd4",  
        "#26a69a",  
        "#66bb6a",  
        "#29b6f6",  
        "#ab47bc",  
        "#42a5f5",  
        "#26c6da",  
        "#00acc1"   
    ]
    
    if table:
        blocks = get_equivalence_partition(_sorted_states(dfa.states), table)
        state_to_block = {}
        for i, block in enumerate(blocks):
            for state in block:
                state_to_block[state] = i
    else:
        state_to_block = {}
    
    for state in _sorted_states(dfa.states):
        if state in state_to_block:
            node_color = block_colors[state_to_block[state] % len(block_colors)]
        else:
            node_color = "#00bcd4" 
        
        if state in dfa.final_states:
            shape = 'doublecircle'
        else:
            shape = 'circle'
        
        if state == dfa.initial_state:
            style = 'filled'
            penwidth = '3'
            fontcolor = '#ffffff'
        else:
            style = 'filled'
            penwidth = '2.5'
            fontcolor = '#ffffff'
        
        G.add_node(state, 
                  shape=shape, 
                  style=style,
                  fillcolor='#1a1f2e', 
                  color=node_color,
                  fontcolor=fontcolor,
                  fontsize='18',
                  fontname='Arial Bold',
                  penwidth=penwidth,
                  width='0.7',
                  height='0.7')
    
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            
            if src in state_to_block:
                edge_color = block_colors[state_to_block[src] % len(block_colors)]
            else:
                edge_color = "#00bcd4"
            
            G.add_edge(src, tgt,
                      label=f' {symbol} ',
                      fontsize='16',
                      fontname='Arial',
                      fontcolor='#ffffff',
                      color=edge_color,
                      penwidth='2.5',
                      arrowsize='1.0')
    
    G.add_node('start', 
              shape='point', 
              width='0.01',
              height='0.01',
              style='invis')
    
    if dfa.initial_state in state_to_block:
        arrow_color = block_colors[state_to_block[dfa.initial_state] % len(block_colors)]
    else:
        arrow_color = "#00bcd4"
    
    G.add_edge('start', dfa.initial_state, 
              penwidth='3',
              color=arrow_color,
              arrowsize='1.2')
    
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
    """Create side-by-side analysis with clean modern styling."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='TB',
        compound='true',
        size='20,16',
        dpi='300',
        fontsize='20',
        fontname='Arial',
        labelloc='top',
        label='',
        bgcolor='#1a1f2e',
        fontcolor='#ffffff'
    )
    
    block_colors = ["#00bcd4", "#26a69a", "#66bb6a", "#29b6f6"]
    if table:
        blocks = get_equivalence_partition(_sorted_states(dfa.states), table)
        state_to_block = {}
        for i, block in enumerate(blocks):
            for state in block:
                state_to_block[state] = i
    else:
        state_to_block = {}
    
    left_subgraph = G.add_subgraph(name='cluster_0')
    left_subgraph.graph_attr.update(
        label='',
        style='rounded,filled',
        fillcolor='#232938',
        color='#00bcd4',
        fontcolor='#ffffff',
        fontsize='18',
        fontname='Arial',
        penwidth='3'
    )
    
    for state in _sorted_states(dfa.states):
        if state in state_to_block:
            base_color = block_colors[state_to_block[state] % len(block_colors)]
        else:
            base_color = "#00bcd4"
        
        if focus_pair and state in focus_pair:
            base_color = "#ffeb3b" 
        
        if state in dfa.final_states:
            shape = 'doublecircle'
        else:
            shape = 'circle'
        
        if state == dfa.initial_state:
            style = 'filled'
            penwidth = '3'
        else:
            style = 'filled'
            penwidth = '2.5'
        
        left_subgraph.add_node(f'orig_{state}', 
                              label=state,
                              shape=shape,
                              style=style,
                              fillcolor='#1a1f2e',
                              color=base_color,
                              fontcolor='#ffffff',
                              penwidth=penwidth)
    
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            
            if src in state_to_block:
                edge_color = block_colors[state_to_block[src] % len(block_colors)]
            else:
                edge_color = "#00bcd4"
            
            left_subgraph.add_edge(f'orig_{src}', f'orig_{tgt}', 
                                  label=f' {symbol} ',
                                  fontcolor='#ffffff',
                                  color=edge_color,
                                  penwidth='2')
    
    left_subgraph.add_node('orig_start', shape='point', width='0.01', style='invis')
    
    if dfa.initial_state in state_to_block:
        arrow_color = block_colors[state_to_block[dfa.initial_state] % len(block_colors)]
    else:
        arrow_color = "#00bcd4"
    
    left_subgraph.add_edge('orig_start', f'orig_{dfa.initial_state}', 
                          penwidth='3',
                          color=arrow_color)
    
    right_subgraph = G.add_subgraph(name='cluster_1')
    right_subgraph.graph_attr.update(
        label="Transition Analysis (probing specific input)", 
        style='rounded,filled',
        fillcolor='#232938',
        color='#ff5252',
        fontcolor='#ffffff',
        fontsize='18',
        fontname='Arial',
        penwidth='3'
    )
    
    for state in _sorted_states(dfa.states):
        base_color = "#00bcd4"
        
        if focus_pair and state in focus_pair:
            base_color = "#ff9800" 
        elif current_probe and state in [current_probe.get('delta_p'), current_probe.get('delta_q')]:
            base_color = "#66bb6a" 
        
        if state in dfa.final_states:
            shape = 'doublecircle'
        else:
            shape = 'circle'
        
        if state == dfa.initial_state:
            style = 'filled'
            penwidth = '3'
        else:
            style = 'filled'
            penwidth = '2.5'
        
        right_subgraph.add_node(f'probe_{state}',
                               label=state,
                               shape=shape,
                               style=style,
                               fillcolor='#1a1f2e',
                               color=base_color,
                               fontcolor='#ffffff',
                               penwidth=penwidth)
    
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            
            if (current_probe and 
                focus_pair and src in focus_pair and 
                symbol == current_probe.get('a')):
                right_subgraph.add_edge(f'probe_{src}', f'probe_{tgt}',
                                       label=f' {symbol} ',
                                       color='#ff5252',
                                       fontcolor='#ff5252',
                                       style='bold',
                                       penwidth='4')
            else:
                if src in state_to_block:
                    edge_color = block_colors[state_to_block[src] % len(block_colors)]
                else:
                    edge_color = "#00bcd4"
                
                right_subgraph.add_edge(f'probe_{src}', f'probe_{tgt}',
                                       label=f' {symbol} ',
                                       fontcolor='#ffffff',
                                       color=edge_color,
                                       penwidth='2')
    
    right_subgraph.add_node('probe_start', shape='point', width='0.01', style='invis')
    
    if dfa.initial_state in state_to_block:
        arrow_color = block_colors[state_to_block[dfa.initial_state] % len(block_colors)]
    else:
        arrow_color = "#00bcd4"
    
    right_subgraph.add_edge('probe_start', f'probe_{dfa.initial_state}', 
                           penwidth='3',
                           color=arrow_color)
    
    G.draw(filename, prog='dot')
    return filename

def create_partition_pygraphviz(dfa: DFA, blocks: List[Set[str]], 
                               filename: str = None, title: str = None) -> str:
    """Create partition visualization as regular DFA with color-coded equivalence classes."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='14,10',
        dpi='300',
        fontsize='24',
        fontname='Arial Bold',
        labelloc='top',
        labeljust='center',
        label=title or '',
        bgcolor='#1a1f2e',
        fontcolor='#ffffff',
        pad='0.8',
        nodesep='1.2',
        ranksep='1.5'
    )
    
    block_colors = [
        "#00bcd4", 
        "#26a69a", 
        "#66bb6a",
        "#29b6f6", 
        "#ab47bc", 
        "#42a5f5", 
        "#26c6da", 
        "#00acc1"  
    ]
    
    state_to_block = {}
    for i, block in enumerate(blocks):
        for state in block:
            state_to_block[state] = i
    
    for state in _sorted_states(dfa.states):
        block_idx = state_to_block.get(state, 0)
        node_color = block_colors[block_idx % len(block_colors)]
        
        if state in dfa.final_states:
            shape = 'doublecircle'
        else:
            shape = 'circle'
        
        if state == dfa.initial_state:
            style = 'filled'
            penwidth = '4'
        else:
            style = 'filled'
            penwidth = '3'
        
        G.add_node(state,
                  shape=shape,
                  style=style,
                  fillcolor='#1a1f2e',
                  color=node_color,
                  fontcolor='#ffffff',
                  fontsize='20',
                  fontname='Arial Bold',
                  penwidth=penwidth,
                  width='0.8',
                  height='0.8')
    
    for src in _sorted_states(dfa.states):
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            
            src_block = state_to_block.get(src, 0)
            edge_color = block_colors[src_block % len(block_colors)]
            
            G.add_edge(src, tgt,
                      label=f'  {symbol}  ',
                      fontsize='16',
                      fontname='Arial Bold',
                      fontcolor='#ffffff',
                      color=edge_color,
                      penwidth='2.5',
                      arrowsize='1.2')
    
    G.add_node('start', 
              shape='point', 
              width='0.01',
              style='invis')
    
    init_block = state_to_block.get(dfa.initial_state, 0)
    arrow_color = block_colors[init_block % len(block_colors)]
    
    G.add_edge('start', dfa.initial_state, 
              penwidth='4',
              color=arrow_color,
              arrowsize='1.5')
    
    legend_label = "Equivalence Classes:\\n"
    for i, block in enumerate(blocks):
        color_name = ["Cyan", "Teal", "Green", "Light Blue", "Purple", "Blue", "Light Cyan", "Dark Cyan"][i % 8]
        legend_label += f"Class {i+1} ({color_name}): {{ {', '.join(sorted(block))} }}\\n"
    
    G.add_node('legend',
              shape='box',
              style='rounded,filled',
              fillcolor='#232938',
              color='#ffffff',
              fontcolor='#ffffff',
              fontsize='14',
              fontname='Arial',
              label=legend_label,
              penwidth='2')
    
    if filename:
        G.draw(filename, prog='dot')
        return filename
    else:
        return str(G)

def create_minimized_dfa_pygraphviz(dfa: DFA, filename: str = None) -> str:
    """Create minimized DFA visualization with clean modern styling."""
    
    G = pgv.AGraph(directed=True, strict=False)
    G.graph_attr.update(
        rankdir='LR',
        size='12,8',
        dpi='300',
        fontsize='24',
        fontname='Arial Bold',
        labelloc='top',
        label='Minimized DFA',
        bgcolor='#1a1f2e',
        fontcolor='#ffffff',
        pad='0.8',
        nodesep='1.2',
        ranksep='1.5'
    )
    
    colors = ["#00bcd4", "#26a69a", "#66bb6a", "#29b6f6"]
    
    for idx, state in enumerate(_sorted_states(dfa.states)):
        node_color = colors[idx % len(colors)]
        
        if state in dfa.final_states:
            shape = 'doublecircle'
        else:
            shape = 'circle'
        
        if state == dfa.initial_state:
            style = 'filled'
            penwidth = '4'
        else:
            style = 'filled'
            penwidth = '3'
        
        G.add_node(state,
                  shape=shape,
                  style=style,
                  fillcolor='#1a1f2e',
                  color=node_color,
                  fontcolor='#ffffff',
                  fontsize='22',
                  fontname='Arial Bold',
                  penwidth=penwidth,
                  width='0.9',
                  height='0.9')
    
    for idx, src in enumerate(_sorted_states(dfa.states)):
        edge_color = colors[idx % len(colors)]
        
        for symbol in sorted(dfa.input_symbols):
            tgt = dfa.transitions[src][symbol]
            G.add_edge(src, tgt,
                      label=f'  {symbol}  ',
                      fontsize='18',
                      fontname='Arial Bold',
                      fontcolor='#ffffff',
                      color=edge_color,
                      penwidth='3',
                      arrowsize='1.2')
    
    G.add_node('start', shape='point', width='0.01', style='invis')
    G.add_edge('start', dfa.initial_state, 
              penwidth='4',
              color='#00bcd4',
              arrowsize='1.5')
    
    if filename:
        G.draw(filename, prog='dot')
        return filename
    else:
        return str(G)

def record_indis_details_with_cumulative_step1(dfa: DFA):
    """Enhanced algorithm with cumulative Step 1 approach."""
    states = _sorted_states(dfa.states)
    pairs = [tuple(sorted(p)) for p in combinations(states, 2)]
    finals = set(dfa.final_states)
    total_pairs = len(pairs)

    table: Dict[Tuple[str, str], bool] = {pair: False for pair in pairs}
    initial_reasons = []
    
    print(f"Processing Step 1 - Cumulative initial finality checks...")
    
    finality_analysis = []
    marked_pairs = []
    
    for i, (p, q) in enumerate(pairs):
        is_mismatch = (p in finals) ^ (q in finals)
        
        finality_status_p = "final" if p in finals else "non-final"
        finality_status_q = "final" if q in finals else "non-final"
        
        analysis_text = f"({p}, {q}): {p} is {finality_status_p}, {q} is {finality_status_q}"
        
        finality_analysis.append({
            "pair": (p, q),
            "p_final": p in finals,
            "q_final": q in finals,
            "mismatch": is_mismatch,
            "analysis": analysis_text
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

    cumulative_narrative = (
        f"\\textbf{{Initialization Strategy:}} We systematically examine all {total_pairs} state pairs "
        f"to identify those that differ in finality (the base case for distinguishability). "
        f"The final states are $F = \\{{ {', '.join(sorted(finals))} \\}}$. "
    )
    
    if not finals:
        cumulative_narrative += "Since there are no final states, no pairs can be marked initially. "
    elif len(finals) == len(states):
        cumulative_narrative += "Since all states are final, no pairs can be marked initially. "
    else:
        cumulative_narrative += (
            f"For each pair $(p, q)$, we check whether exactly one of $p$ or $q$ is final. "
            f"Such pairs are immediately distinguishable because the empty string $\\varepsilon$ "
            f"is accepted from one state but rejected from the other. "
        )
    
    if marked_pairs:
        cumulative_narrative += (
            f"\\\\[0.3em]\\textbf{{Result:}} We mark {len(marked_pairs)} pairs as distinguishable: "
            f"${', '.join(f'({p}, {q})' for p, q in marked_pairs)}$. "
            f"These receive ``X'' marks in our indistinguishability table."
        )
    else:
        cumulative_narrative += "\\\\[0.3em]\\textbf{Result:} No pairs differ in finality, so no initial markings are made."

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

    step_num = 1
    while True:
        print(f"Processing Step {step_num + 1} - Refinement round...")
        
        prev = tables[-1]
        curr = prev.copy()
        newly: Set[Tuple[str, str]] = set()
        reasons: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        pair_substeps: List[Dict[str, Any]] = []
        
        unmarked_count = sum(1 for v in prev.values() if not v)

        for i, (p, q) in enumerate(pairs):
            if curr[(p, q)]:
                pair_substeps.append({
                    "idx": i,
                    "label": _sublabel(i),
                    "pair": [p, q],
                    "kind": "refine",
                    "narrative": (f"This pair was already marked in a previous iteration, "
                                  f"so no further analysis is needed."),
                    "finality": None,
                    "decision": "already-marked",
                    "probes": []
                })
                continue

            probes_for_pair = []
            decision = "keep-unmarked"
            narrative = (f"This pair is currently unmarked. We test each input symbol to see if "
                        f"$({p}, {q})$ can be distinguished based on where they transition.")

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
                
                step_info = f"Iteration {step_num}, Pair {_sublabel(i)}, Input '{a}'"
                visual_path = create_side_by_side_dfa_analysis(
                    dfa,
                    focus_pair=(p, q),
                    current_probe=probe_entry,
                    table=prev,
                    step_info=step_info,
                    filename=f"phase1/dfa_minimization/out/plots/pair_steps/iter{step_num}_pair{_sublabel(i)}_input{probe_idx+1}.png"
                )
                
                probe_entry["visual_path"] = f"pair_steps/iter{step_num}_pair{_sublabel(i)}_input{probe_idx+1}.png"
                probe_entry["figure_label"] = f"fig:iter{step_num}_pair{_sublabel(i)}_input{probe_idx+1}"

                if witness_is_marked:
                    curr[(p, q)] = True
                    newly.add((p, q))
                    probe_entry["decision"] = "mark"
                    probes_for_pair.append(probe_entry)
                    reasons.setdefault((p, q), []).append({
                        "a": a, "tp": tp, "tq": tq, "witness_pair": key
                    })
                    narrative = (f"On input ${a}$: State ${p}$ transitions to ${tp}$ and state ${q}$ "
                                f"transitions to ${tq}$. The witness pair $({key[0]}, {key[1]})$ "
                                f"is already marked as distinguishable. Therefore, $({p}, {q})$ must "
                                f"also be distinguishable.")
                    decision = "mark"
                    break
                else:
                    probes_for_pair.append(probe_entry)

            if decision != "mark":
                if len(probes_for_pair) > 0:
                    narrative += (f" After checking all {len(probes_for_pair)} input symbols, no probe "
                                f"revealed a marked witness pair. This pair remains unmarked this iteration.")
                else:
                    narrative += " No distinguishing evidence found."

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
            cm = sum(1 for v in curr.values() if v)
            remaining_unmarked = sum(1 for v in curr.values() if not v)
            details.append({
                "step": len(tables) - 1,
                "stage": "refine",
                "description": (f"\\textbf{{Fixed point reached:}} After examining all {unmarked_count} unmarked pairs, "
                               f"no new pairs could be marked. The algorithm terminates. "
                               f"{remaining_unmarked} pairs remain unmarked, indicating they are indistinguishable."),
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
                "description": (f"In this iteration, we examined {unmarked_count} unmarked pairs and found "
                               f"{len(newly)} that could now be marked as distinguishable. "
                               f"Since changes were made, we continue to the next iteration."),
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

    ax.set_title(f"Indistinguishability Table â€” Step {step_idx + 1}", fontsize=20, pad=20)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    
    if step_idx > 0:
        legend_elements = [
            plt.Line2D([0], [0], marker='X', color='red', linestyle='None',
                      markersize=15, label='Newly marked this step', markeredgewidth=2),
            plt.Line2D([0], [0], marker='X', color='darkred', linestyle='None',
                      markersize=15, label='Previously marked', alpha=0.6, markeredgewidth=2)
        ]
        ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()

    filename = f"phase1/dfa_minimization/out/plots/indis_step{step_idx + 1}.png"
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename

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

def main():
    print("Starting DFA minimization with clean modern visualizations...")
    
    print("Creating original DFA visualization...")
    create_dfa_visualization_pygraphviz(dfa, table=None, 
                                       filename="phase1/dfa_minimization/out/plots/original_dfa.png",
                                       title="Original DFA")
    
    indis_states, indis_tables, indis_details = record_indis_details_with_cumulative_step1(dfa)
    
    print("Creating indistinguishability table plots...")
    indis_plot_paths = []
    for idx, tbl in enumerate(indis_tables):
        newly = set(map(tuple, indis_details[idx]["newly"])) if indis_details[idx]["newly"] else set()
        path = plot_indis_step_enhanced(indis_states, tbl, newly, idx)
        indis_plot_paths.append(path)
    
    print("Creating partition timeline...")
    blocks_plot_paths = []
    for i, tbl in enumerate(indis_tables):
        blocks = get_equivalence_partition(indis_states, tbl)
        title = f"Partition After Step {i+1}"
        filename = f"phase1/dfa_minimization/out/plots/blocks_step{i+1}.png"
        path = create_partition_pygraphviz(dfa, blocks, filename=filename, title=title)
        blocks_plot_paths.append(path)
    
    print("Creating minimized DFA...")
    final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
    min_dfa = build_minimized_dfa(dfa, final_partition)
    final_min_png = create_minimized_dfa_pygraphviz(min_dfa, filename="phase1/dfa_minimization/out/minimized_dfa.png")
    
    print("Preparing data for LaTeX generation...")
    data = {
        "indis_plots": [path.replace("phase1/dfa_minimization/out/plots/", "plots/") for path in indis_plot_paths],
        "blocks_plots": [path.replace("phase1/dfa_minimization/out/plots/", "plots/") for path in blocks_plot_paths],
        "tf": dfa.transitions,
        "indis_details": indis_details,
        "minimized_dfa_png": final_min_png.replace("phase1/dfa_minimization/out/", "") if final_min_png else None,
        "original_dfa_png": "plots/original_dfa.png"
    }
    
    try:
        print("Generating LaTeX document...")
        my_Solution = Solution()
        my_Solution.add_dynamic_content("body.tex", data)
        my_Solution.generate_latex()
        
        print("Generating PDF...")
        my_Solution.generate_pdf()
        
        print("âœ“ Clean modern DFA minimization visualization complete!")
        
        total_pair_visuals = sum(len(detail.get('pair_substeps', [])) for detail in indis_details)
        total_probe_visuals = sum(
            len(ps.get('probes', [])) for detail in indis_details
            for ps in detail.get('pair_substeps', [])
        )
        
        print(f"Generated original DFA visualization with dark theme")
        print(f"Generated cumulative Step 1 analysis")
        print(f"Generated {total_pair_visuals} pair-level analyses for refinement steps")
        print(f"Generated {total_probe_visuals} individual probe visualizations")
        print(f"Generated {len(blocks_plot_paths)} partition visualizations with dark theme")
        print(f"Generated minimized DFA with dark theme")
        print(f"Check out/plots/pair_steps/ for detailed step-by-step DFA visualizations")
        print(f"Main document: phase1/dfa_minimization/out/dfa_minimization.pdf")
        
    except Exception as e:
        print(f"Error generating LaTeX/PDF: {e}")
        print("Data has been prepared successfully, but document generation failed.")
        return data
    
    return data

if __name__ == "__main__":
    result = main()
