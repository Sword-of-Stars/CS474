from typing import Dict, List


def parse_symbols(label: str) -> List[str]:
    out: List[str] = []
    for part in (label or "").split(","):
        p = part.strip()
        if not p:
            continue
        if p.lower() in {"epsilon", "eps"} or p == "ε":
            out.append("")
        else:
            out.append(p)
    return out


def symbols_to_label(symbols: List[str]) -> str:
    return ", ".join("ε" if s == "" else s for s in symbols)


def export_for_explainer(editor: Dict, alphabet: List[str], automaton_type: str, allow_eps: bool) -> Dict:
    states = sorted((editor.get("states") or {}).keys())
    if not states:
        raise ValueError("Add at least one state.")
    if not alphabet:
        raise ValueError("Alphabet is required.")
    start_state = editor.get("start_state") or states[0]
    if start_state not in editor["states"]:
        raise ValueError("Start state must be in states.")
    final_states = [s for s in states if editor["states"][s].get("accept")]

    if automaton_type == "DFA":
        transitions = {s: {} for s in states}
        seen = set()
        for e in editor.get("edges", []):
            src = e["source"]
            tgt = e["target"]
            for sym in parse_symbols(e.get("label", "")):
                if sym == "":
                    raise ValueError("DFA cannot use epsilon transitions.")
                key = (src, sym)
                if key in seen:
                    raise ValueError(f"DFA already has a transition for state {src} and symbol {sym}.")
                seen.add(key)
                transitions[src][sym] = tgt
        for s in states:
            for a in alphabet:
                if a not in transitions[s]:
                    raise ValueError(f"Missing transition from {s} on {a}.")
        return {
            "states": states,
            "input_symbols": alphabet,
            "transitions": transitions,
            "initial_state": start_state,
            "final_states": final_states,
        }

    transitions = {s: {} for s in states}
    for e in editor.get("edges", []):
        src = e["source"]
        tgt = e["target"]
        for sym in parse_symbols(e.get("label", "")):
            if sym == "" and not allow_eps:
                raise ValueError("Epsilon transitions are disabled.")
            transitions[src].setdefault(sym, set()).add(tgt)
    transitions_out = {s: {k: sorted(list(v)) for k, v in transitions[s].items()} for s in states}
    return {
        "states": states,
        "input_symbols": alphabet,
        "transitions": transitions_out,
        "initial_state": start_state,
        "final_states": final_states,
    }
