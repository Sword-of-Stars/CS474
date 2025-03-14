def convert_cfg_to_pda(grammar, start_symbol):
    """
    Convert a Context-Free Grammar to a Push-Down Automaton
    
    Parameters:
    grammar (dict): A dictionary mapping variables to lists of production rules
                    Each production rule is a string, and "e" represents the empty string
    start_symbol (str): The start symbol of the grammar
    
    Returns:
    tuple: (states, input_alphabet, stack_alphabet, transitions, start_state, initial_stack, accept_states)
    """
    # Initialize PDA components
    states = {"q0", "qLoop", "qAccept"}
    input_alphabet = set()
    stack_alphabet = set(grammar.keys())  # Variables are stack symbols
    transitions = {
        "q0": {"": {("", "Z"): {("qLoop", f"{start_symbol}Z")}}},  # Initial transition pushes start symbol and Z marker
        "qLoop": {},
        "qAccept": {}
    }
    start_state = "q0"
    initial_stack = ""  # Empty initial stack
    accept_states = {"qAccept"}
    
    # Identify terminal symbols from grammar
    for variable, rules in grammar.items():
        stack_alphabet.add(variable)
        for rule in rules:
            for symbol in rule:
                if symbol != "e":  # Skip empty symbol
                    if symbol.islower() or symbol in "0123456789":  # Terminal symbols
                        input_alphabet.add(symbol)
                    stack_alphabet.add(symbol)
    
    # Add bottom-of-stack marker to stack alphabet
    stack_alphabet.add("Z")
    
    # Process grammar rules
    for variable, rules in grammar.items():
        if "qLoop" not in transitions:
            transitions["qLoop"] = {}
            
        for rule in rules:
            if rule == "e":  # Empty rule
                # Pop the variable, push nothing
                if "" not in transitions["qLoop"]:
                    transitions["qLoop"][""] = {}
                if variable not in transitions["qLoop"][""]:
                    transitions["qLoop"][""][variable] = set()
                transitions["qLoop"][""][variable].add(("qLoop", ""))
            else:
                # Pop the variable, push the rule in reverse
                if "" not in transitions["qLoop"]:
                    transitions["qLoop"][""] = {}
                if variable not in transitions["qLoop"][""]:
                    transitions["qLoop"][""][variable] = set()
                
                # Push in reverse order since stack is LIFO
                reversed_rule = rule[::-1]
                transitions["qLoop"][""][variable].add(("qLoop", reversed_rule))
    
    # Add transitions for terminal symbols
    for terminal in input_alphabet:
        if terminal not in transitions["qLoop"]:
            transitions["qLoop"][terminal] = {}
        
        transitions["qLoop"][terminal][terminal] = {("qLoop", "")}
    
    # Add acceptance condition when stack has only Z left
    if "" not in transitions["qLoop"]:
        transitions["qLoop"][""] = {}
    transitions["qLoop"][""]["Z"] = {("qAccept", "Z")}
    
    return (states, input_alphabet, stack_alphabet, transitions, start_state, initial_stack, accept_states)

def print_pda(pda):
    """
    Print a readable representation of the PDA
    """
    states, input_alphabet, stack_alphabet, transitions, start_state, initial_stack, accept_states = pda
    
    print("PDA Definition:")
    print("States:", states)
    print("Input Alphabet:", input_alphabet)
    print("Stack Alphabet:", stack_alphabet)
    print("Start State:", start_state)
    print("Initial Stack:", initial_stack if initial_stack else "(empty)")
    print("Accept States:", accept_states)
    print("\nTransitions:")
    
    for state in transitions:
        for input_symbol in transitions[state]:
            for stack_symbol in transitions[state].get(input_symbol, {}):
                for (next_state, push_string) in transitions[state][input_symbol].get(stack_symbol, set()):
                    input_display = input_symbol if input_symbol else "ε"
                    stack_display = stack_symbol if stack_symbol else "ε"
                    push_display = push_string if push_string else "ε"
                    print(f"δ({state}, {input_display}, {stack_display}) = ({next_state}, {push_display})")

# Example usage
def example():
    # Example grammar for balanced parentheses: S -> (S)S | e
    grammar = {
        "S": ["(S)S", "e"]
    }
    
    pda = convert_cfg_to_pda(grammar, "S")
    print_pda(pda)
    
    # Example grammar for a^nb^n: S -> aSb | e
    grammar2 = {
        "S": ["aSb", "e"]
    }
    
    print("\n" + "-"*50 + "\n")
    pda2 = convert_cfg_to_pda(grammar2, "S")
    print_pda(pda2)

if __name__ == "__main__":
    example()