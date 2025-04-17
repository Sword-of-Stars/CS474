import os
import sys
import matplotlib.pyplot as plt
from IPython.display import display

# adjust as needed so solution.py can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from solution import Solution

# Make sure output directories exist
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
        # write
        self.tape[self.head] = new_sym
        # move
        if direction == 'R':
            self.head += 1
        elif direction == 'L':
            self.head -= 1
        # update
        self.current_state = new_state
        return True

    def is_halted(self):
        return self.current_state in {self.accept_state, self.reject_state}


def record_detailed_configurations(tm, max_steps=100):
    """
    Returns (configs, details):
      configs = [ (tape_dict, head, state), ... ]
      details[i] = {
         'head_position', 'read_symbol', 'written_symbol', 'new_state'
      }
    Includes the final halting configuration as the last entry.
    """
    configs = []
    details = []

    # record initial—no write yet
    configs.append((dict(tm.tape), tm.head, tm.current_state))
    details.append({
        "head_position": tm.head,
        "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
        "written_symbol": None,
        "new_state": tm.current_state
    })

    for _ in range(max_steps):
        if tm.is_halted():
            break
        # capture before step
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
            "new_state": next_state
        })

    # ensure we include the final (halting) config if not already
    if not configs or configs[-1][2] not in {tm.accept_state, tm.reject_state}:
        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": tm.head,
            "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
            "written_symbol": None,
            "new_state": tm.current_state
        })

    return configs, details


def plot_configuration_fixed(tape_dict, head, state,
                             fixed_left, fixed_right,
                             blank_symbol='⊔'):
    """
    Plot one configuration and return the Figure.
    """
    fig, ax = plt.subplots(figsize=(8,2))
    for i in range(fixed_left, fixed_right+1):
        sym = tape_dict.get(i, blank_symbol)
        rect = plt.Rectangle((i,0),1,1, fill=False, edgecolor='black')
        ax.add_patch(rect)
        ax.text(i+0.5, 0.5, sym, ha='center', va='center', fontsize=12)
    # arrow + state label
    ax.annotate("",
                xy=(head+0.5,0),
                xytext=(head+0.5,-0.7),
                arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
    ax.text(head+0.5, -1.1, state,
            ha='center', va='center', fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"))
    ax.set_xlim(fixed_left, fixed_right+1)
    ax.set_ylim(-1.5,1.5)
    ax.axis('off')
    plt.tight_layout()
    display(fig)
    plt.close(fig)
    return fig


def plot_all_configurations_individually_fixed(configs, fixed_left, fixed_right, blank_symbol='⊔'):
    """
    Plot every configuration (including the final halt) and save PNGs.
    Returns list of Figures.
    """
    figs = []
    for idx, (tape, head, state) in enumerate(configs):
        print(f"Step {idx}: State={state}, Head@{head}")
        fig = plot_configuration_fixed(tape, head, state,
                                       fixed_left, fixed_right,
                                       blank_symbol)
        fig.savefig(f"out/plots/plot{idx+1}.png", dpi=150)
        figs.append(fig)
    return figs


# --- Example TM Definition ---

blank = '⊔'
transition_function = {
    ('q0','0'): ('x','R','q1'),
    ('q0','1'): ('x','R','q1'),
    ('q0',blank): (blank,'S','q2'),
    ('q1','0'): ('0','R','q0'),
    ('q1','1'): ('1','R','q0'),
    ('q1',blank):(blank,'S','q2'),
}

tm = TuringMachine(
    tape_string="10101",
    blank_symbol=blank,
    initial_state='q0',
    accept_state='q2',
    reject_state='qr',
    transition_function=transition_function
)

# --- Run & Plot ---

configs, details = record_detailed_configurations(tm, max_steps=50)
plots = plot_all_configurations_individually_fixed(configs,
                                                  fixed_left=-5,
                                                  fixed_right=15,
                                                  blank_symbol=blank)

# --- Package into LaTeX ---

data = {
    "plots": plots,
    "tf": transition_function,
    "details": details
}

my_Solution = Solution("templates", "out/tm_steps.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()
