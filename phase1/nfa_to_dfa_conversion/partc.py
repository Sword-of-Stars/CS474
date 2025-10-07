from automata.fa.nfa import NFA
import sys, os
import graphviz
from typing import Dict, Set, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from part_a.solution import Solution
from part_a.solution import create_latex_solution, create_markdown_solution, create_html_solution
import pandas as pd

OUT_PATH = "phase1/part_c/out/figures"

def make_table(target_fa) -> pd.DataFrame:
    initial_state = target_fa.initial_state
    final_states = target_fa.final_states

    table = {}

    for from_state, to_state, symbol in target_fa.iter_transitions():
        if isinstance(from_state, frozenset):
            from_state_str = str(set(from_state))
        else:
            from_state_str = str(from_state)

        if from_state in final_states:
            from_state_str = "*" + from_state_str
        if from_state == initial_state:
            from_state_str = "→" + from_state_str

        if isinstance(to_state, frozenset):
            to_state_str = str(set(to_state))
        else:
            to_state_str = str(to_state)

        if to_state in final_states:
            to_state_str = "*" + to_state_str

        if symbol == "":
            symbol = "ε"

        from_state_dict = table.setdefault(from_state_str, dict())
        from_state_dict.setdefault(symbol, set()).add(to_state_str)

    for symbol_dict in table.values():
        for symbol in symbol_dict:
            if len(symbol_dict[symbol]) == 1:
                symbol_dict[symbol] = symbol_dict[symbol].pop()

    df = pd.DataFrame.from_dict(table).fillna("∅").T
    return df.reindex(sorted(df.columns), axis=1)

def make_e_closure_table(target_fa) -> pd.DataFrame:
    final_states = target_fa.final_states
    all_states = target_fa.states

    table = {state: {"ε":{state}} for state in all_states}

    for from_state, to_state, symbol in target_fa.iter_transitions():
        if isinstance(from_state, frozenset):
            from_state_str = int(set(from_state))
        else:
            from_state_str = int(from_state)

        if isinstance(to_state, frozenset):
            to_state_str = int(set(to_state))
        else:
            to_state_str = int(to_state)

        if symbol == "":
            symbol = "ε"
            from_state_dict = table.setdefault(from_state_str, dict())
            from_state_dict.setdefault(symbol, set()).add(to_state_str)

    df = pd.DataFrame([(state, set(data['ε'])) for state, data in table.items()], 
                  columns=['State', 'ε-Transitions'])

    return df.sort_values(by='State').reset_index(drop=True)

def get_e_closure(state, table):
    return table.loc[table['State'] == state, 'ε-Transitions'].values[0]

