import os
import re
import sys

from automata.tm.dtm import DTM
from graphviz import Digraph

from solution import Solution

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "")))


# first, define the transitions for the TM
transitions={
        # Start in q0: add 1 from least significant bit (left)
        '$q_0$': {
            '0': ('$q_a$', '1', 'N'),  # 0 + 1 = 1, no carry
            '1': ('$q_0$', '0', 'R'),        # 1 + 1 = 0 (carry), move right
            '$\\sqcup$': ('$q_a$', '1', 'N'),  # If carry still remains, write 1
        },
    }

tm = DTM(
    states={'$q_0$', '$q_a$'},
    input_symbols={'0', '1'},
    tape_symbols={'0', '1', '$\\sqcup$'},
    transitions=transitions,
    initial_state='$q_0$',
    blank_symbol='$\\sqcup$',
    final_states={'$q_a$'}
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
    states = tm.states.union({"$q_r$"})
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
        self.state_lookup = {v: k for k, v in self.schema[0].items()}
        self.char_lookup = {v: k for k, v in self.schema[1].items()}
        self.dir_lookup = {v: k for k, v in self.schema[2].items()}



        self.tapes = self.create_UTM_tapes()
        self.pointers = [0,0,0] # the index of the pointer on each tape

    def get_encoded_TM(self):
        return self.tapes[0]
    
    def get_encoded_string(self):
        return self.tapes[1]
    
    def get_encoded_state(self):
        return self.tapes[2]
    
    def get_accept_state(self):
        return self.schema[0]["$q_a$"]
    
    def get_reject_state(self):
        return self.schema[0]["$q_r$"]

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

        prev_p2 = p2

        # the history of steps to return to the autoexplainer
        history = {
                "match": False,
                "string": self.get_encoded_string(),
                "current_state": self.get_encoded_state(),
                "states": [],
                "updates": {}
            }

        # If we're in an accept state, hurray!
        if self.schema[0]["$q_a$"] == current_state:
            print("Halt accept")
            return None, True
        elif self.schema[0]["$q_r$"] == current_state:
            print("Halt reject")
            return None, False

        # Parse transitions from tape 1 (TM encoding)
        # 00 splits transitions, 0 splits parts of each encoding
        transitions = [t.split("0") for t in t1.split("00") if t]

        # Get all positions right after each '00'
        split_indices = [0] + [m.end() for m in re.finditer("00", t1)][:-1]

        for i, parts in enumerate(transitions):
            history["states"].append([])
            if len(parts) != 5:
                continue # Skip malformed transitions
            state, read, dst, write, direction = parts
            
            print(f"Examining state, from idx {split_indices[i]} to {split_indices[i]+len(state)-1}")

            if state == current_state:
                # add current state from TM
                history["states"][i].append((
                    split_indices[i], 
                    split_indices[i]+len(state)-1, 
                    self.state_lookup[current_state], 
                    True))
                
                # examine current state on tape 3
                history["states"][i].append((
                    0, 
                    len(current_state)-1, 
                    self.state_lookup[current_state]
                    ))
                
                print(f"Examining character from {split_indices[i] + len(state)+1} to {split_indices[i] + len(state)+len(read)}")
                # examine transition char on TM
                history["states"][i].append((
                    split_indices[i] + len(state)+1, 
                    split_indices[i] + len(state)+len(read), 
                    self.char_lookup[read]))
                
                # examine char on tape 1 (string)
                history["states"][i].append((
                    p2, 
                    p2+len(current_char)-1, 
                    self.char_lookup[current_char]))
                
            else:
                history["states"][i].append((
                    split_indices[i], 
                    split_indices[i]+len(state)-1, 
                    self.state_lookup[current_state], 
                    False))

            if state == current_state and read == current_char:
                # Match found
                history["match"] = True
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
                history["updates"] = {
                    "state":(dst, self.state_lookup[dst], len(dst)-1),
                    "string": (t2, p2, self.dir_lookup[direction], self.char_lookup[write], prev_p2, prev_p2+len(write)-1),
                }
                self.pointers = [p1, p2, 0]
                print(self)
                return history, None
            
            else:
                print("Not a match, moving on")

        return history, None


    def __str__(self):
        s = "Universal Turing Machine\n"
        for i, tape in enumerate(self.tapes):
            s += f"T{i+1}: {tape} at position {self.pointers[i]}\n"
        return s

#===== Main =====#
visualize_tm_graphviz(transitions)

string = "1101"
schema = generate_encoding_schema(tm)
utm = UTM(tm, string)
initial_string = utm.get_encoded_string()

history = []
final_adjudication = False

states = [(key, i+1, item) for i, (key, item) in enumerate(utm.schema[0].items())]

characters = [(key, i+1, item) for i, (key, item) in enumerate(utm.schema[1].items())]

directions = [(key, i+1, item) for i, (key, item) in enumerate(utm.schema[2].items())]

max_len = max(max(len(states), len(characters)), len(directions))

while True:
    info, resolution = utm.execute_transition_abbreviated()

    if resolution != None:
        final_adjudication = resolution
        break
    else:
        history.append(info)


data = {
    "string": string,
    "encoded_string": initial_string,
    "encoded_TM": utm.get_encoded_TM(),
    "encoded_state": utm.get_encoded_state(),
    "passes": history,
    "total_accept": final_adjudication,
    "accept_state": utm.get_accept_state(),
    "reject_state": utm.get_reject_state(),
    "states": states,
    "characters": characters,
    "directions":directions,
    "max_length":max_len
}

my_Solution = Solution("phase3/universal_turing_machine/templates", "phase3/universal_turing_machine/out/utm_visualizer.tex")
my_Solution.add_dynamic_content("body.tex", data)
my_Solution.generate_latex()
my_Solution.generate_pdf()