from interfaces.automata_editor_schema import parse_symbols, symbols_to_label, export_for_explainer


def test_symbol_roundtrip_with_epsilon():
    syms = parse_symbols("a, ε, b")
    assert syms == ["a", "", "b"]
    assert symbols_to_label(syms) == "a, ε, b"


def test_dfa_export_enforces_single_transition_per_symbol():
    editor = {
        "states": {"q_1": {"accept": False}, "q_2": {"accept": True}},
        "start_state": "q_1",
        "edges": [
            {"id": "e1", "source": "q_1", "target": "q_2", "label": "a"},
            {"id": "e2", "source": "q_1", "target": "q_1", "label": "b"},
            {"id": "e3", "source": "q_2", "target": "q_2", "label": "a,b"},
        ],
    }
    out = export_for_explainer(editor, ["a", "b"], "DFA", allow_eps=False)
    assert out["initial_state"] == "q_1"
    assert out["transitions"]["q_1"]["a"] == "q_2"
    assert out["transitions"]["q_2"]["b"] == "q_2"


def test_nfa_export_allows_epsilon_when_enabled():
    editor = {
        "states": {"q_1": {"accept": False}, "q_2": {"accept": True}},
        "start_state": "q_1",
        "edges": [
            {"id": "e1", "source": "q_1", "target": "q_2", "label": "ε"},
            {"id": "e2", "source": "q_1", "target": "q_1", "label": "a"},
        ],
    }
    out = export_for_explainer(editor, ["a"], "NFA", allow_eps=True)
    assert "" in out["transitions"]["q_1"]
    assert out["transitions"]["q_1"][""] == ["q_2"]
