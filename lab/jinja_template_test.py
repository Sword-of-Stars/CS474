from jinja2 import Template
import subprocess

e_removal_iterable_template = """

{% macro bold_red(character) -%}
    \\textcolor{red}{\\textbf{ {{character}} }}
{%- endmacro -%}

{% macro bold_red(character) -%}
    \\textcolor{red}{\\textbf{ {{character}} }}
{%- endmacro -%}

{% for state, closure in e_closure_table.items() %}
\subsection*{Handling State ${{ state }}$}

\\begin{enumerate}
    \item \\textcolor{gray}{Calculate the $\epsilon$-closure of the state in M; call the result $S$.} 
    From the $\epsilon$-closure table, we know that $E(\{ {{state}} \})=\{ {{closure}} \}$. 
    
    \item \\textcolor{gray}{Calculate the transitions in $M$ from each state in $R$ on each input character.} 
    \\begin{itemize}
        {% for character, value in transitions.get(state, 'ERROR').items() %}
            \item [{{bold_red(character)}}] 
            Here we must collect all places we can get to when reading an {{bold_red(character)}}
            starting in any state in \{ {{closure}} \}. 
            Since
            {% for e_closure_state in closure %}
                $\delta({{e_closure_state}}, {{bold_red(character)}}) = 
                \{ {{ transitions.get(e_closure_state, empty_set).get(character, empty_set) }} \}$, 
            {% endfor %}
            
            we see then that $\delta_R({{state}}, {{bold_red(character)}})$ includes at least 
            \{ {{partial_closure.get(state, empty_set).get(character, empty_set)}} \}.
        {% endfor %}
    \end{itemize}

    \item \\textcolor{gray}{For each input character, calculate the $\epsilon$-closure of the resulting set of states.}   
    \\begin{itemize}
    {% for character, value in transitions.get(state, 'ERROR').items() %}
            \item [{{bold_red(character)}}] 
            Merging the relevant rows in the table for $E(\{ {{partial_closure.get(state, empty_set).get(character, empty_set) }} \})$, 
            we see that $\delta_R( {{state}}, {{character}} )=\{ {{aggregate_closure.get(state, empty_set)[character]}} \}$. 
        {% endfor %}
    \end{itemize}
\end{enumerate}

After processing state {{state}}, we add these new transitions to $M'$. This is depicted below with the original NFA $M$ on the left and $M'$ on the right.

{% endfor %}
"""

e_colsure_template = open("phase1/part_c/templates/e_removal.tex", "r").read()

template = Template(e_colsure_template)

e_closure = {
    'q1': {'q3', 'q1'}, 
    'q2': {'q2'}, 
    'q3': {'q3'}, 
    'q4': {'q4', 'q3'}, 
    'q5': {'q5'}
    }

transitions = {
    'q1': {'a': {'q2'}, 'b': {}}, 
    'q2': {'a': {'q4', 'q3'}, 'b': {'q2'}}, 
    'q3': {'a': {'q5'}, 'b': {'q2', 'q1', 'q5'}}, 
    'q4': {'a': {}, 'b': {'q5', 'q3'}}, 
    'q5': {'a': {}, 'b': {}}
}

partial_closure = {
    "q1":{'a': {'q5', 'q2'}, 'b': {'q5', 'q1', 'q2'}},
    "q2":{'a': {'q3', 'q4'}, 'b': {'q2'}},
    "q3":{'a': {'q5'}, 'b': {'q5', 'q1', 'q2'}},
    "q4":{'a': {'q5'}, 'b': {'q1', 'q2', 'q5', 'q3'}},
    "q5":{'a': {}, 'b': {}}
     }

aggregate_closure = {
    'q1': {'a': {'q5', 'q2'}, 'b': {'q1', 'q2', 'q5', 'q3'}},
    'q2': {'a': {'q3', 'q4'}, 'b': {'q2'}},
    'q3': {'a': {'q5'}, 'b': {'q1', 'q2', 'q5', 'q3'}},
    'q4': {'a': {'q5'}, 'b': {'q1', 'q2', 'q5', 'q3'}},
    'q5': {'a': {}, 'b': {}}
    }


def reverse_transform_dict_with_integers(data):
    reversed_data = {}
    for key, value in data.items():
        new_key = int(key[1:]) # Remove 'q' and convert to integer
        if isinstance(value, set):
            new_value = {int(item[1:]) if item else None for item in value} # Handle empty set by checking for item before conversion, although in current context empty sets should remain empty sets
            new_value = {item for item in new_value if item is not None} # Remove None if any were added from empty strings in sets (though in current case should not be an issue)
        elif isinstance(value, dict):
            new_value = {}
            for inner_key, inner_value in value.items():
                if isinstance(inner_value, set):
                    new_inner_value = {int(item[1:]) if item else None for item in inner_value} #Same logic as above for sets
                    new_inner_value = {item for item in new_inner_value if item is not None} # Remove None values
                else: # Assuming empty set case, handle based on possible types if needed
                    new_inner_value = set() # Keep as empty set
                new_value[inner_key] = new_inner_value
        else: # Handle cases where value is not set or dict as needed
            new_value = value # Or handle differently if other types appear

        reversed_data[new_key] = new_value
    return reversed_data

reversed_e_closure = reverse_transform_dict_with_integers(e_closure)
reversed_transitions = reverse_transform_dict_with_integers(transitions)
reversed_partial_closure = reverse_transform_dict_with_integers(partial_closure)
reversed_aggregate_closure = reverse_transform_dict_with_integers(aggregate_closure)

latex_empty_set = r'\varnothing' # Define as raw string

data = {
    "e_closure_table": reversed_e_closure,
    "transitions": reversed_transitions,
    "partial_closure": reversed_partial_closure,
    "aggregate_closure": reversed_aggregate_closure,
    "empty_set": latex_empty_set
}

from pprint import pprint

pprint(reversed_transitions)
pprint(reversed_e_closure) 

'''
{1: {'a': {2}, 'b': set()},
 2: {'a': {3, 4}, 'b': {2}},
 3: {'a': {5}, 'b': {1, 2, 5}},
 4: {'a': set(), 'b': {3, 5}},
 5: {'a': set(), 'b': set()}}
'''

rendered_string = template.render(data)

format = open("phase1/part_c/templates/format.tex", "r").read()
introduction = open("phase1/part_c/templates/introduction.tex", "r").read()
conclusion = open("phase1/part_c/templates/conclusion.tex", "r").read()

with open("phase1/part_c/out/e_removal.tex", "w") as f:
    f.write(format)
    f.write(introduction)
    f.write(rendered_string)    
    f.write(conclusion)

tex_filepath = "phase1/part_c/out/e_removal.tex"
output_dir = "phase1/part_c/out/" # Directory where you want PDFs

subprocess.run(["pdflatex",
                 "-output-directory=" + output_dir,
                 tex_filepath])

print(f"PDF generated in output directory: {output_dir}/e_removal.pdf") # Confirmation