def create_side_by_side_diagram_with_progression(original_nfa: NFA, current_state, 
                                               all_added_transitions: Dict[int, Dict[str, Set]], 
                                               current_step_transitions: Dict[str, Set],
                                               e_closure_table: pd.DataFrame, path: str):
    main_graph = graphviz.Digraph(
        name='comparison',
        format='png',
        graph_attr={
            'rankdir': 'LR', 
            'compound': 'true',
            'size': '24,12', 
            'dpi': '300',   
            'fontsize': '20',
            'fontname': 'Arial',
            'center': 'true', 
            'splines': 'true'
        }
    )
    
    table_html = '''<TABLE BORDER="3" CELLBORDER="2" CELLSPACING="4" CELLPADDING="8" COLOR="black">
    <TR><TD BGCOLOR="lightblue" ALIGN="CENTER"><FONT POINT-SIZE="24"><B>State</B></FONT></TD>
    <TD BGCOLOR="lightblue" ALIGN="CENTER"><FONT POINT-SIZE="24"><B>ε-Closure</B></FONT></TD></TR>'''
    
    for _, row in e_closure_table.iterrows():
        state = row['State']
        closure = sorted(list(row['ε-Transitions']))
        closure_str = '{' + ', '.join(map(str, closure)) + '}'
        
        bg_color = "yellow" if state == current_state else "white"
        table_html += f'''<TR><TD BGCOLOR="{bg_color}" ALIGN="CENTER"><FONT POINT-SIZE="20"><B>{state}</B></FONT></TD>
        <TD BGCOLOR="{bg_color}" ALIGN="CENTER"><FONT POINT-SIZE="20">{closure_str}</FONT></TD></TR>'''
    
    table_html += '</TABLE>'
    
    with main_graph.subgraph(name='cluster_0') as table_panel:
        table_panel.attr(
            label='ε-Closure Table', 
            style='rounded', 
            color='black',
            fontsize='24',
            fontname='Arial Bold',
            penwidth='3',
            labeljust='c'
        )
        table_panel.attr('node', style='', fontname='Arial')
        table_panel.node('epsilon_table', f'<{table_html}>', 
                        shape='box', 
                        style='invisible', 
                        fontname='Arial')
    
    with main_graph.subgraph(name='cluster_1') as left:
        left.attr(
            label='Original NFA M', 
            style='rounded', 
            color='blue', 
            fontsize='24',
            fontname='Arial Bold',
            penwidth='3'
        )
        left.attr('node', shape='circle', fontsize='20', fontname='Arial', width='0.8', height='0.8')
        left.attr('edge', fontsize='18', fontname='Arial', penwidth='2')
        
        for state in original_nfa.states:
            if state == original_nfa.initial_state and state in original_nfa.final_states:
                left.node(f'orig_{state}', str(state), shape='doublecircle', style='bold', penwidth='3')
            elif state == original_nfa.initial_state:
                left.node(f'orig_{state}', str(state), shape='circle', style='bold', penwidth='3')
            elif state in original_nfa.final_states:
                left.node(f'orig_{state}', str(state), shape='doublecircle', penwidth='3')
            else:
                left.node(f'orig_{state}', str(state), shape='circle', penwidth='2')
        
        for from_state, transitions in original_nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    display_symbol = symbol if symbol != "" else "ε"
                    left.edge(f'orig_{from_state}', f'orig_{to_state}', 
                             label=f'  {display_symbol}  ', penwidth='2')
        
        left.node('orig_start', shape='point', width='0.3')
        left.edge('orig_start', f'orig_{original_nfa.initial_state}', penwidth='3')
    
    with main_graph.subgraph(name='cluster_2') as right:
        right.attr(
            label="Updated NFA M' (adding non-ε transitions)", 
            style='rounded', 
            color='red', 
            fontsize='24',
            fontname='Arial Bold',
            penwidth='3'
        )
        right.attr('node', shape='circle', fontsize='20', fontname='Arial', width='0.8', height='0.8')
        right.attr('edge', fontsize='18', fontname='Arial', penwidth='2')
        
        for state in original_nfa.states:
            if state == current_state:
                if state == original_nfa.initial_state and state in original_nfa.final_states:
                    right.node(f'work_{state}', str(state), shape='doublecircle', style='bold,filled', 
                              fillcolor='lightyellow', penwidth='4')
                elif state == original_nfa.initial_state:
                    right.node(f'work_{state}', str(state), shape='circle', style='bold,filled', 
                              fillcolor='lightyellow', penwidth='4')
                elif state in original_nfa.final_states:
                    right.node(f'work_{state}', str(state), shape='doublecircle', style='filled', 
                              fillcolor='lightyellow', penwidth='4')
                else:
                    right.node(f'work_{state}', str(state), shape='circle', style='filled', 
                              fillcolor='lightyellow', penwidth='4')
            else:
                if state == original_nfa.initial_state and state in original_nfa.final_states:
                    right.node(f'work_{state}', str(state), shape='doublecircle', style='bold', penwidth='3')
                elif state == original_nfa.initial_state:
                    right.node(f'work_{state}', str(state), shape='circle', style='bold', penwidth='3')
                elif state in original_nfa.final_states:
                    right.node(f'work_{state}', str(state), shape='doublecircle', penwidth='3')
                else:
                    right.node(f'work_{state}', str(state), shape='circle', penwidth='2')
        
        for from_state, transitions in original_nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    display_symbol = symbol if symbol != "" else "ε"
                    right.edge(f'work_{from_state}', f'work_{to_state}', 
                              label=f'  {display_symbol}  ', penwidth='2')
        
        for processed_state, transitions in all_added_transitions.items():
            if processed_state != current_state: 
                for symbol, to_states in transitions.items():
                    for to_state in to_states:
                        right.edge(
                            f'work_{processed_state}', 
                            f'work_{to_state}', 
                            label=f'  {symbol}  ',
                            color='darkorange',
                            fontcolor='darkorange',
                            style='bold',
                            penwidth='4'
                        )
        
        for symbol, to_states in current_step_transitions.items():
            for to_state in to_states:
                right.edge(
                    f'work_{current_state}', 
                    f'work_{to_state}', 
                    label=f'  {symbol}  ',
                    color='red',
                    fontcolor='red',
                    style='bold',
                    penwidth='5'
                )
        
        right.node('work_start', shape='point', width='0.3')
        right.edge('work_start', f'work_{original_nfa.initial_state}', penwidth='3')
    
    main_graph.render(path.replace('.png', ''), cleanup=True)

def create_final_nfa_without_epsilon(original_nfa: NFA, all_added_transitions: Dict[int, Dict[str, Set]]) -> NFA:
    final_transitions = {}
    for state in original_nfa.states:
        final_transitions[state] = {}
        for symbol in original_nfa.input_symbols:
            final_transitions[state][symbol] = set()
            
            if state in original_nfa.transitions and symbol in original_nfa.transitions[state]:
                final_transitions[state][symbol].update(original_nfa.transitions[state][symbol])
            
            if state in all_added_transitions and symbol in all_added_transitions[state]:
                final_transitions[state][symbol].update(all_added_transitions[state][symbol])
    
    return NFA(
        states=original_nfa.states,
        input_symbols=original_nfa.input_symbols,
        transitions=final_transitions,
        initial_state=original_nfa.initial_state,
        final_states=original_nfa.final_states,
    )

