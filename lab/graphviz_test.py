# import graphviz

# dot = graphviz.Digraph()
# dot.node('q0', shape='circle')
# dot.node('q1', shape='circle')
# dot.edge('q0', 'q1', label='1')
# dot.render('output', format='png', view=True)


import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()
G.add_edge("q0", "q1", label="1")
G.add_edge("q2", "q1", label="1")
G.add_edge("q3", "q4", label="29")
G.add_edge("q4", "q1", label="1")
G.add_edge("q5", "q3", label="1")
G.add_edge("q6", "q1", label="1")
G.add_edge("q5", "q2", label="1\nhello\nyou dumba")
G.add_edge("q5", "q6", label="1")
G.add_edge("q2", "q6", label="1")



pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True)
edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, rotate=True, label_pos=0.1)
plt.show()
