def transitions_to_latex(transitions: dict) -> str:
    states = list(transitions.keys())
    all_targets = set()
    for state_transitions in transitions.values():
        for target, _, _ in state_transitions.values():
            all_targets.add(target)
    all_states = list(set(states) | all_targets)

    state_positions = {
        state: f"({i * 3}, 0)" for i, state in enumerate(all_states)
    }

    latex = []
    latex.append(r"\documentclass{article}")
    latex.append(r"\usepackage{tikz}")
    latex.append(r"\usetikzlibrary{automata, positioning}")
    latex.append(r"\begin{document}")
    latex.append(r"\begin{tikzpicture}[shorten >=1pt, node distance=3cm, on grid, auto]")

    # Draw states
    for i, state in enumerate(all_states):
        style = "state"
        if state == 'q0':
            style += ", initial"
        if 'accept' in state or 'final' in state:
            style += ", accepting"
        latex.append(fr"\node[{style}] ({state}) at {state_positions[state]} {{$\mathsf{{{state}}}$}};")

    # Draw transitions
    for src, symbol_map in transitions.items():
        for read_symbol, (dst, write_symbol, direction) in symbol_map.items():
            label = f"{read_symbol} → {write_symbol}, {direction}"
            if src == dst:
                # loop
                latex.append(fr"\path[->] ({src}) edge[loop above] node {{$\mathsf{{{label}}}$}} ({dst});")
            else:
                latex.append(fr"\path[->] ({src}) edge node {{$\mathsf{{{label}}}$}} ({dst});")

    latex.append(r"\end{tikzpicture}")
    latex.append(r"\end{document}")

    return "\n".join(latex)

transitions = {
    'q0': {
        '0': ('q_accept', '1', 'N'),
        '1': ('q0', '0', 'R'),
        '_': ('q_accept', '1', 'N'),
    }
}

latex_code = transitions_to_latex(transitions)

with open("tm_diagram.tex", "w", encoding="utf-8") as f:
    f.write(latex_code)


