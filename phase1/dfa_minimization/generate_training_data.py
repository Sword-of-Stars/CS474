# -*- coding: utf-8 -*-
"""
DFA Training Data Generator
Generates ~1000 example DFAs, minimizes them, and produces PDF documentation for each.
"""

import os
import shutil
import random
from itertools import combinations
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import pygraphviz as pgv
from automata.fa.dfa import DFA
from solution import Solution

# Import all the visualization functions from main.py
# (You can copy the functions here or import them)

# ---------------------------------------------------------------------
# DFA Generator
# ---------------------------------------------------------------------
class DFAGenerator:
    """Generate random DFAs with various characteristics."""
    
    def __init__(self, seed=None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_random_dfa(self, num_states_range=(3, 8), num_symbols_range=(2, 3), 
                           final_state_prob=0.3, connectivity=0.7):
        """
        Generate a random DFA.
        
        Args:
            num_states_range: (min, max) number of states
            num_symbols_range: (min, max) number of input symbols
            final_state_prob: probability that a state is accepting
            connectivity: probability that each transition exists
        """
        num_states = random.randint(*num_states_range)
        num_symbols = random.randint(*num_symbols_range)
        
        # Generate state names
        states = {str(i) for i in range(1, num_states + 1)}
        
        # Generate input symbols
        symbols = [chr(ord('a') + i) for i in range(num_symbols)]
        input_symbols = set(symbols)
        
        # Pick initial state
        initial_state = "1"
        
        # Pick final states (at least one)
        final_states = set()
        for state in states:
            if random.random() < final_state_prob:
                final_states.add(state)
        if not final_states:
            final_states.add(random.choice(list(states)))
        
        # Generate transitions (ensure complete DFA)
        transitions = {}
        for state in states:
            transitions[state] = {}
            for symbol in input_symbols:
                # Pick a random target state
                transitions[state][symbol] = random.choice(list(states))
        
        # Ensure DFA is connected (reachable from initial state)
        transitions = self._ensure_connectivity(states, input_symbols, transitions, initial_state)
        
        return DFA(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states
        )
    
    def _ensure_connectivity(self, states, symbols, transitions, initial_state):
        """Ensure all states are reachable from initial state."""
        reachable = {initial_state}
        queue = [initial_state]
        
        while queue:
            current = queue.pop(0)
            for symbol in symbols:
                next_state = transitions[current][symbol]
                if next_state not in reachable:
                    reachable.add(next_state)
                    queue.append(next_state)
        
        # If not all states reachable, add transitions to connect them
        unreachable = set(states) - reachable
        if unreachable:
            # Connect each unreachable state
            for state in unreachable:
                # Pick a reachable state and a random symbol
                source = random.choice(list(reachable))
                symbol = random.choice(list(symbols))
                transitions[source][symbol] = state
                reachable.add(state)
                
                # Make sure this state can transition somewhere
                if state not in reachable:
                    queue.append(state)
        
        return transitions
    
    def generate_minimizable_dfa(self, num_states_range=(4, 10), reduction_factor=0.6):
        """
        Generate a DFA that is guaranteed to have redundant states.
        Creates a minimizable DFA by duplicating states.
        """
        # First generate a smaller DFA
        min_states = int(num_states_range[0] * reduction_factor)
        max_states = int(num_states_range[1] * reduction_factor)
        base_dfa = self.generate_random_dfa(
            num_states_range=(min_states, max_states),
            num_symbols_range=(2, 3)
        )
        
        # Duplicate some states to create equivalences
        states = list(base_dfa.states)
        num_duplicates = random.randint(1, len(states) // 2)
        
        new_states = set(base_dfa.states)
        new_transitions = dict(base_dfa.transitions)
        new_finals = set(base_dfa.final_states)
        
        for _ in range(num_duplicates):
            # Pick a state to duplicate
            original = random.choice(states)
            duplicate = str(max([int(s) for s in new_states]) + 1)
            
            new_states.add(duplicate)
            
            # Copy transitions
            new_transitions[duplicate] = dict(new_transitions[original])
            
            # Copy final state status
            if original in new_finals:
                new_finals.add(duplicate)
        
        return DFA(
            states=new_states,
            input_symbols=base_dfa.input_symbols,
            transitions=new_transitions,
            initial_state=base_dfa.initial_state,
            final_states=new_finals
        )
    
    def generate_pattern_dfa(self, pattern_type="alternating"):
        """Generate DFAs with specific patterns for variety."""
        patterns = {
            "alternating": self._gen_alternating_pattern,
            "loop": self._gen_loop_pattern,
            "binary_tree": self._gen_binary_tree_pattern,
            "chain": self._gen_chain_pattern,
        }
        
        if pattern_type in patterns:
            return patterns[pattern_type]()
        else:
            return self.generate_random_dfa()
    
    def _gen_alternating_pattern(self):
        """DFA that accepts strings with alternating symbols."""
        states = {"q0", "q1", "q2", "q3"}
        return DFA(
            states=states,
            input_symbols={"a", "b"},
            transitions={
                "q0": {"a": "q1", "b": "q2"},
                "q1": {"a": "q3", "b": "q0"},
                "q2": {"a": "q0", "b": "q3"},
                "q3": {"a": "q3", "b": "q3"},
            },
            initial_state="q0",
            final_states={"q0", "q1", "q2"}
        )
    
    def _gen_loop_pattern(self):
        """DFA with self-loops."""
        n = random.randint(4, 7)
        states = {str(i) for i in range(1, n + 1)}
        transitions = {}
        
        for i in range(1, n + 1):
            state = str(i)
            transitions[state] = {
                "a": state,  # Self-loop on 'a'
                "b": str((i % n) + 1)  # Cycle on 'b'
            }
        
        final_states = {str(i) for i in range(1, n + 1) if i % 2 == 0}
        
        return DFA(
            states=states,
            input_symbols={"a", "b"},
            transitions=transitions,
            initial_state="1",
            final_states=final_states
        )
    
    def _gen_chain_pattern(self):
        """Linear chain DFA."""
        n = random.randint(4, 8)
        states = {str(i) for i in range(1, n + 1)}
        transitions = {}
        
        for i in range(1, n):
            state = str(i)
            transitions[state] = {
                "a": str(i + 1),
                "b": str(i + 1)
            }
        
        transitions[str(n)] = {"a": str(n), "b": str(n)}
        
        return DFA(
            states=states,
            input_symbols={"a", "b"},
            transitions=transitions,
            initial_state="1",
            final_states={str(n)}
        )
    
    def _gen_binary_tree_pattern(self):
        """Binary tree-like DFA."""
        states = {"q0", "q1", "q2", "q3", "q4", "q5", "q6"}
        return DFA(
            states=states,
            input_symbols={"a", "b"},
            transitions={
                "q0": {"a": "q1", "b": "q2"},
                "q1": {"a": "q3", "b": "q4"},
                "q2": {"a": "q5", "b": "q6"},
                "q3": {"a": "q3", "b": "q3"},
                "q4": {"a": "q4", "b": "q4"},
                "q5": {"a": "q5", "b": "q5"},
                "q6": {"a": "q6", "b": "q6"},
            },
            initial_state="q0",
            final_states={"q3", "q5"}
        )

# ---------------------------------------------------------------------
# Copy visualization functions from main.py
# ---------------------------------------------------------------------

# [Include all the visualization functions here: _sorted_states, _sublabel, 
#  get_equivalence_partition, create_dfa_visualization_pygraphviz, 
#  create_side_by_side_dfa_analysis, create_partition_pygraphviz,
#  create_minimized_dfa_pygraphviz, record_indis_details_with_cumulative_step1,
#  plot_indis_step_enhanced, build_minimized_dfa]

# For brevity, I'll indicate where they should be inserted:
# >>> INSERT ALL VISUALIZATION FUNCTIONS FROM main.py HERE <<<

# ---------------------------------------------------------------------
# Training Data Pipeline
# ---------------------------------------------------------------------

def process_single_dfa(dfa, example_id, output_base_dir="phase1/dfa_minimization/training_data"):
    """
    Process a single DFA through the minimization pipeline and generate PDF.
    
    Args:
        dfa: The DFA to minimize
        example_id: Unique identifier for this example
        output_base_dir: Base directory for training data
    """
    # Create directories for this example
    example_dir = os.path.join(output_base_dir, f"example_{example_id:04d}")
    plots_dir = os.path.join(example_dir, "plots")
    pair_steps_dir = os.path.join(plots_dir, "pair_steps")
    
    os.makedirs(example_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(pair_steps_dir, exist_ok=True)
    
    print(f"[{example_id:04d}] Processing DFA with {len(dfa.states)} states...")
    
    try:
        # Create original DFA visualization
        create_dfa_visualization_pygraphviz(
            dfa, table=None,
            filename=os.path.join(plots_dir, "original_dfa.png"),
            title=f"Original DFA (Example {example_id})"
        )
        
        # Run minimization algorithm
        indis_states, indis_tables, indis_details = record_indis_details_with_cumulative_step1(dfa)
        
        # Create table plots
        indis_plot_paths = []
        for idx, tbl in enumerate(indis_tables):
            newly = set(map(tuple, indis_details[idx]["newly"])) if indis_details[idx]["newly"] else set()
            path = plot_indis_step_enhanced(
                indis_states, tbl, newly, idx,
                output_dir=plots_dir
            )
            indis_plot_paths.append(path)
        
        # Create partition timeline
        blocks_plot_paths = []
        for i, tbl in enumerate(indis_tables):
            blocks = get_equivalence_partition(indis_states, tbl)
            title = f"Partition After Step {i+1}"
            filename = os.path.join(plots_dir, f"blocks_step{i+1}.png")
            path = create_partition_pygraphviz(dfa, blocks, filename=filename, title=title)
            blocks_plot_paths.append(path)
        
        # Create minimized DFA
        final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
        min_dfa = build_minimized_dfa(dfa, final_partition)
        final_min_png = create_minimized_dfa_pygraphviz(
            min_dfa, 
            filename=os.path.join(example_dir, "minimized_dfa.png")
        )
        
        # Prepare data for LaTeX
        data = {
            "indis_plots": [os.path.relpath(path, example_dir) for path in indis_plot_paths],
            "blocks_plots": [os.path.relpath(path, example_dir) for path in blocks_plot_paths],
            "tf": dfa.transitions,
            "indis_details": indis_details,
            "minimized_dfa_png": "minimized_dfa.png" if final_min_png else None,
            "original_dfa_png": "plots/original_dfa.png"
        }
        
        # Generate LaTeX and PDF
        tex_file = os.path.join(example_dir, f"dfa_minimization_{example_id:04d}.tex")
        pdf_file = os.path.join(example_dir, f"dfa_minimization_{example_id:04d}.pdf")
        
        solution = Solution(
            format_path="phase1/dfa_minimization/templates",
            outfile=tex_file
        )
        solution.add_dynamic_content("body.tex", data)
        solution.generate_latex()
        solution.generate_pdf()
        
        # Clean up auxiliary files
        cleanup_latex_auxiliary_files(example_dir, example_id)
        
        print(f"[{example_id:04d}] ✓ PDF generated successfully")
        return True
        
    except Exception as e:
        print(f"[{example_id:04d}] ✗ Error: {e}")
        return False

def cleanup_latex_auxiliary_files(directory, example_id):
    """Remove LaTeX auxiliary files."""
    extensions = ['.aux', '.log', '.out', '.toc']
    for ext in extensions:
        file_path = os.path.join(directory, f"dfa_minimization_{example_id:04d}{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)

def generate_training_dataset(num_examples=1000, output_dir="phase1/dfa_minimization/training_data"):
    """
    Generate a complete training dataset of DFA minimization examples.
    
    Args:
        num_examples: Number of examples to generate
        output_dir: Directory to save all examples
    """
    print(f"=" * 80)
    print(f"DFA MINIMIZATION TRAINING DATA GENERATOR")
    print(f"=" * 80)
    print(f"Target: {num_examples} examples")
    print(f"Output: {output_dir}")
    print(f"=" * 80)
    
    # Create base output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize generator
    generator = DFAGenerator(seed=42)
    
    # Generate variety of DFAs
    successful = 0
    failed = 0
    
    for i in range(num_examples):
        # Vary the type of DFA generated
        if i % 10 == 0:
            # Every 10th example: pattern-based DFA
            pattern = random.choice(["alternating", "loop", "binary_tree", "chain"])
            dfa = generator.generate_pattern_dfa(pattern)
        elif i % 3 == 0:
            # Every 3rd: guaranteed minimizable
            dfa = generator.generate_minimizable_dfa(
                num_states_range=(5, 10),
                reduction_factor=random.uniform(0.5, 0.7)
            )
        else:
            # Random DFA
            dfa = generator.generate_random_dfa(
                num_states_range=(3, 8),
                num_symbols_range=(2, 3),
                final_state_prob=random.uniform(0.2, 0.5)
            )
        
        # Process the DFA
        success = process_single_dfa(dfa, i + 1, output_dir)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Progress update every 50 examples
        if (i + 1) % 50 == 0:
            print(f"\n{'=' * 80}")
            print(f"Progress: {i + 1}/{num_examples} examples processed")
            print(f"Success: {successful} | Failed: {failed}")
            print(f"{'=' * 80}\n")
    
    # Final summary
    print(f"\n{'=' * 80}")
    print(f"GENERATION COMPLETE!")
    print(f"{'=' * 80}")
    print(f"Total examples: {num_examples}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {100 * successful / num_examples:.1f}%")
    print(f"Output directory: {output_dir}")
    print(f"{'=' * 80}\n")

# ---------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate DFA minimization training data')
    parser.add_argument('--num', type=int, default=1000, help='Number of examples to generate')
    parser.add_argument('--output', type=str, default='phase1/dfa_minimization/training_data',
                       help='Output directory for training data')
    
    args = parser.parse_args()
    
    generate_training_dataset(num_examples=args.num, output_dir=args.output)