def remove_e_transitions_from_state(state, nfa, table):
    closure = get_e_closure(state, table)

    M = {}
    for char in nfa.input_symbols: 
        M[char] = set()
        for _state in closure:
            # if that transition exists on that state
            if char in nfa.transitions[_state]: 
                # add all transitions 
                M[char] = M[char].union(set(nfa.transitions[_state][char]))

    E = M.copy()
    for char, states in M.items():
        for _state in states:
            E[char] = E[char].union(get_e_closure(_state, table))

    return M, E

def create_side_by_side_diagram(original_nfa: NFA, working_nfa: NFA, current_state, 
                              highlighted_transitions: Dict[str, Set], path: str):
    main_graph = graphviz.Digraph(
        name='comparison',
        format='png',
        graph_attr={'rankdir': 'LR', 'compound': 'true'}
    )
    
    with main_graph.subgraph(name='cluster_0') as left:
        left.attr(label='Original NFA M', style='rounded', color='blue')
        left.attr('node', shape='circle')
        
        for state in original_nfa.states:
            if state == original_nfa.initial_state and state in original_nfa.final_states:
                left.node(f'orig_{state}', str(state), shape='doublecircle', style='bold')
            elif state == original_nfa.initial_state:
                left.node(f'orig_{state}', str(state), shape='circle', style='bold')
            elif state in original_nfa.final_states:
                left.node(f'orig_{state}', str(state), shape='doublecircle')
            else:
                left.node(f'orig_{state}', str(state), shape='circle')
        
        for from_state, transitions in original_nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    display_symbol = symbol if symbol != "" else "ε"
                    left.edge(f'orig_{from_state}', f'orig_{to_state}', label=display_symbol)
        
        left.node('orig_start', shape='point')
        left.edge('orig_start', f'orig_{original_nfa.initial_state}')
    
    with main_graph.subgraph(name='cluster_1') as right:
        right.attr(label="NFA M' (ε-transitions removed)", style='rounded', color='red')
        right.attr('node', shape='circle')
        
        for state in working_nfa.states:
            if state == working_nfa.initial_state and state in working_nfa.final_states:
                right.node(f'work_{state}', str(state), shape='doublecircle', style='bold')
            elif state == working_nfa.initial_state:
                right.node(f'work_{state}', str(state), shape='circle', style='bold')
            elif state in working_nfa.final_states:
                right.node(f'work_{state}', str(state), shape='doublecircle')
            else:
                right.node(f'work_{state}', str(state), shape='circle')
        
        for from_state, transitions in working_nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    should_highlight = (
                        from_state == current_state and 
                        symbol in highlighted_transitions and 
                        to_state in highlighted_transitions[symbol]
                    )
                    
                    display_symbol = symbol if symbol != "" else "ε"
                    
                    if should_highlight:
                        right.edge(
                            f'work_{from_state}', 
                            f'work_{to_state}', 
                            label=display_symbol,
                            color='red',
                            fontcolor='red',
                            style='bold',
                            penwidth='2'
                        )
                    else:
                        right.edge(f'work_{from_state}', f'work_{to_state}', label=display_symbol)
        
        right.node('work_start', shape='point')
        right.edge('work_start', f'work_{working_nfa.initial_state}')
    
    main_graph.render(path.replace('.png', ''), cleanup=True)

def remove_e_transitions_from_NFA(nfa: NFA):
    original_transitions_without_e = {
        state: {x: set() for x in sorted(nfa.input_symbols)}
        for state in nfa.states
    }

    for state, transition in nfa.transitions.items():
        for symbol, states in transition.items():
            if symbol != "":
                original_transitions_without_e[state][symbol] = states

    all_added_transitions = {}
    
    sorted_states = sorted(nfa.states)
    e_closure = make_e_closure_table(nfa)
    partial_closure = {}

    for state in sorted_states:
        M, E = remove_e_transitions_from_state(state, nfa, e_closure)
        partial_closure[state] = M
        
        current_step_transitions = {}
        for symbol in nfa.input_symbols:
            original_targets = original_transitions_without_e[state].get(symbol, set())
            new_targets = E[symbol] - original_targets
            if new_targets: 
                current_step_transitions[symbol] = new_targets
        
        all_added_transitions[state] = current_step_transitions
        
        create_side_by_side_diagram_with_progression(
            nfa, 
            state, 
            all_added_transitions,  
            current_step_transitions,  
            e_closure,  
            f"{OUT_PATH}/step_{state}.png"
        )

    final_nfa = create_final_nfa_without_epsilon(nfa, all_added_transitions)
    
    final_nfa.show_diagram(layout_method="circo", path=f"{OUT_PATH}/final_no_epsilon.png")

    e_closure_dict = {entry['State']: entry['ε-Transitions'] for entry in e_closure.to_dict(orient='records')}
    
    return {
        "final_nfa": final_nfa,
        "transitions": original_transitions_without_e,
        "aggregate_closure": {state: E for state, (M, E) in 
                            [(s, remove_e_transitions_from_state(s, nfa, e_closure)) for s in sorted_states]},
        "e_closure_table": e_closure_dict,
        "partial_closure": partial_closure,
        "empty_set": r'\varnothing',
        "all_added_transitions": all_added_transitions
    }

