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
    """
    Transforms grammar notation for LaTeX display.
    Converts [Xy] to X_y format for subscripts.
    """
    transformed_grammar = {}
    
    for variable, rules in grammar.items():
        formatted_var = variable
        
        transformed_rules = []
        
        for rule in rules:
            transformed_rule = ""
            i = 0
            
            while i < len(rule):
                if (i + 3 < len(rule) and 
                    rule[i] == '[' and 
                    rule[i+3] == ']'):
                    transformed_rule += rule[i+1] + '_' + rule[i+2]
                    i += 4
                else:
                    transformed_rule += rule[i]
                    i += 1
                    
            transformed_rules.append(transformed_rule)
            
        transformed_grammar[formatted_var] = transformed_rules
        
    return transformed_grammar

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

def analyze_nullable_rules(grammar, nullable_vars):
    """
    Analyzes all rules to find which ones contain nullable variables
    and generates all possible derived rules.
    
    Returns a list of dicts with rule analysis information.
    """
    analysis = []
    
    for variable, rules in grammar.items():
        for rule in rules:
            if rule == 'e':
                continue
                
            nullable_in_rule = []
            positions = []
            
            for i, char in enumerate(rule):
                if char in nullable_vars:
                    nullable_in_rule.append(char)
                    positions.append(i)
            
            if nullable_in_rule:
                new_rules = []
                
                for r in range(1, len(positions) + 1):
                    for combo in itertools.combinations(range(len(positions)), r):
                        new_rule = list(rule)
                        for idx in sorted(combo, reverse=True):
                            new_rule[positions[idx]] = ''
                        result = ''.join(new_rule)
                        if result and result != rule: 
                            new_rules.append({
                                'rule': result,
                                'removed': [nullable_in_rule[i] for i in combo]
                            })
                
                analysis.append({
                    'variable': variable,
                    'original_rule': rule,
                    'nullable_vars': nullable_in_rule,
                    'positions': positions,
                    'new_rules': new_rules,
                    'has_nullable': True
                })
    
    return analysis

