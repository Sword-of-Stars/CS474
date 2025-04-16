import os
import re
from collections import namedtuple
from typing import List, Dict, Tuple, Optional
import jinja2

def generate_encoding_schema(tm):
    states = tm.states.union({"qr"})
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
        self.history = []  # Store history of configurations
        
        self.schema = generate_encoding_schema(tm)
        
        self.tapes = self.create_UTM_tapes()
        self.pointers = [0, 0, 0]  # the index of the pointer on each tape
        
        # Save initial configuration
        self.history.append({
            'tapes': self.tapes,
            'pointers': self.pointers.copy(),
            'current_state': self.tm.initial_state,
            'transition_description': "Initial configuration"
        })
    
    def create_UTM_tapes(self):
        tape_1 = encode_TM(self.tm, self.schema)
        tape_2 = encode_string(self.string, self.schema)[1:]
        state_enc, tape_enc, dir_enc = self.schema
        tape_3 = state_enc[self.tm.initial_state]
        return tape_1, tape_2, tape_3
    
    def decode_symbol(self, encoded_symbol):
        """Decode an encoded symbol back to its original form"""
        state_enc, tape_enc, dir_enc = self.schema
        # Reverse the tape_enc dictionary
        rev_tape_enc = {v: k for k, v in tape_enc.items()}
        return rev_tape_enc.get(encoded_symbol, "?")
    
    def decode_state(self, encoded_state):
        """Decode an encoded state back to its original form"""
        state_enc, tape_enc, dir_enc = self.schema
        # Reverse the state_enc dictionary
        rev_state_enc = {v: k for k, v in state_enc.items()}
        return rev_state_enc.get(encoded_state, "?")
    
    def decode_direction(self, encoded_dir):
        """Decode an encoded direction back to its original form"""
        state_enc, tape_enc, dir_enc = self.schema
        # Reverse the dir_enc dictionary
        rev_dir_enc = {v: k for k, v in dir_enc.items()}
        return rev_dir_enc.get(encoded_dir, "?")
    
    def execute_transition_abbreviated(self):
        t1, t2, t3 = self.tapes
        p1, p2, p3 = self.pointers
        current_char = t2[p2:].split("0", 1)[0]
        current_state = t3
        
        # Decode for logging
        decoded_state = self.decode_state(current_state)
        decoded_char = self.decode_symbol(current_char)
        
        # Parse transitions from tape 1 (TM encoding)
        transitions = [t.split("0") for t in t1.split("00") if t]
        
        for parts in transitions:
            if len(parts) != 5:
                continue  # Skip malformed transitions
            state, read, dst, write, direction = parts
            if state == current_state and read == current_char:
                # Match found
                print(f"Found a match! ${decoded_state}, {decoded_char} -> {self.decode_state(dst)}, {self.decode_symbol(write)}, {self.decode_direction(direction)}$")
                
                # Perform the transition
                # Write new symbol
                symbol_len = len(current_char)
                t2 = t2[:p2] + write + t2[p2 + symbol_len:]
                
                # Move the head on tape 2
                old_p2 = p2
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
                    pass  # no-op
                
                # Update the tapes and pointers
                self.tapes = (t1, t2, dst)
                self.pointers = [p1, p2, 0]
                
                # Add to history
                transition_desc = f"$({decoded_state}, {decoded_char}) \\to ({self.decode_state(dst)}, {self.decode_symbol(write)}, {self.decode_direction(direction)})$"
                self.history.append({
                    'tapes': self.tapes,
                    'pointers': self.pointers.copy(),
                    'current_state': self.decode_state(dst),
                    'transition_description': transition_desc
                })
                
                print(self)
                return True
        
        # No transition found - add rejection state to history
        self.history.append({
            'tapes': self.tapes,
            'pointers': self.pointers.copy(),
            'current_state': "reject",
            'transition_description': "No matching transition found: reject"
        })
        
        print("No matching transition found: reject")
        return False
    
    def run_machine(self, max_steps=30):
        """Run the UTM for a maximum number of steps or until halt"""
        step = 0
        while step < max_steps:
            if not self.execute_transition_abbreviated():
                break
            step += 1
    
    def generate_latex(self, output_file="utm_visualization.tex", template=""):
        """Generate LaTeX visualization of the UTM execution history"""
        # Load the Jinja2 template
        template_loader = jinja2.FileSystemLoader(searchpath="./")
        template_env = jinja2.Environment(loader=template_loader, trim_blocks=True, lstrip_blocks=True)
        template = template_env.from_string(template)
        
        # Process history and generate legend
        legend, steps = self.process_history_for_latex()
        
        # Prepare the context data for the template
        context = {
            'legend': legend,
            'steps': steps,
            'title': f"UTM Execution on Input '{self.string}'"
        }
        
        # Render the template
        output_text = template.render(**context)
        print(output_text)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(output_text)
        
        print(f"LaTeX visualization saved to {output_file}")
        return output_file
    
    def process_history_for_latex(self):
        """Process the execution history for LaTeX visualization with decoded values"""
        processed_steps = []
        
        # Create encoding schema legend information at the beginning
        encoding_legend = self.create_encoding_legend()
        
        for step_idx, step in enumerate(self.history):
            tapes = step['tapes']
            pointers = step['pointers']
            
            # For each tape, create a list of visible characters with positions
            formatted_tapes = []
            
            # Process tape 1 (encoded TM)
            tape1_range = self.calculate_visible_range(tapes[0], pointers[0], 15)
            tape1_chars = self.extract_visible_chars(tapes[0], tape1_range)
            pointer_rel_pos = pointers[0] - tape1_range[0] if tape1_range[0] <= pointers[0] < tape1_range[1] else -1
            
            # Identify encoded sequences in tape 1 (transitions)
            encoding_groups = self.identify_encoding_groups(tapes[0], tape1_range)
            
            formatted_tapes.append({
                'name': 'Tape 1 (Encoded TM)',
                'color': 'redtape',
                'characters': tape1_chars,
                'pointer_char_pos': pointer_rel_pos,
                'cell_width': 0.8,
                'encoding_groups': encoding_groups,
                'colored_parts': self.identify_colored_parts(tapes[0], tape1_range)
            })
            
            # Process tape 2 (input string)
            tape2_range = self.calculate_visible_range(tapes[1], pointers[1], 15)
            tape2_chars = self.extract_visible_chars(tapes[1], tape2_range)
            pointer_rel_pos = pointers[1] - tape2_range[0] if tape2_range[0] <= pointers[1] < tape2_range[1] else -1
            
            # Identify encoded symbols in tape 2
            tape2_decoded = self.decode_tape_symbols(tapes[1], tape2_range)
            
            formatted_tapes.append({
                'name': 'Tape 2 (Input)',
                'color': 'greentape',
                'characters': tape2_chars,
                'pointer_char_pos': pointer_rel_pos,
                'cell_width': 0.8,
                'decoded_values': tape2_decoded
            })
            
            # Process tape 3 (current state)
            current_state_enc = tapes[2]
            current_state_dec = self.decode_state(tapes[2])
            state_chars = [(i, char) for i, char in enumerate(current_state_enc)]
            
            formatted_tapes.append({
                'name': f'Tape 3 (Current State: ${current_state_dec}$)',
                'color': 'purpletape',
                'characters': state_chars,
                'pointer_char_pos': pointers[2] if pointers[2] < len(current_state_enc) else 0,
                'cell_width': 0.8,
                'decoded_values': {len(current_state_enc)//2: current_state_dec} if len(current_state_enc) > 0 else {}
            })
            
            processed_steps.append({
                'step_number': step_idx,
                'tapes': formatted_tapes,
                'current_state': step['current_state'],
                'transition_description': step['transition_description']
            })
        
        return encoding_legend, processed_steps

    def create_encoding_legend(self):
        """Create a legend explaining the encoding schema"""
        state_enc, tape_enc, dir_enc = self.schema
        
        # Format the schema data for the template
        legend = {
            'states': [(state, enc) for state, enc in state_enc.items()],
            'symbols': [(symbol, enc) for symbol, enc in tape_enc.items()],
            'directions': [(direction, enc) for direction, enc in dir_enc.items()]
        }
        
        # Add an example transition for illustration
        # Find a sample transition from the TM
        sample_transition = None
        if self.tm.transitions:
            src_state = list(self.tm.transitions.keys())[0]
            if self.tm.transitions[src_state]:
                sym = list(self.tm.transitions[src_state].keys())[0]
                dst, write, move = self.tm.transitions[src_state][sym]
                sample_transition = {
                    'src': src_state,
                    'read': sym,
                    'dst': dst,
                    'write': write,
                    'move': move,
                    'encoded': f"{state_enc[src_state]}0{tape_enc[sym]}0{state_enc[dst]}0{tape_enc[write]}0{dir_enc[move]}"
                }
        
        legend['sample_transition'] = sample_transition
        return legend

    def identify_colored_parts(self, tape, visible_range):
        """Identify and color-code different parts of transitions"""
        if not tape:
            return []
        
        start_idx, end_idx = visible_range
        visible_tape = tape[start_idx:end_idx]

        parts = []
        pos = 0
        part_idx = 0
        
        # Split by '0' delimiter
        segments = visible_tape.split('0')
        
        for segment in segments:
            if segment:
                # Determine which part of the transition we're in based on position
                part_type = part_idx % 5  # There are 5 parts in a transition
                
                color = "black"  # Default
                if part_type == 0:
                    color = "statecolor"  # Source state
                elif part_type == 1:
                    color = "tapesymbolcolor"  # Read symbol
                elif part_type == 2:
                    color = "dststatecolor"  # Destination state
                elif part_type == 3:
                    color = "writesymbolcolor"  # Write symbol
                elif part_type == 4:
                    color = "directioncolor"  # Move direction
                
                # Add color information for each character
                for i, _ in enumerate(segment):
                    char_pos = pos + i - start_idx
                    if 0 <= char_pos < end_idx - start_idx:
                        parts.append((char_pos, color))
                
                part_idx += 1
            
            pos += len(segment) + 1  # +1 for the '0' delimiter
        
        return parts

    def identify_encoding_groups(self, tape, visible_range):
        """Identify groups of characters that represent encoded transitions"""
        if not tape:
            return []
        
        start_idx, end_idx = visible_range
        visible_tape = tape[start_idx:end_idx]
        
        # Find all occurrences of '00' (transition separators)
        separators = [match.start() for match in re.finditer('00', visible_tape)]
        
        # Add beginning and end of visible section
        points = [0] + [sep + 2 for sep in separators]
        if separators and separators[-1] + 2 < len(visible_tape):
            points.append(len(visible_tape))
        
        # Create groups
        groups = []
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i+1]
            
            # Skip empty groups
            if end - start <= 0:
                continue
            
            # Decode this transition segment
            segment = visible_tape[start:end]
            decoded = self.decode_transition_segment(segment)
            
            # Adjust positions to be relative to visible range
            groups.append({
                'start': start,
                'end': end,
                'decoded': decoded
            })
        
        return groups

    def decode_transition_segment(self, segment):
        """Decode a transition segment into a human-readable form with colored components"""
        # A transition is typically: state0read0dst0write0move0
        parts = segment.split('0')
        
        if len(parts) < 5:
            return "Partial transition"
        
        try:
            src_state = self.decode_state(parts[0])
            read_sym = self.decode_symbol(parts[1])
            dst_state = self.decode_state(parts[2])
            write_sym = self.decode_symbol(parts[3])
            move_dir = self.decode_direction(parts[4])
            
            # Use LaTeX colored text for different components
            return f"({src_state},{read_sym})$\\to$({dst_state},{write_sym},{move_dir})"
        except:
            return "?"

    def calculate_visible_range(self, tape, pointer, num_visible=15):
        """Calculate the range of characters to display centered around the pointer"""
        if not tape:
            return (0, 0)
        
        # Calculate the window of characters to display
        start_idx = max(0, pointer - num_visible // 2)
        end_idx = min(len(tape), start_idx + num_visible)
        
        # Adjust start_idx if we have room at the end
        if end_idx < len(tape) and end_idx - start_idx < num_visible:
            # We can show more at the beginning
            extra = min(start_idx, num_visible - (end_idx - start_idx))
            start_idx -= extra
        elif end_idx == len(tape) and end_idx - start_idx < num_visible:
            # We're at the end of the tape, show more at the beginning
            start_idx = max(0, end_idx - num_visible)
        
        return (start_idx, end_idx)

    def extract_visible_chars(self, tape, range_tuple):
        """Extract characters from the tape within the given range"""
        start_idx, end_idx = range_tuple
        
        # Create a list of visible characters with relative positions
        visible_chars = []
        for i in range(start_idx, end_idx):
            if i < len(tape):
                rel_pos = i - start_idx
                visible_chars.append((rel_pos, tape[i]))
        
        # If we have fewer characters than visible slots, pad with blanks
        while len(visible_chars) < end_idx - start_idx:
            visible_chars.append((len(visible_chars), '#'))
        
        return visible_chars

    def decode_tape_symbols(self, tape, visible_range):
        """Decode visible symbols on a tape"""
        if not tape:
            return {}
        
        start_idx, end_idx = visible_range
        visible_tape = tape[start_idx:end_idx]
        
        decoded_values = {}
        
        # Split by '0' delimiter
        parts = visible_tape.split('0')
        position = 0
        
        for part in parts:
            if part:  # Skip empty parts
                # Try to decode the symbol
                decoded = self.decode_symbol(part)
                if decoded != "?":
                    # Center the decoded value over its encoded representation
                    center_pos = position + len(part) // 2
                    decoded_values[center_pos - start_idx] = decoded
            
            position += len(part) + 1  # +1 for the '0' delimiter
        
        return decoded_values
    
    def __str__(self):
        s = "Universal Turing Machine\n"
        for i, tape in enumerate(self.tapes):
            s += f"T{i+1}: {tape} at position {self.pointers[i]}\n"
        return s


# Example usage with your UTM and input "1101"
if __name__ == "__main__":

    from automata.tm.dtm import DTM

    tm = DTM(
        states={'q_0', 'q_a'},
        input_symbols={'0', '1'},
        tape_symbols={'0', '1', '\\sqcup'},
        transitions={
            # Start in q0: add 1 from least significant bit (left)
            'q_0': {
                '0': ('q_a', '1', 'N'),  # 0 + 1 = 1, no carry
                '1': ('q_0', '0', 'R'),        # 1 + 1 = 0 (carry), move right
                '\\sqcup': ('q_a', '1', 'N'),  # If carry still remains, write 1
            },
        },
        initial_state='q_0',
        blank_symbol='\\sqcup',
        final_states={'q_a'}
    )

    # Create and run the UTM
    utm = UTM(tm, "1101")
    utm.run_machine(max_steps=10)
    
    # Generate LaTeX visualization
    with open("phase3/universal_turing_machine/templates/test.tex", "r") as LATEX:

        latex_file = utm.generate_latex(template=LATEX.read())
    
    # Optionally compile the LaTeX file to PDF
    try:
        os.system(f"pdflatex {latex_file}")
        print("PDF generated successfully!")
    except:
        print("Could not compile PDF. Make sure pdflatex is installed.")