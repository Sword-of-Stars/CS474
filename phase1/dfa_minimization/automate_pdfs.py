"""
Automated DFA Training Data Generator
Generates 1000+ DFA minimization examples as PDFs
"""

import os
import sys
import shutil
import random
import matplotlib
matplotlib.use("Agg")
from automata.fa.dfa import DFA

from .main import (
    _sorted_states, get_equivalence_partition,
    create_dfa_visualization_pygraphviz,
    create_side_by_side_dfa_analysis,
    create_partition_pygraphviz,
    create_minimized_dfa_pygraphviz,
    record_indis_details_with_cumulative_step1,
    plot_indis_step_enhanced,
    build_minimized_dfa
)
from .solution import Solution

class DFAGenerator:
    """Generate random DFAs for training data."""
    
    def __init__(self, seed=None):
        if seed:
            random.seed(seed)
    
    def generate_random_dfa(self, num_states=None, num_symbols=2):
        """Generate a random connected DFA."""
        if num_states is None:
            num_states = random.randint(3, 8)
        
        states = {str(i) for i in range(1, num_states + 1)}
        symbols = [chr(ord('a') + i) for i in range(num_symbols)]
        input_symbols = set(symbols)
        
        initial_state = "1"
        
        num_finals = random.randint(1, max(1, num_states // 2))
        final_states = set(random.sample(list(states), num_finals))
        
        transitions = {}
        for state in states:
            transitions[state] = {}
            for symbol in input_symbols:
                transitions[state][symbol] = random.choice(list(states))
        
        return DFA(
            states=states,
            input_symbols=input_symbols,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states
        )
    
    def generate_minimizable_dfa(self):
        """Generate a DFA guaranteed to have redundant states."""
        base_size = random.randint(3, 5)
        base_dfa = self.generate_random_dfa(num_states=base_size, num_symbols=2)
        
        states = list(base_dfa.states)
        num_duplicates = random.randint(1, 3)
        
        new_states = set(base_dfa.states)
        new_transitions = dict(base_dfa.transitions)
        new_finals = set(base_dfa.final_states)
        
        for _ in range(num_duplicates):
            original = random.choice(states)
            duplicate = str(max([int(s) for s in new_states]) + 1)
            
            new_states.add(duplicate)
            new_transitions[duplicate] = dict(new_transitions[original])
            
            if original in new_finals:
                new_finals.add(duplicate)
        
        return DFA(
            states=new_states,
            input_symbols=base_dfa.input_symbols,
            transitions=new_transitions,
            initial_state=base_dfa.initial_state,
            final_states=new_finals
        )


def process_single_dfa(dfa, example_id, base_dir="training_data"):
    """Process one DFA and generate its PDF."""
    
    example_dir = os.path.join(base_dir, f"example_{example_id:04d}")
    plots_dir = os.path.join(example_dir, "plots")
    pair_steps_dir = os.path.join(plots_dir, "pair_steps")
    
    for d in [example_dir, plots_dir, pair_steps_dir]:
        os.makedirs(d, exist_ok=True)
    
    original_cwd = os.getcwd()
    
    try:
        print(f"[{example_id:04d}] Processing DFA with {len(dfa.states)} states...", end=" ")
        
        create_dfa_visualization_pygraphviz(
            dfa, table=None,
            filename=os.path.join(plots_dir, "original_dfa.png"),
            title=f"DFA Example {example_id}"
        )
        
        indis_states, indis_tables, indis_details = record_indis_details_with_cumulative_step1(dfa)

        try:
            repo_pair_dir = os.path.join(os.path.dirname(__file__), 'out', 'plots', 'pair_steps')
            dest_pair_dir = os.path.join(plots_dir, 'pair_steps')
            os.makedirs(dest_pair_dir, exist_ok=True)
            def _maybe_copy(rel_path: str):
                if not rel_path:
                    return
                rel_path = rel_path.replace('\\', '/')
                if not rel_path.startswith('pair_steps/'):
                    return
                fname = os.path.basename(rel_path)
                src = os.path.join(repo_pair_dir, fname)
                dst = os.path.join(dest_pair_dir, fname)
                if os.path.exists(src):
                    try:
                        shutil.copyfile(src, dst)
                    except Exception:
                        pass
            for step in indis_details:
                for ps in step.get('pair_substeps', []):
                    for probe in ps.get('probes', []):
                        _maybe_copy(probe.get('visual_path'))
        except Exception:
            pass
        
        indis_plot_paths = []
        for idx, tbl in enumerate(indis_tables):
            newly = set(map(tuple, indis_details[idx]["newly"])) if indis_details[idx]["newly"] else set()
            
            import matplotlib.pyplot as plt
            n = len(indis_states)
            fig, ax = plt.subplots(figsize=(max(8, n * 1.2), max(6, n)))
            ax.set_xlim(0, n - 1)
            ax.set_ylim(0, n - 1)

            for i in range(1, n):
                for j in range(i):
                    x, y = j, n - 1 - i
                    pair = tuple(sorted((indis_states[j], indis_states[i])))
                    
                    ax.add_patch(plt.Rectangle((x, y), 1, 1, fill=True, facecolor='white',
                                               edgecolor='black', linewidth=1.2))
                    
                    if tbl[pair]:
                        if pair in newly:
                            color, weight, alpha = 'red', 'bold', 1.0
                        else:
                            color, weight, alpha = 'darkred', 'normal', 0.6
                        ax.text(x + 0.5, y + 0.5, 'X', ha='center', va='center',
                               fontsize=18, fontweight=weight, color=color, alpha=alpha)

            ax.set_xticks([j + 0.5 for j in range(n - 1)])
            ax.set_xticklabels(indis_states[:-1], fontsize=14)
            ax.xaxis.tick_bottom()
            ax.set_yticks([n - 1 - i + 0.5 for i in range(1, n)])
            ax.set_yticklabels(indis_states[1:], fontsize=14)
            ax.yaxis.tick_left()
            ax.set_title(f"Indistinguishability Table â€” Step {idx + 1}", fontsize=20, pad=20)
            ax.invert_yaxis()
            ax.tick_params(length=0)
            
            if idx > 0:
                legend_elements = [
                    plt.Line2D([0], [0], marker='X', color='red', linestyle='None',
                              markersize=15, label='Newly marked', markeredgewidth=2),
                    plt.Line2D([0], [0], marker='X', color='darkred', linestyle='None',
                              markersize=15, label='Previously marked', alpha=0.6, markeredgewidth=2)
                ]
                ax.legend(handles=legend_elements, loc='upper right')
            
            plt.tight_layout()
            filename = os.path.join(plots_dir, f"indis_step{idx + 1}.png")
            fig.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            indis_plot_paths.append(filename)
        
        blocks_plot_paths = []
        for i, tbl in enumerate(indis_tables):
            blocks = get_equivalence_partition(indis_states, tbl)
            path = create_partition_pygraphviz(
                dfa, blocks,
                filename=os.path.join(plots_dir, f"blocks_step{i+1}.png"),
                title=f"Partition After Step {i+1}"
            )
            blocks_plot_paths.append(path)
        
        final_partition = get_equivalence_partition(indis_states, indis_tables[-1])
        min_dfa = build_minimized_dfa(dfa, final_partition)
        final_min_png = create_minimized_dfa_pygraphviz(
            min_dfa,
            filename=os.path.join(plots_dir, "minimized_dfa.png")
        )
        
        data = {
            "indis_plots": [f"plots/indis_step{i+1}.png" for i in range(len(indis_plot_paths))],
            "blocks_plots": [f"plots/blocks_step{i+1}.png" for i in range(len(blocks_plot_paths))],
            "tf": dfa.transitions,
            "indis_details": indis_details,
            "minimized_dfa_png": "plots/minimized_dfa.png",
            "original_dfa_png": "plots/original_dfa.png"
        }
        
        os.chdir(example_dir)
        
        tex_file = f"dfa_minimization_{example_id:04d}.tex"
        
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        solution = Solution(
            format_path=template_path,
            outfile=tex_file
        )
        solution.add_dynamic_content("body.tex", data)
        solution.generate_latex()
        
        import subprocess
        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            tex_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            tex_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for ext in ['.aux', '.log', '.out', '.toc']:
            aux_file = f"dfa_minimization_{example_id:04d}{ext}"
            if os.path.exists(aux_file):
                os.remove(aux_file)
        
        if os.path.exists(tex_file):
            os.remove(tex_file)
        
        pdf_old = f"dfa_minimization_{example_id:04d}.pdf"
        pdf_new = f"example_{example_id:04d}.pdf"
        if os.path.exists(pdf_old):
            os.rename(pdf_old, pdf_new)
        
        os.chdir(original_cwd)
        
        print("âœ“")
        return True
        
    except Exception as e:
        os.chdir(original_cwd)
        print(f"âœ— Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_training_data(num_examples=1000):
    """Generate training dataset."""
    print(f"\n{'='*80}")
    print(f"DFA MINIMIZATION TRAINING DATA GENERATOR")
    print(f"{'='*80}")
    print(f"Generating {num_examples} examples...")
    print(f"{'='*80}\n")
    
    base_dir = "training_data"
    os.makedirs(base_dir, exist_ok=True)
    
    generator = DFAGenerator(seed=42)
    
    successful = 0
    failed = 0
    
    for i in range(192, num_examples):
        if i % 3 == 0:
            dfa = generator.generate_minimizable_dfa()
        else:
            dfa = generator.generate_random_dfa()
        
        if process_single_dfa(dfa, i + 1, base_dir):
            successful += 1
        else:
            failed += 1
        
        if (i + 1) % 50 == 0:
            print(f"\nProgress: {i+1}/{num_examples} | Success: {successful} | Failed: {failed}\n")
    
    print(f"\n{'='*80}")
    print(f"COMPLETE!")
    print(f"Total: {num_examples} | Success: {successful} | Failed: {failed}")
    print(f"Success rate: {100*successful/num_examples:.1f}%")
    print(f"Output: {base_dir}/")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate DFA training data')
    parser.add_argument('--num', type=int, default=1000, help='Number of examples')
    args = parser.parse_args()
    
    generate_training_data(num_examples=args.num)
