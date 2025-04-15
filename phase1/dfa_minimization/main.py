import os
import matplotlib.pyplot as plt
from IPython.display import display

from automata.fa.dfa import DFA

from solution import Solution

# --- DFA Minimization Step Functions ---

def minimize_dfa_steps(dfa):
    """
    Performs iterative partition refinement for DFA minimization.
    Returns a list of partitions, where each partition is a list of blocks (each block is a set of states).
    
    The algorithm starts with:
      P0 = { Final states, Non-final states }
    and then refines until the partition is stable.
    
    Parameters:
      dfa: a DFA object with attributes:
           - dfa.states (set of states)
           - dfa.input_symbols (set of symbols)
           - dfa.transitions (dict mapping state to dict of {symbol: target_state})
           - dfa.final_states (set)
           
    Returns:
      partitions: a list of partitions (one per iteration).
    """
    partitions = []
    
    F = set(dfa.final_states)
    Q = set(dfa.states)
    nonF = Q - F
    # Initial partition: only add nonempty blocks
    P = []
    if F:
        P.append(F)
    if nonF:
        P.append(nonF)
    partitions.append(P)
    
    changed = True
    while changed:
        new_P = []
        # For each block in the partition, refine it.
        for block in P:
            # Use a dictionary to separate states by their "transition signature":
            # For each state, build a tuple of indices (one per input symbol)
            # indicating which block its target state falls into (or None if target not found).
            groups = {}
            for state in block:
                key = []
                for symbol in dfa.input_symbols:
                    target = dfa.transitions.get(state, {}).get(symbol, None)
                    # Identify the block index in which the target lies (if any).
                    target_block = None
                    for i, b in enumerate(P):
                        if target in b:
                            target_block = i
                            break
                    key.append(target_block)
                key = tuple(key)
                if key not in groups:
                    groups[key] = set()
                groups[key].add(state)
            # Each group is a refined block.
            new_P.extend(groups.values())
        # Check if the partition changed.
        if new_P == P:
            changed = False
        else:
            P = new_P
            partitions.append(P)
    return partitions

def record_detailed_minimization_steps(dfa):
    """
    Runs the DFA minimization refinement process and creates details for each step.
    
    Returns:
       steps: list of partitions at each refinement iteration.
       details: list of dictionaries with a description and step number.
    """
    steps = minimize_dfa_steps(dfa)
    details = []
    for i, part in enumerate(steps):
        # Create a string representation for the partition
        part_str = "; ".join([", ".join(sorted(list(block))) for block in part])
        detail = {
            "step": i,
            "partition": [sorted(list(b)) for b in part],
            "description": f"Step {i+1}: Partitioned into {len(part)} block(s) -- {part_str}"
        }
        details.append(detail)
    return steps, details

# --- Visualization Functions for Minimization Steps ---

def plot_minimization_configuration(partition, step):
    """
    Creates a matplotlib figure showing the partition configuration.
    Each block is drawn as a rectangle with the states listed inside.
    
    Parameters:
      partition: a list of blocks (each block is a set of states) for this minimization step.
      step: integer indicating which step (iteration) this is.
    
    Returns:
      fig: a matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 3))
    num_blocks = len(partition)
    
    # We'll draw each block next to each other with a fixed width and some spacing.
    block_width = 2
    spacing = 0.5
    x = 0
    for block in partition:
        # Draw a rectangle for this block.
        rect = plt.Rectangle((x, 0), block_width, 1, facecolor="#e0f7fa", edgecolor="black", lw=2)
        ax.add_patch(rect)
        # Get a string of the states in this block.
        states_str = ", ".join(sorted(list(block)))
        ax.text(x + block_width/2, 0.5, states_str, ha="center", va="center", fontsize=12, fontweight="bold")
        x += block_width + spacing
    # Remove the axis and add a title.
    ax.set_xlim(0, x)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(f"Minimization Step {step+1}", fontsize=16, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig

def plot_all_minimization_steps(steps):
    """
    Iterates through all minimization steps and creates a list of figures for visualization.
    
    Parameters:
      steps: list of partitions (each partition is a list of blocks) from minimization.
    
    Returns:
      plots: list of matplotlib figure objects.
    """
    plots = []
    for i, partition in enumerate(steps):
        fig = plot_minimization_configuration(partition, i)
        plots.append(fig)
    return plots

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
    final_states={"3"}                                  
)

# Now, record the detailed minimization steps.
steps, details = record_detailed_minimization_steps(dfa)

# Create the plot figures for each minimization configuration.
plots = plot_all_minimization_steps(steps)

# --- Integrate with the Document Builder ---
# Assume that your document builder expects a data dictionary in the following format:
data = {
    "plots": plots,               # List of plot figures (each for a minimization step)
    "tf": dfa.transitions,        # The transition function of the original DFA
    "details": details            # List of detail dictionaries for each step
}

# Then, create your solution and add the dynamic content:
from solution import Solution  # assuming your Solution class is in solution.py
my_Solution = Solution("templates", "out/tm_steps.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
