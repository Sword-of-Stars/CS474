import os
import sys
import matplotlib.pyplot as plt
from IPython.display import display
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from solution import Solution

os.makedirs("out/plots", exist_ok=True)

class TuringMachine:
    def __init__(self, tape_string, blank_symbol, initial_state, accept_state, reject_state, transition_function):
        self.tape = {i: ch for i, ch in enumerate(tape_string)}
        self.blank_symbol = blank_symbol
        self.head = 0
        self.current_state = initial_state
        self.accept_state = accept_state
        self.reject_state = reject_state
        self.transition_function = transition_function

    def step(self):
        sym = self.tape.get(self.head, self.blank_symbol)
        key = (self.current_state, sym)
        if key not in self.transition_function:
            return False
        new_sym, direction, new_state = self.transition_function[key]
        self.tape[self.head] = new_sym
        if direction == 'R':
            self.head += 1
        elif direction == 'L':
            self.head -= 1
        self.current_state = new_state
        return True

    def is_halted(self):
        return self.current_state in {self.accept_state, self.reject_state}


def format_state_latex(state):
    if not isinstance(state, str):
        return str(state)
    if state.startswith('q') and len(state) > 1:
        if state == 'qaccept':
            return 'q_{\\text{accept}}'
        elif state == 'qreject':
            return 'q_{\\text{reject}}'
        else:
            num = state[1:]
            return f'q_{{{num}}}'
    return state


def create_transition_table(transition_function, blank_symbol='⊔'):
    """Rows are states, columns are input symbols."""
    states = sorted(set(key[0] for key in transition_function.keys()))
    symbols = sorted(set(key[1] for key in transition_function.keys()))
    
    table_data = []
    for state in states:
        row = {'State': format_state_latex(state)}
        for symbol in symbols:
            key = (state, symbol)
            if key in transition_function:
                write_sym, direction, new_state = transition_function[key]
                formatted_state = format_state_latex(new_state)
                
                if write_sym == '#':
                    write_sym_display = r'\#'
                elif write_sym == blank_symbol:
                    write_sym_display = r'\sqcup'
                else:
                    write_sym_display = write_sym
                
                if symbol == '#':
                    symbol_key = r'\#'
                elif symbol == blank_symbol:
                    symbol_key = r'\sqcup'
                else:
                    symbol_key = symbol
                    
                row[symbol_key] = f'({write_sym_display}, {direction}, {formatted_state})'
            else:
                if symbol == '#':
                    symbol_key = r'\#'
                elif symbol == blank_symbol:
                    symbol_key = r'\sqcup'
                else:
                    symbol_key = symbol
                row[symbol_key] = '---'
        table_data.append(row)
    
    return pd.DataFrame(table_data)


def record_detailed_configurations(tm, max_steps=100):
    """
    Returns (configs, details) where they are
      configs = [ (tape_dict, head, state), ... ]
      details[i] = {'head_position', 'read_symbol', 'written_symbol', 'new_state', 'current_transition'}
    Includes the final halting configuration as the last entry.
    """
    configs = []
    details = []

    configs.append((dict(tm.tape), tm.head, tm.current_state))
    details.append({
        "head_position": tm.head,
        "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
        "written_symbol": None,
        "new_state": tm.current_state,
        "current_transition": None
    })

    for _ in range(max_steps):
        if tm.is_halted():
            break
        curr_state = tm.current_state
        curr_head  = tm.head
        read_sym   = tm.tape.get(curr_head, tm.blank_symbol)
        key        = (curr_state, read_sym)
        if key not in tm.transition_function:
            break
        write_sym, direction, next_state = tm.transition_function[key]

        tm.step()

        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": curr_head,
            "read_symbol": read_sym,
            "written_symbol": write_sym,
            "new_state": next_state,
            "current_transition": (curr_state, read_sym, write_sym, direction, next_state),
            "current_state_raw": curr_state
        })

    if not configs or configs[-1][2] not in {tm.accept_state, tm.reject_state}:
        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": tm.head,
            "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
            "written_symbol": None,
            "new_state": tm.current_state,
            "current_transition": None,
            "current_state_raw": tm.current_state
        })

    return configs, details