def merge_frozendicts(*dicts, input_symbols):
    merged = {symbol: frozenset() for symbol in input_symbols}
    for d in dicts:
        for key, value in d.items():
            if key in merged:
                merged[key] = merged[key].union(value)
            else:
                merged[key] = value
    return merged

def create_dfa_table(nfa):
    dfa_table = {}
    working_states = [frozenset([nfa.initial_state])]

    for states in working_states:
        transitions = merge_frozendicts(*[nfa.transitions[state] for state in states],
                                        input_symbols=nfa.input_symbols)
        dfa_table[states] = transitions

        for incremental_subset in transitions.values():
            if incremental_subset not in working_states:
                working_states.append(incremental_subset)

    dfa_table[frozenset()] = {x: frozenset() for x in nfa.input_symbols}
    final_states = {states for states in working_states if states.intersection(nfa.final_states)}

    dfa_table = {' '.join(map(str, sorted(key))) if key else '∅': value for key, value in dfa_table.items()}
    for key, value in dfa_table.items():
        dfa_table[key] = {k: set(v) for k, v in value.items()}

    return dfa_table, final_states

def create_df_for_dfa_table(dfa_table, nfa):
    symbols = sorted(nfa.input_symbols)
    df = pd.DataFrame([(state, *[set(data[symbol]) if data[symbol] != frozenset() else "∅" for symbol in symbols]) 
                       for state, data in dfa_table.items()], 
                  columns=['DFA State', *symbols])
    return df

def incremental_subset_method(nfa):
    dfa_table = {}
    working_states = [frozenset([nfa.initial_state])]

    for states in working_states:
        transitions = merge_frozendicts(*[nfa.transitions[state] for state in states], 
                                        input_symbols=nfa.input_symbols)
        dfa_table[states] = transitions

        for incremental_subset in transitions.values():
            if incremental_subset not in working_states:
                working_states.append(incremental_subset)

    for states in dfa_table:
        for symbol in nfa.input_symbols:
            if symbol not in dfa_table[states]:
                dfa_table[states][symbol] = frozenset()

    final_dfa_table = {states: {symbol: subset for symbol, subset in transitions.items()} 
                       for states, transitions in dfa_table.items()}
    
    dfa_table = create_df_for_dfa_table(final_dfa_table, nfa)
    return dfa_table



if __name__ == "__main__":
    example_nfa = NFA(
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

    os.makedirs(OUT_PATH, exist_ok=True)

    example_nfa.show_diagram(layout_method="circo", path=f"{OUT_PATH}/original.png")
    
    nfa_without_e_transitions = remove_e_transitions_from_NFA(example_nfa)
    
    my_Solution = create_latex_solution()
    my_Solution.add_dynamic_content("e_removal.tex", nfa_without_e_transitions)
    my_Solution.generate_pdf()

    print("\n=== Generating HTML Version ===")
    html_solution = create_html_solution()
    html_solution.add_dynamic_content("e_removal", nfa_without_e_transitions)
    html_solution.generate_content()

    # Markdown to PDF:
    # markdown_solution = create_markdown_solution(figures_dir="out/figures")
    # markdown_solution.add_dynamic_content("e_removal", nfa_without_e_transitions)
    # markdown_solution.generate_pdf()

    # HTML to PDF:
    # html_solution = create_html_solution()
    # html_solution.add_dynamic_content("e_removal", nfa_without_e_transitions)
    # html_solution.generate_pdf()  # Creates PDF via WeasyPrint/wkhtmltopdf


    
    working_nfa = NFA(
        states={1, 2, 3, 4, 5},
        input_symbols={"a", "b"},
        transitions={
            1: {"a": {2}},
            2: {"a": {3, 4}, "b": {2}},
            3: {"a": {5}, "b": {1, 2, 5}},
            4: {"b": {5}},
            5: {}
        },
        initial_state=1,
        final_states={5},
    )

    dfa_result = incremental_subset_method(working_nfa)
    print("DFA Conversion Table:")
    print(dfa_result)