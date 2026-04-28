from graphviz import Digraph

def visualize_tm_graphviz(transitions, filename='tm_graph'):
    dot = Digraph(format='pdf')
    
    # Global graph settings for spacing and aesthetics
    dot.attr(ranksep='1.5', nodesep='1.0')  # more space between rows/columns
    dot.attr('node', shape='circle', fontsize='14', width='0.5', fixedsize='false')
    dot.attr('edge', fontsize='12', penwidth='1.2')

    for src, symbol_map in transitions.items():
        dot.node(src)  # make sure all states are defined
        for read, (dst, write, move) in symbol_map.items():
            label = f"  {read}→{write},{move}"
            dot.edge(src, dst, label=label)

    dot.render(filename, view=True)

# Example usage:
transitions = {
    'q0': {
        '0': ('q_accept', '1', 'N'),
        '1': ('q0', '0', 'R'),
        '_': ('q_accept', '1', 'N'),
    }
}

visualize_tm_graphviz(transitions)
