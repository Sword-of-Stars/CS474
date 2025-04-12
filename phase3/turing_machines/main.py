import re
import os
import sys
# import string
# import itertools

# import networkx as nx
import matplotlib.pyplot as plt
from IPython.display import display


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from solution import Solution

import matplotlib.pyplot as plt

class TuringMachine:
    def __init__(self, tape_string, blank_symbol, initial_state, accept_state, reject_state, transition_function):
        """
        tape_string: the initial input as a string (e.g., '010').
        blank_symbol: symbol used for blanks (e.g., '⊔' or '_').
        initial_state: the start state (e.g., 'q0').
        accept_state: the accept/halting state (e.g., 'ha').
        reject_state: the reject/halting state (e.g., 'hr').
        transition_function: dict with keys (state, symbol) and values (new_symbol, direction, new_state).
        """
        self.tape = {}
        for i, char in enumerate(tape_string):
            self.tape[i] = char
        
        self.blank_symbol = blank_symbol
        self.head = 0
        self.current_state = initial_state
        self.accept_state = accept_state
        self.reject_state = reject_state
        self.transition_function = transition_function

    def step(self):
        """
        Executes one transition step.
        Returns True if a valid transition was made; returns False if no transition is available (machine halts).
        """
        current_symbol = self.tape.get(self.head, self.blank_symbol)
        key = (self.current_state, current_symbol)
        
        if key in self.transition_function:
            new_symbol, direction, new_state = self.transition_function[key]
            
            self.tape[self.head] = new_symbol
            
            if direction == 'R':
                self.head += 1
            elif direction == 'L':
                self.head -= 1
            
            self.current_state = new_state
            return True
        else:
            return False

    def is_halted(self):
        """
        Checks if the machine is in either the accept or reject state.
        """
        return self.current_state == self.accept_state or self.current_state == self.reject_state

def plot_configuration_fixed(tape_dict, head, state, fixed_left, fixed_right, blank_symbol='⊔'):
    """
    Plots a single Turing Machine configuration with a fixed tape range.
    The tape cells remain in a fixed position and only the state pointer (arrow & label) moves.
    
    Parameters:
      tape_dict (dict): Mapping of tape indices to symbols.
      head (int): The current head position.
      state (str): The current state.
      fixed_left (int): The leftmost tape cell index to display.
      fixed_right (int): The rightmost tape cell index to display.
      blank_symbol (str): Symbol for blank cells.
    """
    fig, ax = plt.subplots(figsize=(8, 2))
    
    for i in range(fixed_left, fixed_right + 1):
        symbol = tape_dict.get(i, blank_symbol)
        cell_rect = plt.Rectangle((i, 0), 1, 1, fill=False, edgecolor='black')
        ax.add_patch(cell_rect)
        ax.text(i + 0.5, 0.5, symbol, ha='center', va='center', fontsize=12)
    
    ax.annotate("",
                xy=(head + 0.5, 0),         
                xytext=(head + 0.5, -0.7), 
                arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
    
    ax.text(head + 0.5, -1.1, state,
            ha='center', va='center', fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"))
    
    ax.set_xlim(fixed_left, fixed_right + 1)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')
    plt.tight_layout()
    
    display(fig)
    plt.close(fig)

plots = []

def plot_all_configurations_individually_fixed(configs, fixed_left, fixed_right, blank_symbol='⊔'):
    """
    Iterates through a list of configurations and plots each one as its own figure,
    using a fixed tape range for every configuration.
    
    Parameters:
      configs (list): List of tuples (tape_dict, head, state).
      fixed_left (int): The leftmost tape cell index to display.
      fixed_right (int): The rightmost tape cell index to display.
      blank_symbol (str): Symbol for blank cells.
    """
    for idx, (tape_dict, head, state) in enumerate(configs):
        print(f"Transition {idx}:")
        fig = plot_configuration_fixed(tape_dict, head, state, fixed_left, fixed_right, blank_symbol)
        plots.append(fig)

# def record_configurations(tm, max_steps=50):
#     configurations = []
#     configurations.append((dict(tm.tape), tm.head, tm.current_state))
    
#     for _ in range(max_steps):
#         if tm.is_halted():
#             break
#         if not tm.step():
#             break
#         configurations.append((dict(tm.tape), tm.head, tm.current_state))
    
#     return configurations

def record_detailed_configurations(tm, max_steps=50):
    configs = []
    details = [] 
    
    initial_config = (dict(tm.tape), tm.head, tm.current_state)
    configs.append(initial_config)
    details.append({
        "head_position": tm.head,
        "read_symbol": tm.tape.get(tm.head, tm.blank_symbol),
        "written_symbol": None,   
        "new_state": tm.current_state,
    })
    
    for _ in range(max_steps):
        if tm.is_halted():
            break
        read_symbol = tm.tape.get(tm.head, tm.blank_symbol)
        if not tm.step():
            break

        written_symbol = tm.tape.get(tm.head - 1, tm.blank_symbol)  
        
        configs.append((dict(tm.tape), tm.head, tm.current_state))
        details.append({
            "head_position": tm.head,
            "read_symbol": read_symbol,
            "written_symbol": written_symbol,
            "new_state": tm.current_state,
        })
    
    return configs, details

transition_function = {
    ('q0', '0'): ('x', 'R', 'q1'),
    ('q0', '1'): ('x', 'R', 'q1'),
    ('q0', '⊔'): ('⊔', 'R', 'q2'),

    ('q1', '0'): ('0', 'R', 'q0'),
    ('q1', '1'): ('1', 'R', 'q0'),
    ('q1', '⊔'): ('⊔', 'R', 'q2')
}

tm = TuringMachine(
    tape_string="10101",    
    blank_symbol='⊔',
    initial_state='q0',
    accept_state='q2',    
    reject_state='qr',    
    transition_function=transition_function
)

configs_dets = record_detailed_configurations(tm, max_steps=10)
plot_all_configurations_individually_fixed(configs_dets[0], fixed_left=-5, fixed_right=15, blank_symbol='⊔')

data = {
    "plots": plots,
    "tf":transition_function,
    "details": configs_dets[1]
}

my_Solution = Solution("templates", "out/tm_steps.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()