def plot_configuration_before_after(tape_dict_before, tape_dict_after, head_before, head_after, changed_positions,
                                   fixed_left, fixed_right, blank_symbol='⊔'):
    """Plot before and after configurations with highlighting and transparency.
    Changed cells are highlighted, and cells away from head have reduced opacity."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 4))
    
    def in_focus(pos, head_pos):
        return abs(pos - head_pos) <= 2
    
    for i in range(fixed_left, fixed_right+1):
        sym = tape_dict_before.get(i, blank_symbol)
        alpha = 1.0 if in_focus(i, head_before) else 0.3
        rect = plt.Rectangle((i,0), 1, 1, fill=False, edgecolor='black', alpha=alpha)
        ax1.add_patch(rect)
        ax1.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12, alpha=alpha)
    
    ax1.text(fixed_left-1.5, 0.5, 'Before:', ha='right', va='center', fontsize=12, weight='bold')
    
    ax1.annotate("",
                xy=(head_before+0.5, 0),
                xytext=(head_before+0.5, -0.7),
                arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
    
    ax1.set_xlim(fixed_left-2, fixed_right+2)
    ax1.set_ylim(-1, 1.5)
    ax1.axis('off')
    
    ax1.text(fixed_right+1.5, 0.5, '...', ha='center', va='center', fontsize=14)
    
    for i in range(fixed_left, fixed_right+1):
        sym = tape_dict_after.get(i, blank_symbol)
        alpha = 1.0 if in_focus(i, head_after) else 0.3
        
        if i in changed_positions:
            facecolor = 'lightgreen'
            rect = plt.Rectangle((i,0), 1, 1, fill=True, facecolor=facecolor, 
                                edgecolor='green', linewidth=2, alpha=alpha)
        else:
            rect = plt.Rectangle((i,0), 1, 1, fill=False, edgecolor='black', alpha=alpha)
        
        ax2.add_patch(rect)
        ax2.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12, alpha=alpha)
    
    ax2.text(fixed_left-1.5, 0.5, 'After:', ha='right', va='center', fontsize=12, weight='bold')
    
    ax2.annotate("",
                xy=(head_after+0.5, 0),
                xytext=(head_after+0.5, -0.7),
                arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
    
    ax2.set_xlim(fixed_left-2, fixed_right+2)
    ax2.set_ylim(-1, 1.5)
    ax2.axis('off')
    
    ax2.text(fixed_right+1.5, 0.5, '...', ha='center', va='center', fontsize=14)
    
    plt.tight_layout()
    display(fig)
    plt.close(fig)
    return fig


def plot_all_configurations_with_transitions(configs, details, fixed_left, fixed_right, blank_symbol='⊔'):
    """Plot before/after for each transition and save PNGs, ultimately returning a list of Figures."""
    figs = []
    for idx, (tape, head, state) in enumerate(configs):
        if idx == 0:
            print(f"Step {idx}: Initial State={state}, Head@{head}")
            fig, ax = plt.subplots(figsize=(10, 2))
            
            for i in range(fixed_left, fixed_right+1):
                sym = tape.get(i, blank_symbol)
                rect = plt.Rectangle((i,0), 1, 1, fill=False, edgecolor='black')
                ax.add_patch(rect)
                ax.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12)
                # Add index labels
                ax.text(i+0.5, 1.3, str(i), ha='center', va='center', fontsize=8, color='gray')
            
            ax.text(fixed_left-1.5, 0.5, 'Initial:', ha='right', va='center', fontsize=12, weight='bold')
            ax.annotate("",
                       xy=(head+0.5, 0),
                       xytext=(head+0.5, -0.7),
                       arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
            ax.text(fixed_right+1.5, 0.5, '...', ha='center', va='center', fontsize=14)
            
            ax.set_xlim(fixed_left-2, fixed_right+2)
            ax.set_ylim(-1, 2)
            ax.axis('off')
            plt.tight_layout()
            display(fig)
            plt.close(fig)
            fig.savefig(f"out/plots/plot{idx+1}.png", dpi=150)
            figs.append(fig)
        else:
            print(f"Step {idx}: State={state}, Head@{head}")
            tape_before = configs[idx-1][0]
            tape_after = tape
            head_before = configs[idx-1][1]
            head_after = head
            
            changed_positions = set()
            if details[idx].get('current_transition'):
                changed_positions.add(details[idx]['head_position'])
            
            fig = plot_configuration_before_after(tape_before, tape_after, 
                                                 head_before, head_after,
                                                 changed_positions,
                                                 fixed_left, fixed_right, blank_symbol)
            fig.savefig(f"out/plots/plot{idx+1}.png", dpi=150)
            figs.append(fig)
    
    return figs


# --- TM Definition ---

blank = '⊔'
transition_function = {
    ('q1', '0'): ('x', 'R', 'q2'),
    ('q1', '1'): ('x', 'R', 'q8'),
    ('q1', '#'): ('#', 'R', 'q4'),
    ('q1', 'x'): ('x', 'R', 'q1'),
    
    ('q2', '0'): ('0', 'R', 'q2'),
    ('q2', '1'): ('1', 'R', 'q2'),
    ('q2', '#'): ('#', 'R', 'q4'),
    
    ('q8', '0'): ('0', 'R', 'q8'),
    ('q8', '1'): ('1', 'R', 'q8'),
    ('q8', '#'): ('#', 'R', 'q3'),
    
    ('q4', 'x'): ('x', 'R', 'q4'),
    ('q4', '0'): ('x', 'L', 'q6'),
    ('q4', blank): (blank, 'S', 'qaccept'),
    
    ('q3', 'x'): ('x', 'R', 'q3'),
    ('q3', '1'): ('x', 'L', 'q6'),
    ('q3', '0'): ('0', 'R', 'qreject'),
    ('q3', blank): (blank, 'S', 'qaccept'),
    
    ('q5', 'x'): ('x', 'R', 'q5'),
    ('q5', '0'): ('0', 'R', 'q5'),
    ('q5', '1'): ('1', 'R', 'q5'),
    
    ('q6', '0'): ('0', 'L', 'q6'),
    ('q6', '1'): ('1', 'L', 'q6'),
    ('q6', 'x'): ('x', 'L', 'q6'),
    ('q6', '#'): ('#', 'L', 'q7'),
    
    ('q7', '0'): ('0', 'L', 'q7'),
    ('q7', '1'): ('1', 'L', 'q7'),
    ('q7', 'x'): ('x', 'R', 'q1'),
}

test_string_10 = "0101#0101"      

tm_10 = TuringMachine(
    tape_string=test_string_10,
    blank_symbol=blank,
    initial_state='q1',
    accept_state='qaccept',
    reject_state='qreject',
    transition_function=transition_function
)

configs, details = record_detailed_configurations(tm_10, max_steps=500)
plots = plot_all_configurations_with_transitions(configs, details,
                                                 fixed_left=-5,
                                                 fixed_right=15,
                                                 blank_symbol=blank)

transition_table = create_transition_table(transition_function, blank_symbol=blank)

data = {
    "plots": plots,
    "tf": transition_function,
    "details": details,
    "transition_table": transition_table,
    "blank": blank
}

my_Solution = Solution("phase3/turing_machines/templates", "phase3/turing_machines/out/tm_steps.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()