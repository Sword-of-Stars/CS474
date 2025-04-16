import os
import sys

from automata.tm.dtm import DTM
from graphviz import Digraph

from solution import Solution

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "")))


# first, define the transitions for the TM
transitions={
        # Start in q0: add 1 from least significant bit (left)
        'q_0': {
            '0': ('q_a', '1', 'N'),  # 0 + 1 = 1, no carry
            '1': ('q_0', '0', 'R'),        # 1 + 1 = 0 (carry), move right
            '_': ('q_a', '1', 'N'),  # If carry still remains, write 1
        },
    }

tm = DTM(
    states={'q_0', 'q_a'},
    input_symbols={'0', '1'},
    tape_symbols={'0', '1', '_'},
    transitions=transitions,
    initial_state='q_0',
    blank_symbol='_',
    final_states={'q_a'}
)


def visualize_tm_graphviz(transitions, filename='phase3/universal_turing_machine/out/tm_graph'):
    dot = Digraph(format='png')
    
    # Global graph settings for spacing and aesthetics
    dot.attr(ranksep='1.5', nodesep='1.0')  # more space between rows/columns
    dot.attr('node', shape='circle', fontsize='14', width='0.5', fixedsize='false')
    dot.attr('edge', fontsize='12', penwidth='1.2')

    for src, symbol_map in transitions.items():
        dot.node(src)  # make sure all states are defined
        for read, (dst, write, move) in symbol_map.items():
            label = f"  {read}→{write},{move}"
            dot.edge(src, dst, label=label)

    dot.render(filename, view=False)


def generate_encoding_schema(tm):
    states = tm.states.union({"q_r"})
    tape_alphabet = sorted(tm.tape_symbols)

    directions = ['R', 'L', 'N']

    state_enc = {state: "1"*(i+1) for i, state in enumerate(states)}
    tape_enc = {letter: "1"*(i+1) for i, letter in enumerate(tape_alphabet)}
    dir_enc = {direction: "1"*(i+1) for i, direction in enumerate(directions)}

    return state_enc, tape_enc, dir_enc


def encode_string(string, schema):
    _, tape_enc, _ = schema

    encoded_string = ""

    for char in string:
        encoded_string += f"0{tape_enc[char]}"

    return encoded_string



def encode_TM(tm, schema):

    transitions = ""
    state_enc, tape_enc, dir_enc = schema

    for src, symbol_map in tm.transitions.items():
        for read, (dst, write, move) in symbol_map.items():
            transitions += f"{state_enc[src]}0{tape_enc[read]}0{state_enc[dst]}0{tape_enc[write]}0{dir_enc[move]}00"
    return transitions



class UTM:
    def __init__(self, tm, string):
        self.tm = tm
        self.string = string

        self.schema = generate_encoding_schema(tm)

        self.tapes = self.create_UTM_tapes()
        self.pointers = [0,0,0] # the index of the pointer on each tape

    def get_encoded_TM(self):
        return self.tapes[0]
    
    def get_encoded_state(self):
        return self.tapes[2]

    def create_UTM_tapes(self):
        tape_1 = encode_TM(self.tm, self.schema)  # <-- fixed
        tape_2 = encode_string(self.string, self.schema)[1:]
        state_enc, tape_enc, dir_enc = self.schema
        tape_3 = state_enc[self.tm.initial_state]
        return tape_1, tape_2, tape_3
    
    def execute_transition_abbreviated(self):
        t1, t2, t3 = self.tapes
        p1, p2, p3 = self.pointers
        current_char = t2[p2:].split("0", 1)[0]
        current_state = t3

        # Parse transitions from tape 1 (TM encoding)
        transitions = [t.split("0") for t in t1.split("00") if t]

        for parts in transitions:
            if len(parts) != 5:
                continue  # Skip malformed transitions
            state, read, dst, write, direction = parts
            if state == current_state and read == current_char:
                # Match found
                print("Found a match!")
                # Perform the transition
                # Write new symbol
                symbol_len = len(current_char)
                t2 = t2[:p2] + write + t2[p2 + symbol_len:]

                # Move the head on tape 2
                if direction == "11":  # Left
                    # Move p2 to previous symbol (scan backwards for 0)
                    back = t2[:p2][::-1]
                    zero_idx = back.find("0")
                    if zero_idx == -1:
                        p2 = 0
                    else:
                        prev_start = p2 - zero_idx - 1
                        prev_sym = t2[:prev_start].rfind("0") + 1 if "0" in t2[:prev_start] else 0
                        p2 = prev_sym
                elif direction == "1":  # Right
                    # Move p2 to next symbol (scan forwards after next 0)
                    next_zero = t2[p2:].find("0")
                    if next_zero == -1:
                        p2 = len(t2)  # Move to end
                    else:
                        p2 += next_zero + 1
                else:
                    pass # no-op

                # Update the tapes and pointers
                self.tapes = (t1, t2, dst)
                self.pointers = [p1, p2, 0]
                print(self)
                return True


        if self.schema[0]["q_a"] == current_state:
            print("Halt accept")
            return False
        elif self.schema[0]["q_r"] == current_state:
            print("Halt reject")
            return False
        return True


    def __str__(self):
        s = "Universal Turing Machine\n"
        for i, tape in enumerate(self.tapes):
            s += f"T{i+1}: {tape} at position {self.pointers[i]}\n"
        return s

#===== Main =====#
visualize_tm_graphviz(transitions)

string = "1101"
schema = generate_encoding_schema(tm)
encoded_string = encode_string(string, schema)
encode_TM(tm, schema)
utm = UTM(tm, string)
while utm.execute_transition_abbreviated():
    pass

data = {
    "string": string,
    "encoded_string": encoded_string,
    "encoded_TM": utm.get_encoded_TM(),
    "encoded_state": utm.get_encoded_state()
}

my_Solution = Solution("phase3/universal_turing_machine/templates", "phase3/universal_turing_machine/out/utm_visualizer.tex")
my_Solution.add_dynamic_content("body.tex", data)
# my_Solution.generate_latex()
# my_Solution.generate_pdf()