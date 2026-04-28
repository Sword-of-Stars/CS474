import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("ok")

from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.finite_automaton import State
from pyformlang.finite_automaton import Symbol

enfa = EpsilonNFA()
enfa.add_transitions([(0, "abc", 1), (0, "d", 1),         (0, "epsilon", 2)])
enfa.add_start_state(0)
enfa.add_final_state(1)
enfa.write_as_dot("enfa.dot")