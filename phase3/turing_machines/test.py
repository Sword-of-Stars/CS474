import matplotlib.pyplot as plt

# Define the TuringMachine class.
class TuringMachine:
    def __init__(self, tape_string, blank_symbol, initial_state, accept_state, reject_state, transition_function):
        """
        tape_string: the initial tape input (e.g., "10101").
        blank_symbol: symbol representing blank cells (e.g., '⊔').
        initial_state: starting state (e.g., 'q0').
        accept_state: accept (halting) state.
        reject_state: reject state (if used).
        transition_function: dictionary mapping (state, symbol) to (new_symbol, direction, new_state).
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
        """Execute one transition step; return True if a valid transition occurs."""
        current_symbol = self.tape.get(self.head, self.blank_symbol)
        key = (self.current_state, current_symbol)
        if key in self.transition_function:
            new_symbol, direction, new_state = self.transition_function[key]
            self.tape[self.head] = new_symbol
            if direction == 'R':
                self.head += 1
            elif direction == 'L':
                self.head -= 1
            # For 'S' we do not move the head.
            self.current_state = new_state
            return True
        else:
            # No defined transition: halt.
            return False

    def is_halted(self):
        """Return True if the machine is in an accept or reject state."""
        return self.current_state == self.accept_state or self.current_state == self.reject_state


# Record configurations as (tape_dict, head, state) for each step.
def record_configurations(tm, max_steps=50):
    configurations = []
    configurations.append((dict(tm.tape), tm.head, tm.current_state))
    for _ in range(max_steps):
        if tm.is_halted():
            break
        if not tm.step():
            break
        configurations.append((dict(tm.tape), tm.head, tm.current_state))
    return configurations


# Plot a single configuration using a fixed tape view.
def plot_configuration_fixed(tape_dict, head, state, fixed_left, fixed_right, blank_symbol='⊔'):
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Draw fixed tape cells from fixed_left to fixed_right.
    for i in range(fixed_left, fixed_right + 1):
        symbol = tape_dict.get(i, blank_symbol)
        cell_rect = plt.Rectangle((i, 0), 1, 1, fill=False, edgecolor='black')
        ax.add_patch(cell_rect)
        ax.text(i + 0.5, 0.5, symbol, ha='center', va='center', fontsize=12)
    
    # Draw an arrow pointing from below up to the tape cell under the head.
    ax.annotate("",
                xy=(head + 0.5, 0),         # arrow tip at tape cell
                xytext=(head + 0.5, -0.7),    # arrow start point below tape
                arrowprops=dict(arrowstyle="->", color='red', lw=1.5))
    
    # Display the current state below the arrow in a small text box.
    ax.text(head + 0.5, -1.1, state,
            ha='center', va='center', fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black"))
    
    ax.set_xlim(fixed_left, fixed_right + 1)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')
    plt.tight_layout()
    plt.show()  # This will block until the plot window is closed.


# Define a three-state transition function that handles all inputs.
# States:
#   q0: initial state, processes a cell by marking it and switching to q1.
#   q1: passes through unmodified cells and returns to q0.
#   q2: halting state (accept).
transition_function = {
    # For state q0:
    ('q0', '0'): ('x', 'R', 'q1'),
    ('q0', '1'): ('x', 'R', 'q1'),
    ('q0', '⊔'): ('⊔', 'R', 'q2'),

    # For state q1:
    ('q1', '0'): ('0', 'R', 'q0'),
    ('q1', '1'): ('1', 'R', 'q0'),
    ('q1', '⊔'): ('⊔', 'R', 'q2'),
}

# Create a TuringMachine instance.
tm = TuringMachine(
    tape_string="10101",   # Input tape
    blank_symbol='⊔',
    initial_state='q0',
    accept_state='q2',     # q2 is the halting (accept) state.
    reject_state='qr',     # Unused in this example.
    transition_function=transition_function
)

# Record the configurations for each step.
configs = record_configurations(tm, max_steps=10)

# Define a fixed tape window (this view will not shift).
fixed_left = -5
fixed_right = 15

# Loop through each configuration:
for idx, (tape_dict, head, state) in enumerate(configs):
    # Print text between transitions.
    print(f"--- Transition {idx} ---")
    print(f"Current State: {state}, Head Position: {head}")
    
    # Plot the configuration.
    plot_configuration_fixed(tape_dict, head, state, fixed_left, fixed_right, blank_symbol='⊔')
    
    # Print additional text between plots.
    print(f"Completed Transition {idx}.")
    # Wait for user input to proceed to the next transition.
    input("Press Enter to continue to the next transition...")