def visualize_unit_rule_graph(edges, grammar, output_path="phase2/chomsky_converter/out/directed_graph.png"):
    """
    Creates an enhanced visualization of the unit rule dependency graph.
    Shows which variables can reach others via unit rules.
    """
    G = nx.DiGraph()
    G.add_edges_from(edges)
    
    all_vars = set(grammar.keys())
    for var in all_vars:
        if var not in G:
            G.add_node(var)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    try:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    except:
        pos = nx.spring_layout(G, seed=42)
    
    nodes_with_outgoing = set([e[0] for e in edges])
    nodes_with_incoming = set([e[1] for e in edges])
    isolated_nodes = all_vars - nodes_with_outgoing - nodes_with_incoming
    
    nx.draw_networkx_nodes(G, pos, nodelist=list(isolated_nodes), 
                          node_color='#E8F4F8', node_size=1800, 
                          edgecolors='#2E86AB', linewidths=2, ax=ax)
    if len(nodes_with_outgoing | nodes_with_incoming) > 0:
        nx.draw_networkx_nodes(G, pos, nodelist=list(nodes_with_outgoing | nodes_with_incoming),
                              node_color='#A7C7E7', node_size=1800,
                              edgecolors='#1B5E88', linewidths=2.5, ax=ax)
    
    if len(edges) > 0:
        nx.draw_networkx_edges(G, pos, edge_color='#2E86AB', 
                              arrows=True, arrowsize=20, arrowstyle='-|>', 
                              width=2.5, connectionstyle='arc3,rad=0.1',
                              min_source_margin=15, min_target_margin=15, ax=ax)
    
    labels = {}
    for node in G.nodes():
        if node == 'S_0':
            labels[node] = '$S_0$'
        else:
            labels[node] = node
    
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=14, font_weight='bold', 
                           font_family='sans-serif', ax=ax)
    
    ax.set_title("Unit Rule Dependency Graph\n(Variables with paths between them can substitute rules)", 
                 fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return G

def compute_unit_rule_closure(grammar, node_graph):
    """
    Uses Floyd-Warshall (APSP) concept via NetworkX to find all reachable variables.
    Returns a dictionary showing which variables can reach which others.
    """
    all_pairs_paths = {}
    
    for v1 in grammar.keys():
        all_pairs_paths[v1] = {}
        for v2 in grammar.keys():
            if v1 == v2:
                all_pairs_paths[v1][v2] = {'reachable': True, 'distance': 0}
            elif nx.has_path(node_graph, v1, v2):
                path = nx.shortest_path(node_graph, v1, v2)
                all_pairs_paths[v1][v2] = {
                    'reachable': True, 
                    'distance': len(path) - 1,
                    'path': path
                }
            else:
                all_pairs_paths[v1][v2] = {'reachable': False, 'distance': float('inf')}
    
    return all_pairs_paths

def eliminate_unit_rules_with_explanation(grammar, node_graph):
    """
    Eliminates unit rules and provides step-by-step explanation data.
    """
    closure = compute_unit_rule_closure(grammar, node_graph)
    
    steps = []
    new_grammar = deepcopy(grammar)
    unit_rules_to_remove = {}
    
    for variable, rules in grammar.items():
        unit_rules_to_remove[variable] = [r for r in rules if r in grammar.keys()]
    
    for v1 in grammar.keys():
        added_rules = []
        
        for v2 in grammar.keys():
            if v1 != v2 and closure[v1][v2]['reachable']:
                non_unit_rules = [r for r in grammar[v2] if r not in grammar.keys()]
                
                if non_unit_rules:
                    steps.append({
                        'from': v1,
                        'to': v2,
                        'path': closure[v1][v2].get('path', []),
                        'distance': closure[v1][v2]['distance'],
                        'rules_added': non_unit_rules
                    })
                    
                    new_grammar[v1].extend(non_unit_rules)
                    added_rules.extend(non_unit_rules)
        
        new_grammar[v1] = list(set(new_grammar[v1]))
    
    for variable in new_grammar.keys():
        new_grammar[variable] = [r for r in new_grammar[variable] if r not in grammar.keys()]
    
    return new_grammar, steps, unit_rules_to_remove

grammar = {
    "S": ["AaB", "b", "S"],
    "A": ["S", "e", "AB"],
    "B": ["bbb", "ASA"],
}

initial_grammar = deepcopy(grammar)

grammar["S_0"] = ["S"]

nullable_vars = []

for key in grammar:
    if "e" in grammar[key]:
        nullable_vars.append(key)

nullable_analysis = analyze_nullable_rules(grammar, nullable_vars)

rules_with_nullable = {}
for variable, rules in grammar.items():
    rules_with_nullable[variable] = []
    for rule in rules:
        for nullable_var in nullable_vars:
            if nullable_var in rule and rule != 'e':
                rules_with_nullable[variable].append(rule)
                break

for char in nullable_vars:
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

node_graph = visualize_unit_rule_graph(edges, grammar)

unit_removed_grammar, unit_elimination_steps, unit_rules_marked = eliminate_unit_rules_with_explanation(grammar, node_graph)

new_grammar = deepcopy(unit_removed_grammar)
rules_with_mixed_terminals = {}

for variable, rules in unit_removed_grammar.items():
    replacements = set()
    rules_with_mixed_terminals[variable] = []
    
    for rule in rules:
        if len(rule) == 1:
            continue
        has_terminal = False
        for char in rule:
            if char.islower():
                replacements.add(rule)
                has_terminal = True
                break
        if has_terminal:
            rules_with_mixed_terminals[variable].append(rule)

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
    
        results = []
        for match in re.finditer(pattern, rule):
            if match.group(1):
                results.append(match.group(1))
            elif match.group(2):
                for char in match.group(2):
                    results.append(char)

        if len(results) > 2:
            new_grammar[variable].remove(rule)

            while len(results) > 2:
                a, b = results[:2]
                rhs = f"{a}{b}"

                var_found = None
                for v, r_list in new_grammar.items():
                    if rhs in r_list and len(r_list) == 1:
                        var_found = v
                        break
                
                if var_found is None:
                    var = unused_characters.pop(0)
                    new_grammar[var] = [rhs]
                else:
                    var = var_found
                
                results = results[2:]
                results.insert(0, var)

            new_rule = "".join(results)
            new_grammar[variable].append(new_rule)
            
final_grammar = transform_grammar(deepcopy(new_grammar))

data = {
    "grammar": grammar,
    "initial_grammar": initial_grammar,
    "nullable": nullable_vars,
    "nullable_analysis": nullable_analysis,
    "rules_with_nullable": rules_with_nullable,
    "e_removal_1_grammar": e_removal_1_grammar,
    "e_removal_2_grammar": e_removal_2_grammar,
    "has_unit_rules": len(edges) > 0,
    "unit_rules_marked": unit_rules_marked,
    "unit_elimination_steps": unit_elimination_steps,
    "unit_removed_grammar": unit_removed_grammar,
    "rules_with_mixed_terminals": rules_with_mixed_terminals,
    "one_term_or_var_grammar": one_term_or_vars_grammar,
    "final_grammar": final_grammar,
    "edges": edges
}

my_Solution = Solution("phase2/templates", "phase2/out/cnf_converter.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()