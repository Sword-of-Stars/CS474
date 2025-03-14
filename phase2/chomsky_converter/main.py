import re
import os
import sys
import string
import itertools

import networkx as nx
import matplotlib.pyplot as plt


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from solution import Solution
from copy import deepcopy

def display_grammar(grammar):
    for key in grammar:
        print(key, '->', ' | '.join(grammar[key]))

def transform_grammar(grammar):
    transformed_grammar = {}
    
    for variable, rules in grammar.items():
        transformed_rules = []
        
        for rule in rules:
            transformed_rule = ""
            i = 0
            
            while i < len(rule):
                # Check for pattern [Xy]
                if (i + 3 < len(rule) and 
                    rule[i] == '[' and 
                    rule[i+3] == ']'):
                    # Replace [Xy] with X_y
                    transformed_rule += rule[i+1] + '_' + rule[i+2]
                    i += 4
                else:
                    transformed_rule += rule[i]
                    i += 1
                    
            transformed_rules.append(transformed_rule)
            
        transformed_grammar[variable] = transformed_rules
        
    return transformed_grammar

# Note, we'll need to include code for the indirect transformations eventually

def replace_chars(s, chars_to_replace, replacement_char):
    """
    Replaces characters in a string with a replacement character using itertools.

    Args:
        s: The input string.
        chars_to_replace: A list of characters to replace.
        replacement_char: The character to replace with.

    Returns:
        A list of strings with characters replaced.
    """
    indices_to_replace = [i for i, char in enumerate(s) if char in chars_to_replace]
    results = []

    if not indices_to_replace:
        return []

    max_replacements = len(indices_to_replace)

    for r in range(max_replacements + 1):
        for indices in itertools.combinations(indices_to_replace, r):
            new_s = list(s)
            for index in indices:
                new_s[index] = replacement_char
            results.append("".join(new_s))

    return results

def visualize_directed_graph(edges):
    G = nx.DiGraph()
    G.add_edges_from(edges)

    pos = nx.spring_layout(G)  # Layout mehod

    nx.draw(G, pos, with_labels=True, node_size=1500, node_color='skyblue', arrowsize=20)

    plt.savefig("phase2/chomsky_converter/out/directed_graph.png")

    return G

grammar = {
    "S":["AaB", "b", "S"],
    "A":["S", "e", "AB"],
    "B":["bbb","ASA"],
}

initial_grammar = deepcopy(grammar)

# begin by adding S0 -> S to the grammar
grammar["S0"] = ["S"]

nullable_vars = []

# first, find the variables that can make e directly
for key in grammar:
    if "e" in grammar[key]:
        nullable_vars.append(key)

for char in nullable_vars: # eliminate each variable that can make e directly
    for variable, rules in grammar.items():
        to_append = []

        for rule in rules:
            new_rules = replace_chars(rule, char, "")
            to_append.extend(new_rules)

        grammar[variable].extend(to_append)
        grammar[variable] = list(set(grammar[variable]))

e_removal_1_grammar = deepcopy(grammar)

for variable, rules in grammar.items():
    if "e" in rules:
        rules.remove("e")

e_removal_2_grammar = deepcopy(grammar)

# next, we make a graph for all unit rules
unit_rules = {}

for key in grammar:
    unit_rules[key] = []
    for rule in grammar[key]:
        if rule in grammar.keys():
            unit_rules[key].append(rule)

edges = []
for start, ends in unit_rules.items():
    for end in ends:
        edges.append((start, end))

# Example usage
node_graph = visualize_directed_graph(edges)

# then, all rules that can be reached by unit rules
# have their rules added to the original variable
for v1, rule in grammar.items():
    for v2 in grammar.keys():
        if nx.has_path(node_graph, v1, v2):
            grammar[v1].extend(grammar[v2])
            grammar[v1] = list(set(grammar[v1]))

# then remove the unit rules
for variable, rule in grammar.items():
    grammar[variable] = [r for r in rule if r not in grammar.keys()]

unit_removed_grammar = deepcopy(grammar)

new_grammar = deepcopy(grammar)

for variable, rules in grammar.items():
    replacements = set()
    for rule in rules:
        # if a rule contains anything but single terminals,
        # replace those terminals with a variable
        if len(rule) == 1:
            continue
        for char in rule:
            if char.islower():
                replacements.add(rule)

    for rule in replacements:
        new_grammar[variable].remove(rule)

        result = ""
        for char in rule:
            if char.islower():
                new_grammar[f"[U{char}]"] = [char]
                result += f"[U{char}]"
            else:
                result += char

        new_grammar[variable].append(result)

grammar = deepcopy(new_grammar)
one_term_or_vars_grammar = transform_grammar(deepcopy(grammar))

unused_characters = [x for x in string.ascii_uppercase if x not in grammar.keys()]

for variable, rules in grammar.items():

    for rule in rules:
        pattern = r'(\[[^\]]+\])|([^[]+?(?=\[|$))'
    
        # do some re matching to extract characters
        results = []
        for match in re.finditer(pattern, rule):
            if match.group(1):  # Bracketed content
                # Remove the brackets and add to results
                results.append(match.group(1))
            elif match.group(2):  # Non-bracketed content
                # Split non-bracketed content into individual characters
                for char in match.group(2):
                    results.append(char)

        if len(results) > 2:
            
            new_grammar[variable].remove(rule)
            new_rule = ""

            while len(results) > 2:
                a, b = results[:2]

                # add a new variable to the grammar which is the composite
                rhs = f"{a}{b}"

                # Find if this RHS already exists in the grammar
                var_found = None
                for v, r_list in new_grammar.items():
                    if rhs in r_list and len(r_list) == 1:
                        var_found = v
                        break
                
                # If not found, create a new variable
                if var_found is None:
                    var = unused_characters.pop(0)
                    new_grammar[var] = [rhs]
                else:
                    var = var_found
                
                # Update the rule under consideration
                results = results[2:]
                results.insert(0, var)

            new_rule = "".join(results)
            new_grammar[variable].append(new_rule)
            
final_grammar = transform_grammar(deepcopy(new_grammar))

data = {
    "grammar":grammar,
    "initial_grammar":initial_grammar,
    "nullable":nullable_vars,
    "e_removal_1_grammar":e_removal_1_grammar,
    "e_removal_2_grammar":e_removal_2_grammar,
    "has_unit_rules":True,
    "unit_removed_grammar":unit_removed_grammar,
    "one_term_or_var_grammar":one_term_or_vars_grammar,
    "final_grammar":final_grammar
}

my_Solution = Solution("phase2/templates", "phase2/out/cnf_converter.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()