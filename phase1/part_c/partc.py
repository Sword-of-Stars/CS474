from automata.fa.nfa import NFA
import sys, os
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from part_a.solution import Solution
import pandas as pd

OUT_PATH = "phase1/part_c/out/figures"

def make_table(target_fa) -> pd.DataFrame:
    initial_state = target_fa.initial_state
    final_states = target_fa.final_states

    table = {}

    for from_state, to_state, symbol in target_fa.iter_transitions():
        # make string pretty
        if isinstance(from_state, frozenset):
            from_state_str = str(set(from_state))
        else:
            from_state_str = str(from_state)

        if from_state in final_states:
            from_state_str = "*" + from_state_str
        if from_state == initial_state:
            from_state_str = "→" + from_state_str

        # make string pretty
        if isinstance(to_state, frozenset):
            to_state_str = str(set(to_state))
        else:
            to_state_str = str(to_state)

        if to_state in final_states:
            to_state_str = "*" + to_state_str

        # make e pretty
        if symbol == "":
            symbol = "ε"

        from_state_dict = table.setdefault(from_state_str, dict())
        from_state_dict.setdefault(symbol, set()).add(to_state_str)

    # reformat table for singletons
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

    # convert to DF
    df = pd.DataFrame([(state, set(data['ε'])) for state, data in table.items()], 
                  columns=['State', 'ε-Transitions'])

    # sort state
    return df.sort_values(by='State').reset_index(drop=True)

def get_e_closure(state, table):
    return table.loc[table['State'] == state, 'ε-Transitions'].values[0]

def remove_e_transitions_from_state(state, nfa, table):
    closure = get_e_closure(state, table)

    M = {}
    for char in nfa.input_symbols: 
        M[char] = set()
        for _state in closure:
            # if that transition exists on that state
            if char in nfa.transitions[_state]: 
                # add all transitions 
                M[char]  = M[char].union(set(nfa.transitions[_state][char]))

    E = M.copy()
    for char, states in M.items():
        for _state in states:
            E[char] = E[char].union(get_e_closure(_state, table))

    return M, E

def remove_e_transitions_from_NFA(nfa: NFA):

    original_transitions_without_e = {
        state: {x: set() for x in sorted(nfa.input_symbols)}  # Sort input symbols here
        for state in nfa.states
    }

    for state, transition in nfa.transitions.items():
        for symbol, states in transition.items():
            if symbol != "":
                original_transitions_without_e[state][symbol] = states

    aggregate_closure = {state: {} for state in nfa.states}
    sorted_states = sorted(nfa.states)
    e_closure = make_e_closure_table(nfa)
    partial_closure = {}

    for state in sorted_states:
        M, E = remove_e_transitions_from_state(
            state, nfa, e_closure
            )
        aggregate_closure[state] = E
        partial_closure[state] = M

        working_nfa = NFA(
            states=nfa.states,
            input_symbols=nfa.input_symbols,
            transitions=aggregate_closure,
            initial_state=nfa.initial_state,
            final_states=nfa.final_states,
        )

        working_nfa.show_diagram(layout_method="circo", path=f"{OUT_PATH}/step_{state}.png")


    e_closure_dict = {entry['State']: entry['ε-Transitions'] for entry in e_closure.to_dict(orient='records')}

    
    working_nfa.show_diagram(layout_method="circo", path=f"{OUT_PATH}/step_{state}.png")

    return {"final_nfa": working_nfa,
            "transitions": original_transitions_without_e,
            "aggregate_closure": aggregate_closure,
            "e_closure_table": e_closure_dict,
            "partial_closure": partial_closure,
            "empty_set": r'\varnothing'}

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
    # entries of the form {states: {symbols: states}}


    for states in working_states:
        transitions = merge_frozendicts(*[nfa.transitions[state] for state in states],
                                        input=nfa.input_symbols)
        dfa_table[states] = transitions

        for incremental_subset in transitions.values():
            if incremental_subset not in working_states:
                working_states.append(incremental_subset)

    dfa_table[frozenset()] = {x: {} for x in nfa.input_symbols}
    final_states = {states for states in working_states if states.intersection(nfa.final_states)}

    dfa_table = {' '.join(key): value for key, value in dfa_table.items()}
    for key, value in dfa_table.items():
        dfa_table[key] = {k: set(v) for k, v in value.items()}

    return dfa_table, final_states

def create_df_for_dfa_table(dfa_table, nfa):
    symbols = sorted(nfa.input_symbols)
    df = pd.DataFrame([(state, *[set(data[symbol] if data[symbol] != frozenset() else "∅") for symbol in symbols]) 
                       for state, data in dfa_table.items()], 
                  columns=['DFA State', *symbols])
    return df

def incremental_subset_method(nfa):
    dfa_table = {}
    working_states = [frozenset([nfa.initial_state])]
    # entries of the form {states: {symbols: states}}

    for states in working_states:
        transitions = merge_frozendicts(*[nfa.transitions[state] for state in states], 
                                        input_symbols=nfa.input_symbols)
        dfa_table[states] = transitions

        for incremental_subset in transitions.values():
            if incremental_subset not in working_states:
                working_states.append(incremental_subset)

    # ensure all input symbols are in the DFA table
    for states in dfa_table:
        for symbol in working_nfa.input_symbols:
            if symbol not in dfa_table[states]:
                dfa_table[states][symbol] = frozenset()

    # convert frozensets to sets
    dfa_table = {frozenset(key) if len(key) != 1 else key: 
                {k: set(v) if len(v) != 1 else v for k, v in value.items()} 
                for key, value in dfa_table.items()}

    # convert states to strings for the final DFA
    final_dfa_table = {state: {symbol: subset
                            for symbol, subset in transitions.items()} 
                            for state, transitions in dfa_table.items()}
    
    dfa_table = create_df_for_dfa_table(final_dfa_table, nfa)

    return dfa_table

###########################
# Begin Solution Creation #
###########################

# NFA which matches strings beginning with "a", ending with "a", and
# containing no consecutive "b"s
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

example_nfa.show_diagram(layout_method="circo", path=f"{OUT_PATH}/original.png")
nfa_without_e_transitions = remove_e_transitions_from_NFA(example_nfa)

# Once the e-transitions are removed, we can generate a solution

my_Solution = Solution() # our templates for Solution are loaded in by default
my_Solution.add_dynamic_content("e_removal.tex", nfa_without_e_transitions)
my_Solution.generate_pdf()


# Ideally, this would be combined into a single file. However, I'm doing it in parts
# to match the provided NFA->DFA visualizer in the course notes 
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

incremental_subset_method(working_nfa)
