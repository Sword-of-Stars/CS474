# Simple custom language to Turing Machine translator

from typing import List, Tuple, Dict
from collections import defaultdict
import string

# -------------------
# 1. Define simple language
# -------------------

# Example program in our custom mini-language:
program = """
set x 0
loop x < 3
  print x
  inc x
end
"""

# -------------------
# 2. Parse to AST
# -------------------

def parse(program: str) -> List[Tuple[str, List[str]]]:
    lines = [line.strip() for line in program.strip().splitlines() if line.strip()]
    ast = []
    for line in lines:
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]
        ast.append((cmd, args))
    return ast

# -------------------
# 3. Define TM representation
# -------------------

class TuringMachine:
    def __init__(self):
        self.states = set()
        self.transitions = {}  # (state, symbol) -> (new_state, write_symbol, direction)
        self.start_state = 'q0'
        self.accept_state = 'q_accept'
        self.reject_state = 'q_reject'
        self.tape = defaultdict(lambda: '_')
        self.head = 0
        self.current_state = self.start_state

    def add_transition(self, state, symbol, new_state, write, move):
        self.states.update([state, new_state])
        self.transitions[(state, symbol)] = (new_state, write, move)

    def run(self, max_steps=100):
        steps = 0
        while steps < max_steps and self.current_state not in {self.accept_state, self.reject_state}:
            symbol = self.tape[self.head]
            key = (self.current_state, symbol)
            if key not in self.transitions:
                self.current_state = self.reject_state
                break
            new_state, write, move = self.transitions[key]
            self.tape[self.head] = write
            self.head += {'R': 1, 'L': -1, 'N': 0}[move]
            self.current_state = new_state
            steps += 1

    def print_tape(self):
        min_index = min(self.tape.keys())
        max_index = max(self.tape.keys())
        tape_str = ' '.join(self.tape[i] for i in range(min_index, max_index + 1))
        print(f"TAPE: {tape_str}\nHEAD: {'   ' * (self.head - min_index)}^")

# -------------------
# 4. Compile AST to TM transitions
# -------------------

def compile_to_tm(ast: List[Tuple[str, List[str]]]) -> TuringMachine:
    tm = TuringMachine()

    # Just a stub for now. You can expand this to handle variables and control flow.
    # For now, we hardcode: set x 0 => write 'x0' to tape

    tm.tape[0] = 'x'
    tm.tape[1] = '0'
    tm.add_transition('q0', 'x', 'q1', 'x', 'R')
    tm.add_transition('q1', '0', 'q_accept', '0', 'N')

    return tm

# -------------------
# 5. Run it
# -------------------

ast = parse(program)
tm = compile_to_tm(ast)
tm.run()
tm.print_tape()
