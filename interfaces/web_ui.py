import io
import json
import base64
import os
import re
import math
import sys
import pathlib
import importlib.util
from argparse import Namespace

import streamlit as st
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

try:
    from interfaces.automata_editor_component import automata_editor_component
except Exception:
    try:
        from automata_editor_component import automata_editor_component
    except Exception:
        _comp_file = _THIS_DIR / "automata_editor_component.py"
        if _comp_file.exists():
            spec = importlib.util.spec_from_file_location("automata_editor_component", str(_comp_file))
            if spec and spec.loader:
                _mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_mod)
                automata_editor_component = _mod.automata_editor_component
            else:
                automata_editor_component = None
        else:
            automata_editor_component = None

try:
    from streamlit_flow import streamlit_flow
    from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
    from streamlit_flow.state import StreamlitFlowState
    STREAMLIT_FLOW_AVAILABLE = True
except Exception:
    STREAMLIT_FLOW_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers (module-level so all functions can use them)
# ─────────────────────────────────────────────────────────────────────────────

def _point_segment_distance(px, py, ax, ay, bx, by):
    """Perpendicular distance from point (px,py) to segment (ax,ay)→(bx,by)."""
    abx, aby = bx - ax, by - ay
    ab2 = abx * abx + aby * aby
    if ab2 <= 1e-9:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / ab2))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def _segments_intersect(a1, a2, b1, b2):
    def _cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    d1, d2 = _cross(b1, b2, a1), _cross(b1, b2, a2)
    d3, d4 = _cross(a1, a2, b1), _cross(a1, a2, b2)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


# ─────────────────────────────────────────────────────────────────────────────
# streamlit-flow wrappers
# ─────────────────────────────────────────────────────────────────────────────

def _streamlit_flow_safe(key, state):
    def _invoke_flow(flow_key, flow_state):
        try:
            return streamlit_flow(
                flow_key,
                flow_state,
                fit_view=False,
                allow_new_edges=True,
                show_controls=True,
            )
        except TypeError:
            return streamlit_flow(flow_key, flow_state, fit_view=False)

    def _coerce_component_value(value):
        if not isinstance(value, dict):
            return value
        nodes = value.get("nodes")
        if not isinstance(nodes, list):
            return value
        changed = False
        out_nodes = []
        for node in nodes:
            if not isinstance(node, dict):
                out_nodes.append(node)
                continue
            new_node = dict(node)
            position = new_node.get("position")
            if isinstance(position, (list, tuple)) and len(position) >= 2:
                new_node["position"] = {"x": position[0], "y": position[1]}
                changed = True
            elif isinstance(position, dict):
                new_node["position"] = {"x": position.get("x", 0), "y": position.get("y", 0)}
            elif "pos" in new_node and isinstance(new_node.get("pos"), (list, tuple)) and len(new_node["pos"]) >= 2:
                p = new_node["pos"]
                new_node["position"] = {"x": p[0], "y": p[1]}
                changed = True
            out_nodes.append(new_node)
        if not changed:
            return value
        out = dict(value)
        out["nodes"] = out_nodes
        return out

    def _normalize_state_for_flow(raw_state):
        def _safe_pos(pos_raw, idx):
            default_x = 160 + 130 * idx
            default_y = 160 + 20 * idx
            x, y = default_x, default_y
            if isinstance(pos_raw, dict):
                x = pos_raw.get("x", default_x)
                y = pos_raw.get("y", default_y)
            elif isinstance(pos_raw, (list, tuple)) and len(pos_raw) >= 2:
                x, y = pos_raw[0], pos_raw[1]
            try:
                x, y = float(x), float(y)
            except Exception:
                return [default_x, default_y]
            if not (math.isfinite(x) and math.isfinite(y)):
                return [default_x, default_y]
            if abs(x) > 5000 or abs(y) > 5000:
                return [default_x, default_y]
            return [x, y]

        if isinstance(raw_state, StreamlitFlowState):
            raw_nodes = getattr(raw_state, "nodes", []) or []
            raw_edges = getattr(raw_state, "edges", []) or []
        else:
            raw_nodes = []
            raw_edges = []
            if isinstance(raw_state, dict):
                raw_nodes = raw_state.get("nodes", []) or []
                raw_edges = raw_state.get("edges", []) or []
            else:
                raw_nodes = getattr(raw_state, "nodes", []) or []
                raw_edges = getattr(raw_state, "edges", []) or []

        nodes = []
        for idx, node in enumerate(raw_nodes):
            if isinstance(node, StreamlitFlowNode):
                pos = _safe_pos(getattr(node, "pos", None) or getattr(node, "position", None) or [0, 0], idx)
                nodes.append(StreamlitFlowNode(
                    id=getattr(node, "id", None),
                    data=getattr(node, "data", None) or {},
                    pos=pos,
                    style=getattr(node, "style", None),
                ))
            elif isinstance(node, dict):
                pos = _safe_pos(node.get("pos") or node.get("position") or [0, 0], idx)
                nodes.append(StreamlitFlowNode(
                    id=node.get("id"), data=node.get("data") or {}, pos=pos, style=node.get("style"),
                ))
            else:
                nodes.append(node)

        edges = []
        for edge in raw_edges:
            if isinstance(edge, StreamlitFlowEdge):
                edges.append(edge)
            elif isinstance(edge, dict):
                edge_obj = StreamlitFlowEdge(
                    id=edge.get("id"), source=edge.get("source"), target=edge.get("target"),
                    label=edge.get("label"), data=edge.get("data"), type=edge.get("type"),
                    style=edge.get("style"), labelStyle=edge.get("labelStyle"), labelBgStyle=edge.get("labelBgStyle"),
                )
                edge_color = "#111111"
                try:
                    if isinstance(edge.get("style"), dict):
                        edge_color = str(edge["style"].get("stroke") or edge_color)
                except Exception:
                    pass
                _edge_force_directional(edge_obj, edge_color)
                edges.append(edge_obj)
            else:
                edges.append(edge)
        return StreamlitFlowState(nodes=nodes, edges=edges)

    state = _normalize_state_for_flow(state)
    if key in st.session_state:
        st.session_state[key] = _coerce_component_value(st.session_state.get(key))
    try:
        return _invoke_flow(key, state)
    except AttributeError as e:
        if "list' object has no attribute 'get'" in str(e):
            if key in st.session_state:
                del st.session_state[key]
            recover_count_key = f"__flow_recover_count_{key}"
            recover_idx = int(st.session_state.get(recover_count_key, 0)) + 1
            st.session_state[recover_count_key] = recover_idx
            return _invoke_flow(f"{key}__recover_{recover_idx}", state)
        raise


def _reset_flow_component_state(flow_key: str):
    if flow_key in st.session_state:
        del st.session_state[flow_key]


def _bump_flow_key(version_key: str):
    st.session_state[version_key] = int(st.session_state.get(version_key, 0)) + 1


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interfaces.auto_explainer_cli import (
    handle_dfa_min,
    handle_nfa_eps,
    handle_cnf,
    handle_tm,
)
try:
    from interfaces.automata_editor_schema import (
        parse_symbols as _schema_parse_symbols,
        symbols_to_label as _schema_symbols_to_label,
        export_for_explainer as _schema_export_for_explainer,
    )
except Exception:
    def _schema_parse_symbols(label: str):
        out = []
        for part in (label or "").split(","):
            p = part.strip()
            if not p:
                continue
            if p.lower() in {"epsilon", "eps"} or p == "ε":
                out.append("")
            else:
                out.append(p)
        return out

    def _schema_symbols_to_label(symbols):
        return ", ".join("ε" if s == "" else s for s in (symbols or []))

    def _schema_export_for_explainer(editor: dict, alphabet: list, automaton_type: str, allow_eps: bool):
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
                src, tgt = e["source"], e["target"]
                for sym in _schema_parse_symbols(e.get("label", "")):
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
                "states": states, "input_symbols": alphabet, "transitions": transitions,
                "initial_state": start_state, "final_states": final_states,
            }

        transitions = {s: {} for s in states}
        for e in editor.get("edges", []):
            src, tgt = e["source"], e["target"]
            for sym in _schema_parse_symbols(e.get("label", "")):
                if sym == "" and not allow_eps:
                    raise ValueError("Epsilon transitions are disabled.")
                transitions[src].setdefault(sym, set()).add(tgt)
        return {
            "states": states, "input_symbols": alphabet,
            "transitions": {s: {k: sorted(list(v)) for k, v in transitions[s].items()} for s in states},
            "initial_state": start_state, "final_states": final_states,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Page config & global CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="CS474 Auto-Explainers", layout="wide")

st.markdown("""
<style>
/* Smooth edge rendering – no flicker */
.react-flow__edge-path,
.react-flow__edge-text,
.react-flow__edge-textbg { transition: none !important; animation: none !important; }

/* Tighter sidebar */
section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* Monospace for JSON areas */
textarea[data-testid="stTextArea"] { font-family: "JetBrains Mono", monospace; font-size: 12px; }

/* Make flow canvas taller */
.react-flow { min-height: 460px; }

/* Style the legend pills */
.legend-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f8f9fa; border: 1px solid #dee2e6;
    border-radius: 20px; padding: 3px 10px; font-size: 12px;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

st.title("CS474 Auto‑Explainers")
st.caption("Generate step-by-step PDFs for DFA Minimisation · NFA ε-removal · CNF conversion · Turing Machines")

OUT_BASE = os.environ.get("EXPLAINER_OUT", os.path.join(os.getcwd(), "out"))
os.makedirs(OUT_BASE, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Visual-editor node / edge styling
# ─────────────────────────────────────────────────────────────────────────────

# Vibrant, accessible colour palette – index 0 is the "default" colour.
_SYMBOL_PALETTE = [
    "#111111",  # default / black
    "#e85d04",  # vivid orange
    "#d62828",  # red
    "#1d6fa3",  # blue
    "#2d6a4f",  # green
    "#6a0572",  # purple
    "#b5838d",  # rose
    "#457b9d",  # steel blue
]


def _editor_symbol_colors(alphabet: list) -> dict:
    return {a: _SYMBOL_PALETTE[(i + 1) % len(_SYMBOL_PALETTE)] for i, a in enumerate(alphabet or [])}


def _editor_style_node(is_accept: bool) -> dict:
    """Return CSS-in-JS style for a state node circle."""
    base = {
        "borderRadius": "50%",
        "width": 68,
        "height": 68,
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "fontSize": "15px",
        "fontWeight": "700",
        "fontFamily": "'Courier New', monospace",
        "border": "2.5px solid #111111",
        "background": "#ffffff",
        "color": "#111111",
        "boxShadow": "0 2px 6px rgba(0,0,0,0.12)",
        "cursor": "grab",
    }
    if is_accept:
        # Double-ring: inner shadow mimics the second circle of an accept state
        base["boxShadow"] = (
            "inset 0 0 0 5px #ffffff, "
            "inset 0 0 0 8px #111111, "
            "0 2px 8px rgba(0,0,0,0.18)"
        )
        base["background"] = "#f0f4ff"
    return base


def _editor_edge_style(label: str, color_map: dict) -> tuple:
    """Return (edge_style, label_style, label_bg_style) for a given label."""
    symbols = _schema_parse_symbols(label)
    is_eps = bool(symbols) and symbols[0] == ""

    if is_eps:
        color = "#6c757d"
        stroke_dash = "7 4"
    elif symbols:
        color = color_map.get(symbols[0], _SYMBOL_PALETTE[0])
        stroke_dash = None
    else:
        color = _SYMBOL_PALETTE[0]
        stroke_dash = None

    edge_style: dict = {"stroke": color, "strokeWidth": 2.5}
    if stroke_dash:
        edge_style["strokeDasharray"] = stroke_dash

    label_style = {"fontSize": 13, "fontWeight": "700", "fill": color}
    label_bg = {
        "fill": "#ffffff", "fillOpacity": 0.92,
        "stroke": color, "strokeWidth": 1, "rx": 4, "ry": 4,
    }
    return edge_style, label_style, label_bg


def _edge_force_directional(edge_obj, color: str):
    marker = {"type": "arrowclosed", "color": color, "width": 18, "height": 18}
    try:
        edge_obj.arrowHeadType = "arrowclosed"
    except Exception:
        pass
    try:
        edge_obj.markerEndType = "arrowclosed"
    except Exception:
        pass
    try:
        edge_obj.markerEnd = marker
    except Exception:
        pass
    try:
        if getattr(edge_obj, "data", None) is None:
            edge_obj.data = {}
        edge_obj.data["markerEnd"] = marker
        edge_obj.data["arrowHeadType"] = "arrowclosed"
        edge_obj.data["markerEndType"] = "arrowclosed"
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Core: convert editor dict → StreamlitFlowState
# ─────────────────────────────────────────────────────────────────────────────

def _editor_to_flow_state(editor: dict, alphabet: list) -> StreamlitFlowState:
    """
    Render the internal editor representation as a React Flow graph.

    Improvements over the baseline:
    • Self-loops are rendered as visible arcs above the originating state.
    • Bidirectional edges (A→B and B→A) are curved in opposite directions so
      they do not overlap.
    • When a direct straight line would pass through another state, curvature
      is automatically increased to route around it.
    • Multiple parallel edges between the same pair are fanned out.
    • Every edge has an arrowhead via markerEnd.
    """
    nodes: list = []
    edges: list = []
    states: dict = editor.get("states") or {}
    start_state: str = editor.get("start_state") or ""
    color_map = _editor_symbol_colors(alphabet)

    # Helper: centre coordinates of a state's circle (pos is top-left of 68×68 div)
    def _cx(sid: str) -> float:
        return float(states[sid].get("x", 140)) + 34.0

    def _cy(sid: str) -> float:
        return float(states[sid].get("y", 140)) + 34.0

    # ── Build state nodes ────────────────────────────────────────────────────
    for sid in _editor_state_ids(editor):
        s = states[sid]
        nodes.append(StreamlitFlowNode(
            id=sid,
            data={"label": _editor_make_label(sid)},
            pos=[float(s.get("x", 140)), float(s.get("y", 140))],
            style=_editor_style_node(bool(s.get("accept", False))),
        ))

    # ── Start-state arrow ────────────────────────────────────────────────────
    if start_state and start_state in states:
        sp = states[start_state]
        anchor_id = "__start__"
        sx_node = float(sp.get("x", 140))
        sy_node = float(sp.get("y", 140))

        nodes.append(StreamlitFlowNode(
            id=anchor_id,
            data={"label": ""},
            pos=[max(sx_node - 80, 5), sy_node + 17],
            style={
                "width": 1, "height": 1, "opacity": 0,
                "background": "rgba(0,0,0,0)", "border": "none",
            },
        ))
        start_edge = StreamlitFlowEdge(
            id=f"{anchor_id}→{start_state}",
            source=anchor_id,
            target=start_state,
            label="",
            type="straight",
            style={"stroke": "#111111", "strokeWidth": 2.8, "strokeLinecap": "round"},
            data={
                "markerEnd": {"type": "arrowclosed", "color": "#111111", "width": 20, "height": 20},
                "sourceHandle": "right",
                "targetHandle": "left",
            },
            labelStyle={"fontSize": 1},
            labelBgStyle={"fill": "#ffffff", "fillOpacity": 0},
        )
        _edge_force_directional(start_edge, "#111111")
        edges.append(start_edge)

    # ── Analyse edge set ─────────────────────────────────────────────────────
    edge_list: list = editor.get("edges") or []

    # Count how many edges share each directed pair
    pair_counts: dict = {}
    for e in edge_list:
        k = (e["source"], e["target"])
        pair_counts[k] = pair_counts.get(k, 0) + 1

    pair_cursor: dict = {}   # how many edges we've already processed for each pair

    for e in edge_list:
        src: str = e["source"]
        tgt: str = e["target"]
        raw_label: str = e.get("label", "")
        display_label: str = _format_symbols_for_label(raw_label)
        edge_style, label_style, label_bg = _editor_edge_style(raw_label, color_map)
        stroke_color: str = edge_style.get("stroke", "#111111")

        pair_key = (src, tgt)
        lane: int = pair_cursor.get(pair_key, 0)
        pair_cursor[pair_key] = lane + 1

        marker_end = {
            "type": "arrowclosed",
            "color": stroke_color,
            "width": 18,
            "height": 18,
        }

        # ── Self-loop ────────────────────────────────────────────────────────
        if src == tgt:
            # Use smoothstep with same source/target handle on the TOP of the
            # node; 'offset' controls how far the loop arcs upward.
            loop_offset = max(72, 72 + lane * 22)
            loop_edge = StreamlitFlowEdge(
                id=e["id"],
                source=src,
                target=tgt,
                label=display_label,
                type="smoothstep",
                style={**edge_style, "strokeLinecap": "round"},
                labelStyle=label_style,
                labelBgStyle=label_bg,
                data={
                    "markerEnd": marker_end,
                    "sourceHandle": "right",
                    "targetHandle": "right",
                    "pathOptions": {"borderRadius": 999, "offset": loop_offset},
                },
            )
            _edge_force_directional(loop_edge, stroke_color)
            edges.append(loop_edge)
            continue

        # ── Regular (non-loop) edge ──────────────────────────────────────────
        sx, sy = _cx(src), _cy(src)
        tx, ty = _cx(tgt), _cy(tgt)

        # If user manually set geometry, honor it.
        manual_type = str(e.get("edge_type") or "").strip().lower()
        manual_src_handle = str(e.get("source_handle") or "").strip().lower()
        manual_tgt_handle = str(e.get("target_handle") or "").strip().lower()
        if manual_type in {"default", "smoothstep", "straight"}:
            data = {"markerEnd": marker_end}
            if manual_src_handle in {"left", "right", "top", "bottom"}:
                data["sourceHandle"] = manual_src_handle
            if manual_tgt_handle in {"left", "right", "top", "bottom"}:
                data["targetHandle"] = manual_tgt_handle
            route_offset = int(e.get("route_offset") or 0)
            if manual_type == "smoothstep":
                data["pathOptions"] = {"borderRadius": 14, "offset": max(0, route_offset)}
            elif manual_type == "default":
                curvature = float(e.get("curvature", 0.2))
                data["pathOptions"] = {"curvature": max(0.0, min(1.2, curvature))}

            manual_edge = StreamlitFlowEdge(
                    id=e["id"],
                    source=src,
                    target=tgt,
                    label=display_label,
                    type=manual_type,
                    style={**edge_style, "strokeLinecap": "round"},
                    labelStyle=label_style,
                    labelBgStyle=label_bg,
                    data=data,
                )
            _edge_force_directional(manual_edge, stroke_color)
            edges.append(manual_edge)
            continue

        # 1. Check for states that block the straight-line path
        max_obstruction: float = 0.0
        for oid in states:
            if oid in (src, tgt):
                continue
            ox, oy = _cx(oid), _cy(oid)
            d = _point_segment_distance(ox, oy, sx, sy, tx, ty)
            if d < 80:
                # Obstruction strength 0→1 as distance goes 80→0
                max_obstruction = max(max_obstruction, (80.0 - d) / 80.0)

        # 2. Determine curvature
        reverse_exists: bool = (tgt, src) in pair_counts
        total_in_pair: int = pair_counts.get(pair_key, 1)

        edge_type = "default"
        data = {"markerEnd": marker_end}
        if reverse_exists:
            # Separate A→B from B→A by curving in opposite directions.
            # lane 0 → curve "above" the midpoint; lane 1+ → progressively more.
            curvature = 0.45 + lane * 0.20
            edge_type = "smoothstep"
            data.update({"sourceHandle": "right", "targetHandle": "left"})
            data["pathOptions"] = {"borderRadius": 14, "offset": 56 + lane * 24}
        elif total_in_pair > 1:
            # Fan out multiple edges between the same pair.
            curvature = 0.20 + lane * 0.30
            edge_type = "smoothstep"
            data.update({"sourceHandle": "right", "targetHandle": "left"})
            data["pathOptions"] = {"borderRadius": 14, "offset": 44 + lane * 20}
        elif max_obstruction > 0.0:
            # Route around blocking states.
            curvature = 0.35 + max_obstruction * 0.45
            edge_type = "smoothstep"
            data.update({"sourceHandle": "right", "targetHandle": "left"})
            data["pathOptions"] = {"borderRadius": 14, "offset": int(52 + 64 * max_obstruction)}
        else:
            curvature = 0.15   # gentle default — barely perceptible curve
            data["pathOptions"] = {"curvature": curvature}

        auto_edge = StreamlitFlowEdge(
            id=e["id"],
            source=src,
            target=tgt,
            label=display_label,
            type=edge_type,
            style={**edge_style, "strokeLinecap": "round"},
            labelStyle=label_style,
            labelBgStyle=label_bg,
            data=data,
        )
        _edge_force_directional(auto_edge, stroke_color)
        edges.append(auto_edge)

    return StreamlitFlowState(nodes=nodes, edges=edges)


# ─────────────────────────────────────────────────────────────────────────────
# Editor state helpers
# ─────────────────────────────────────────────────────────────────────────────

def _editor_new_state() -> dict:
    return {"states": {}, "start_state": "", "edges": []}


def _editor_state_ids(editor: dict) -> list:
    return sorted(
        (editor.get("states") or {}).keys(),
        key=lambda s: (int(s.split("_")[1]) if s.startswith("q_") and s.split("_")[1].isdigit() else s),
    )


def _editor_make_label(state_id: str) -> str:
    if state_id.startswith("q_") and state_id.split("_", 1)[1].isdigit():
        return _to_subscript(int(state_id.split("_", 1)[1]))
    return state_id


def _editor_edge_symbols(label: str) -> list:
    return _schema_parse_symbols(label)


def _editor_symbols_to_label(symbols: list) -> str:
    return _schema_symbols_to_label(symbols)


def _editor_sync_positions_from_flow(editor: dict, flow_state):
    states = editor.get("states") or {}
    nodes, _ = _flow_get_nodes_edges(flow_state)
    for n in nodes:
        nid = _node_id(n)
        if nid in states:
            x, y = _node_pos(n)
            if math.isfinite(x) and math.isfinite(y) and not (abs(x) < 1 and abs(y) < 1):
                states[nid]["x"] = float(x)
                states[nid]["y"] = float(y)


def _editor_sync_new_edges_from_flow(editor: dict, flow_state):
    known_ids = {e["id"] for e in (editor.get("edges") or [])}
    existing_pairs = {(e["source"], e["target"]) for e in (editor.get("edges") or [])}
    _, flow_edges = _flow_get_nodes_edges(flow_state)
    for e in flow_edges:
        src, tgt = _edge_source(e), _edge_target(e)
        eid = _edge_id(e)
        if not src or not tgt or src == "__start__":
            continue
        if src not in (editor.get("states") or {}) or tgt not in (editor.get("states") or {}):
            continue
        if eid and eid in known_ids:
            continue
        if (src, tgt) in existing_pairs:
            continue
        new_id = f"e_{len(editor['edges'])+1}_{src}_{tgt}"
        is_loop = src == tgt
        editor["edges"].append(
            {
                "id": new_id,
                "source": src,
                "target": tgt,
                "label": "",
                "edge_type": "smoothstep" if is_loop else "default",
                "source_handle": "right",
                "target_handle": "right" if is_loop else "left",
                "route_offset": 72 if is_loop else 0,
            }
        )
        known_ids.add(new_id)
        existing_pairs.add((src, tgt))


def _editor_remove_selected(editor: dict, flow_state):
    selected_nodes = set(_flow_selected_nodes(flow_state) or [])
    selected_edges = set(_flow_selected_edges(flow_state) or [])
    if selected_nodes:
        for nid in selected_nodes:
            editor["states"].pop(nid, None)
        if editor.get("start_state") in selected_nodes:
            editor["start_state"] = ""
        editor["edges"] = [
            e for e in editor.get("edges", [])
            if e["source"] not in selected_nodes and e["target"] not in selected_nodes
        ]
    if selected_edges:
        editor["edges"] = [e for e in editor.get("edges", []) if e["id"] not in selected_edges]


def _editor_auto_tidy_layout(editor: dict):
    state_ids = _editor_state_ids(editor)
    if not state_ids:
        return
    start = editor.get("start_state") if editor.get("start_state") in state_ids else state_ids[0]
    adj = {sid: [] for sid in state_ids}
    for e in editor.get("edges", []):
        src = e.get("source")
        tgt = e.get("target")
        if src in adj and tgt in adj and tgt not in adj[src]:
            adj[src].append(tgt)

    depth = {start: 0}
    q = [start]
    while q:
        cur = q.pop(0)
        for nxt in adj.get(cur, []):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1
                q.append(nxt)

    max_depth = max(depth.values()) if depth else 0
    unattached = [sid for sid in state_ids if sid not in depth]
    for idx, sid in enumerate(unattached):
        depth[sid] = max_depth + 1 + (idx // 4)

    layers = {}
    for sid in state_ids:
        d = depth.get(sid, 0)
        layers.setdefault(d, []).append(sid)

    x0 = 140
    y0 = 140
    x_step = 220
    y_step = 140
    for d in sorted(layers.keys()):
        layer = sorted(layers[d], key=lambda s: (s.startswith("q_"), s))
        for idx, sid in enumerate(layer):
            editor["states"][sid]["x"] = float(x0 + d * x_step)
            editor["states"][sid]["y"] = float(y0 + idx * y_step)


def _editor_dfa_conflicts(editor: dict):
    conflicts = []
    table = {}
    for e in editor.get("edges", []):
        src = e.get("source")
        tgt = e.get("target")
        for sym in _schema_parse_symbols(e.get("label", "")):
            key = (src, sym)
            table.setdefault(key, set()).add(tgt)
    for (src, sym), tgts in sorted(table.items()):
        if len(tgts) > 1:
            sym_disp = "ε" if sym == "" else sym
            conflicts.append(f"{src} has nondeterministic transition on '{sym_disp}' to {sorted(tgts)}")
    return conflicts


def _editor_import_json_to_editor(raw_text: str, automaton_type: str):
    obj = json.loads(raw_text)
    editor = _editor_new_state()
    alphabet = []

    # Schema A: explainer format {"states":[], "transitions":{}, "initial_state":...}
    if "states" in obj and "transitions" in obj and "initial_state" in obj:
        states = [str(s) for s in obj.get("states", [])]
        alphabet = [str(a) for a in obj.get("input_symbols", [])]
        for i, s in enumerate(states):
            editor["states"][s] = {
                "x": 160 + 130 * i, "y": 180,
                "accept": str(s) in {str(x) for x in obj.get("final_states", [])},
            }
        editor["start_state"] = str(obj.get("initial_state", ""))
        trans = obj.get("transitions", {})
        eid = 1
        if automaton_type == "DFA":
            for s, by_sym in trans.items():
                for sym, tgt in (by_sym or {}).items():
                    editor["edges"].append({"id": f"e_{eid}", "source": str(s), "target": str(tgt),
                                            "label": _editor_symbols_to_label([str(sym)])})
                    eid += 1
        else:
            for s, by_sym in trans.items():
                for sym, tgts in (by_sym or {}).items():
                    for tgt in (tgts or []):
                        label = _editor_symbols_to_label(["" if sym == "" else str(sym)])
                        editor["edges"].append({"id": f"e_{eid}", "source": str(s), "target": str(tgt), "label": label})
                        eid += 1
        layout = ((obj.get("metadata") or {}).get("layout") or {})
        for sid, pos in layout.items():
            if sid in editor["states"] and isinstance(pos, dict):
                editor["states"][sid]["x"] = float(pos.get("x", editor["states"][sid]["x"]))
                editor["states"][sid]["y"] = float(pos.get("y", editor["states"][sid]["y"]))
        return editor, alphabet

    # Schema B: {"type":..., "states":[], "transitions":[], "startState":...}
    if "type" in obj and "states" in obj and "transitions" in obj:
        states = [str(s) for s in obj.get("states", [])]
        alphabet = [str(a) for a in obj.get("alphabet", [])]
        accepts = {str(s) for s in obj.get("acceptStates", [])}
        for i, s in enumerate(states):
            editor["states"][s] = {"x": 160 + 130 * i, "y": 180, "accept": s in accepts}
        editor["start_state"] = str(obj.get("startState", ""))
        eid = 1
        for t in obj.get("transitions", []):
            src = str(t.get("from"))
            to_val = t.get("to")
            tgts = to_val if isinstance(to_val, list) else [to_val]
            sym = t.get("symbol", "")
            for tgt in tgts:
                label = _editor_symbols_to_label(["" if str(sym) in {"", "ε", "epsilon", "eps"} else str(sym)])
                editor["edges"].append({"id": f"e_{eid}", "source": src, "target": str(tgt), "label": label})
                eid += 1
        return editor, alphabet

    raise ValueError("Unsupported JSON schema for automaton import.")


def _editor_export_for_explainer(editor: dict, alphabet: list, automaton_type: str, allow_eps: bool):
    return _schema_export_for_explainer(editor, alphabet, automaton_type, allow_eps)


# ─────────────────────────────────────────────────────────────────────────────
# Flow-state accessors (handle both dict and object representations)
# ─────────────────────────────────────────────────────────────────────────────

def _flow_get_nodes_edges(flow_state):
    if flow_state is None:
        return [], []
    nodes = getattr(flow_state, "nodes", None)
    edges = getattr(flow_state, "edges", None)
    if nodes is None and isinstance(flow_state, dict):
        nodes = flow_state.get("nodes", [])
        edges = flow_state.get("edges", [])
    return nodes or [], edges or []


def _flow_user_node_count(flow_state):
    nodes, _ = _flow_get_nodes_edges(flow_state)
    return len([n for n in nodes if _node_id(n) != "__start__"])


def _flow_user_node_ids(flow_state):
    nodes, _ = _flow_get_nodes_edges(flow_state)
    return sorted(str(_node_id(n)) for n in nodes if _node_id(n) and _node_id(n) != "__start__")


def _flow_positions_collapsed(flow_state):
    nodes, _ = _flow_get_nodes_edges(flow_state)
    pts = set()
    for n in nodes:
        if _node_id(n) == "__start__":
            continue
        x, y = _node_pos(n)
        pts.add((round(float(x), 1), round(float(y), 1)))
    return len(pts) == 1 if len(pts) >= 1 else False


def _flow_selected_edges(flow_state):
    if flow_state is None:
        return []
    for attr in ("selected_edges", "selectedEdges", "selected_edges_ids"):
        val = getattr(flow_state, attr, None) or (flow_state.get(attr) if isinstance(flow_state, dict) else None)
        if val is not None:
            return val
    return []


def _flow_selected_nodes(flow_state):
    if flow_state is None:
        return []
    for attr in ("selected_nodes", "selectedNodes", "selected_nodes_ids"):
        val = getattr(flow_state, attr, None) or (flow_state.get(attr) if isinstance(flow_state, dict) else None)
        if val is not None:
            return val
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Low-level node / edge accessors
# ─────────────────────────────────────────────────────────────────────────────

def _node_id(node):
    return node.get("id") if isinstance(node, dict) else getattr(node, "id", "")


def _edge_id(edge):
    return edge.get("id") if isinstance(edge, dict) else getattr(edge, "id", "")


def _edge_source(edge):
    return edge.get("source") if isinstance(edge, dict) else getattr(edge, "source", "")


def _edge_target(edge):
    return edge.get("target") if isinstance(edge, dict) else getattr(edge, "target", "")


def _edge_label(edge):
    if edge is None:
        return ""
    if isinstance(edge, dict):
        return str(edge.get("label") or (edge.get("data") or {}).get("label") or "").strip()
    if hasattr(edge, "label") and edge.label is not None:
        return str(edge.label).strip()
    if hasattr(edge, "data") and edge.data:
        return str(edge.data.get("label") or "").strip()
    return ""


def _node_pos(node):
    pos = (node.get("pos") or node.get("position") or [0, 0]) if isinstance(node, dict) \
        else (getattr(node, "pos", None) or getattr(node, "position", None) or [0, 0])
    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
        return [float(pos[0]), float(pos[1])]
    if isinstance(pos, dict):
        return [float(pos.get("x", 0)), float(pos.get("y", 0))]
    return [0.0, 0.0]


def _set_node_pos(node, pos):
    value = [float(pos[0]), float(pos[1])]
    if isinstance(node, dict):
        node["pos"] = value
    elif hasattr(node, "pos"):
        node.pos = value
    elif hasattr(node, "position"):
        node.position = value


# ─────────────────────────────────────────────────────────────────────────────
# Misc helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_subscript(n: int) -> str:
    subs = str(n).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))
    return f"q{subs}"


def _next_state_id(nodes) -> str:
    max_n = 0
    for n in nodes:
        nid = n.get("id") if isinstance(n, dict) else n.id
        if nid and nid.startswith("q_"):
            try:
                max_n = max(max_n, int(nid.split("_", 1)[1]))
            except Exception:
                pass
    return f"q_{max_n + 1}"


def _split_csv(text: str) -> list:
    return [t.strip() for t in (text or "").split(",") if t.strip()]


def _parse_cfg_text(text: str) -> dict:
    grammar: dict = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "->" not in line:
            raise ValueError(f"Missing '->' in line: {line}")
        lhs, rhs = [p.strip() for p in line.split("->", 1)]
        if not lhs:
            raise ValueError(f"Missing LHS in line: {line}")
        alts = [a.strip() for a in rhs.split("|") if a.strip()]
        if not alts:
            raise ValueError(f"Missing RHS in line: {line}")
        grammar[lhs] = alts
    return grammar


def _format_symbols_for_label(label: str) -> str:
    symbols = _schema_parse_symbols(label)
    if not symbols:
        return ""
    return ", ".join("ε" if s == "" else s for s in symbols)


def _split_symbols(label: str) -> list:
    return _schema_parse_symbols(label)


# ─────────────────────────────────────────────────────────────────────────────
# PDF helpers
# ─────────────────────────────────────────────────────────────────────────────

def _latest_pdf_under(path: str):
    if not os.path.exists(path):
        return None
    newest, newest_mtime = None, -1
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".pdf"):
                p = os.path.join(root, f)
                m = os.path.getmtime(p)
                if m > newest_mtime:
                    newest, newest_mtime = p, m
    return newest


def _read_preset_json(name: str):
    try:
        base = os.path.join(os.path.dirname(__file__), "presets")
        with open(os.path.join(base, name), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def download_file_button(label: str, file_path: str):
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        st.download_button(label, data=data, file_name=os.path.basename(file_path), mime="application/pdf")
    else:
        st.info("No PDF available yet.")


def preview_pdf_inline(file_path: str, height: int = 820):
    if not (file_path and os.path.exists(file_path)):
        st.info("No PDF to preview.")
        return
    try:
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="{height}px" style="border:1px solid #dee2e6; border-radius:6px;"></iframe>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Could not preview PDF: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# JSON input widget (file upload or paste)
# ─────────────────────────────────────────────────────────────────────────────

def _json_text_or_file(kind: str, preset_filename: str, upload_label: str):
    with st.expander("💡 Getting JSON from a textbook photo or scan", expanded=False):
        st.markdown(
            f"Upload your problem image to ChatGPT (or any multimodal model) with this prompt:\n\n"
            f"```\nExtract the automaton/grammar/TM from this image into valid JSON matching the "
            f"{kind.upper()} schema shown on this page. Return JSON only, no extra text.\n```"
        )
    mode = st.radio(f"{kind.upper()} Source", ["Upload file", "Paste JSON"], horizontal=True, key=f"{kind}_src")
    file_path = None
    text_used = None

    if mode == "Upload file":
        up = st.file_uploader(upload_label, type=["json"], key=f"{kind}_uploader")
        if up:
            tmp_path = os.path.join(OUT_BASE, f"{kind}_input.json")
            with open(tmp_path, "wb") as f:
                f.write(up.read())
            file_path = tmp_path
    else:
        state_key = f"{kind}_text"
        if not st.session_state.get(state_key):
            sample = _read_preset_json(preset_filename)
            if sample:
                st.session_state[state_key] = sample
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text_area("Paste JSON here", height=200, key=state_key)
        with col2:
            st.write("")
            st.write("")
            if st.button("Load Example", key=f"{kind}_load_example"):
                sample = _read_preset_json(preset_filename)
                if sample:
                    st.session_state[state_key] = sample
                else:
                    st.warning("Example JSON unavailable.")
            if st.button("Validate", key=f"{kind}_validate"):
                try:
                    json.loads(st.session_state.get(f"{kind}_text", ""))
                    st.success("✓ Valid")
                except Exception as ex:
                    st.error(f"Invalid: {ex}")
        text_used = st.session_state.get(f"{kind}_text") or None

    return file_path, text_used


# ─────────────────────────────────────────────────────────────────────────────
# Visual-editor legend
# ─────────────────────────────────────────────────────────────────────────────

def _render_editor_legend(alphabet: list):
    color_map = _editor_symbol_colors(alphabet)
    parts = [
        "**Legend:**",
        "○ Normal state",
        "◎ Accept state (double ring)",
        "→ Start state (arrow)",
    ]
    if alphabet:
        for sym in alphabet:
            c = color_map.get(sym, "#111")
            parts.append(f'<span style="color:{c};font-weight:700">─── {sym}</span>')
    parts.append('<span style="color:#6c757d;font-style:italic">- - - ε (epsilon)</span>')
    st.markdown(
        "&nbsp;&nbsp;|&nbsp;&nbsp;".join(parts),
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shared visual-editor widget (DFA and NFA share most logic)
# ─────────────────────────────────────────────────────────────────────────────

def _render_visual_editor(
    automaton_type: str,
    state_key: str,
    flow_key: str,
    allow_eps: bool = False,
    sidebar_prefix: str = "",
) -> tuple:
    col_alphabet, col_eps = st.columns([3, 1])
    with col_alphabet:
        imported_alpha = st.session_state.pop(f"{automaton_type.lower()}_alphabet_imported", None)
        default_alpha = imported_alpha or "a,b"
        alphabet_input = st.text_input(
            "Alphabet (comma-separated symbols)",
            value=st.session_state.get(f"{automaton_type.lower()}_alpha_val", default_alpha),
            key=f"{automaton_type.lower()}_alpha_input",
        )
        st.session_state[f"{automaton_type.lower()}_alpha_val"] = alphabet_input
    with col_eps:
        include_eps = st.checkbox("Allow epsilon transitions", value=True, key=f"{automaton_type.lower()}_eps_chk") if allow_eps else False

    alphabet = _split_csv(alphabet_input)
    if state_key not in st.session_state:
        st.session_state[state_key] = _editor_new_state()
    editor = st.session_state[state_key]

    tool_mode = st.radio("Tool", ["Select", "Add State", "Add Transition", "Delete"], horizontal=True, key=f"{automaton_type}_tool_mode")

    col_a, col_b, col_c, col_d, col_e = st.columns([1, 1, 1, 1, 3])
    with col_a:
        if st.button("Add State", key=f"{automaton_type}_add_state", use_container_width=True, disabled=(tool_mode != "Add State")):
            idx = len(_editor_state_ids(editor))
            node_id = _next_state_id([{"id": sid} for sid in _editor_state_ids(editor)])
            row = idx // 6
            col_pos = idx % 6
            editor["states"][node_id] = {"x": 160 + 140 * col_pos, "y": 160 + 130 * row, "accept": False}
            st.rerun()
    with col_b:
        if st.button("Delete Selected", key=f"{automaton_type}_del", use_container_width=True, disabled=(tool_mode != "Delete")):
            current_flow = _streamlit_flow_safe(flow_key, _editor_to_flow_state(editor, alphabet))
            _editor_remove_selected(editor, current_flow)
            _reset_flow_component_state(flow_key)
            st.rerun()
    with col_c:
        if st.button("Clear All", key=f"{automaton_type}_clear", use_container_width=True):
            st.session_state[state_key] = _editor_new_state()
            _reset_flow_component_state(flow_key)
            st.rerun()
    with col_d:
        if st.button("Auto Tidy", key=f"{automaton_type}_tidy", use_container_width=True):
            _editor_auto_tidy_layout(editor)
            _reset_flow_component_state(flow_key)
            st.rerun()
    with col_e:
        if tool_mode == "Add Transition":
            st.caption("Transition mode: use the transition panel below for deliberate edge creation.")
        elif tool_mode == "Delete":
            st.caption("Delete mode: select nodes/edges on canvas, then click Delete Selected.")
        else:
            st.caption("Drag states to move. Drag from right handle to left handle to create transitions.")

    _render_editor_legend(alphabet)
    render_state = _editor_to_flow_state(editor, alphabet)
    returned_flow = _streamlit_flow_safe(flow_key, render_state)
    _editor_sync_positions_from_flow(editor, returned_flow)
    _editor_sync_new_edges_from_flow(editor, returned_flow)
    node_ids = _editor_state_ids(editor)

    if automaton_type == "DFA":
        conflicts = _editor_dfa_conflicts(editor)
        if conflicts:
            st.warning("DFA nondeterminism detected:")
            for msg in conflicts:
                st.caption(f"- {msg}")

    st.sidebar.subheader(f"{sidebar_prefix or automaton_type} State Settings")
    if node_ids:
        default_start = editor.get("start_state") if editor.get("start_state") in node_ids else node_ids[0]
        start_state = st.sidebar.radio("Start State", node_ids, index=node_ids.index(default_start), key=f"{automaton_type}_start_state", format_func=_editor_make_label)
        accept_states = st.sidebar.multiselect(
            "Accept States (double-ring)",
            node_ids,
            default=[s for s in node_ids if editor["states"][s].get("accept")],
            key=f"{automaton_type}_accept_states",
            format_func=_editor_make_label,
        )
        editor["start_state"] = start_state
        for sid in node_ids:
            editor["states"][sid]["accept"] = sid in accept_states
    else:
        editor["start_state"] = ""
        st.sidebar.info("Add states using the toolbar.")

    if editor.get("edges"):
        st.markdown("---")
        st.markdown("**Edit transition labels and routing**")
        edge_options = {
            e["id"]: f"{_editor_make_label(e['source'])} -> {_editor_make_label(e['target'])} [{_format_symbols_for_label(e.get('label','')) or 'empty'}]"
            for e in editor["edges"]
        }
        selected_edge_id = st.selectbox("Edge", list(edge_options.keys()), format_func=lambda eid: edge_options.get(eid, eid), key=f"{automaton_type}_edge_select")
        edge_obj = next((e for e in editor["edges"] if e["id"] == selected_edge_id), None)
        if edge_obj is not None:
            cols = st.columns(4)
            with cols[0]:
                hint = "e.g. a,b or epsilon" + (" (epsilon allowed)" if allow_eps else "")
                new_label = st.text_input("Symbols", value=_format_symbols_for_label(edge_obj.get("label", "")), key=f"{automaton_type}_edit_edge_label", placeholder=hint)
                edge_obj["label"] = _editor_symbols_to_label(_editor_edge_symbols(new_label))
            with cols[1]:
                edge_obj["edge_type"] = st.selectbox("Type", ["default", "smoothstep", "straight"], index=["default", "smoothstep", "straight"].index(edge_obj.get("edge_type", "default")) if edge_obj.get("edge_type", "default") in {"default", "smoothstep", "straight"} else 0, key=f"{automaton_type}_edge_type")
            with cols[2]:
                edge_obj["source_handle"] = st.selectbox("From side", ["right", "left", "top", "bottom"], index=["right", "left", "top", "bottom"].index(edge_obj.get("source_handle", "right")) if edge_obj.get("source_handle", "right") in {"right", "left", "top", "bottom"} else 0, key=f"{automaton_type}_edge_src_handle")
            with cols[3]:
                edge_obj["target_handle"] = st.selectbox("To side", ["left", "right", "top", "bottom"], index=["left", "right", "top", "bottom"].index(edge_obj.get("target_handle", "left")) if edge_obj.get("target_handle", "left") in {"left", "right", "top", "bottom"} else 0, key=f"{automaton_type}_edge_tgt_handle")
            edge_obj["route_offset"] = int(st.slider("Route offset", min_value=0, max_value=220, value=int(edge_obj.get("route_offset", 0) or 0), step=4, key=f"{automaton_type}_edge_offset"))
            if st.button("Remove Edge", key=f"{automaton_type}_remove_edge", use_container_width=True):
                editor["edges"] = [e for e in editor["edges"] if e["id"] != selected_edge_id]
                st.rerun()

    with st.expander("Add transition manually", expanded=(tool_mode == "Add Transition")):
        if node_ids:
            ca, cb, cc, cd = st.columns(4)
            with ca:
                from_state = st.selectbox("From", node_ids, key=f"{automaton_type}_from", format_func=_editor_make_label)
            with cb:
                to_state = st.selectbox("To", node_ids, key=f"{automaton_type}_to", format_func=_editor_make_label)
            with cc:
                edge_label_manual = st.text_input("Label", key=f"{automaton_type}_edge_label_manual", placeholder="a,b or epsilon")
            with cd:
                st.write("")
                st.write("")
                if st.button("Add", key=f"{automaton_type}_add_edge", use_container_width=True):
                    clean_label = _editor_symbols_to_label(_editor_edge_symbols(edge_label_manual))
                    is_loop = from_state == to_state
                    editor["edges"].append(
                        {
                            "id": f"e_{len(editor['edges'])+1}_{from_state}_{to_state}",
                            "source": from_state,
                            "target": to_state,
                            "label": clean_label,
                            "edge_type": "smoothstep" if is_loop else "default",
                            "source_handle": "right",
                            "target_handle": "right" if is_loop else "left",
                            "route_offset": 72 if is_loop else 0,
                        }
                    )
                    st.rerun()
        else:
            st.caption("Add states first.")

    with st.expander("Import / Export JSON", expanded=False):
        import_text = st.text_area("Paste JSON to import", value="", key=f"{automaton_type}_import_json", height=120)
        ci, ce = st.columns(2)
        with ci:
            if st.button("Load JSON into editor", key=f"{automaton_type}_import_btn", use_container_width=True):
                try:
                    imported_editor, imported_alpha = _editor_import_json_to_editor(import_text, automaton_type)
                    st.session_state[state_key] = imported_editor
                    if imported_alpha:
                        st.session_state[f"{automaton_type.lower()}_alphabet_imported"] = ",".join(imported_alpha)
                    _reset_flow_component_state(flow_key)
                    st.success("Imported successfully.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Import failed: {ex}")
        with ce:
            try:
                exported = _editor_export_for_explainer(editor, alphabet, automaton_type, allow_eps=include_eps)
                st.download_button("Download current JSON", data=json.dumps(exported, indent=2), file_name=f"{automaton_type.lower()}_export.json", mime="application/json", use_container_width=True, key=f"{automaton_type}_dl_json")
            except Exception:
                pass
        st.markdown("**Current export preview:**")
        try:
            exported = _editor_export_for_explainer(editor, alphabet, automaton_type, allow_eps=include_eps)
            st.code(json.dumps(exported, indent=2), language="json")
        except Exception as ex:
            st.caption(f"Preview unavailable until valid: {ex}")

    validated_json = None
    val_key = f"{automaton_type}_visual_validation"
    if st.button(f"Validate {automaton_type} input", key=f"{automaton_type}_validate_visual", type="primary"):
        try:
            validated_json = _editor_export_for_explainer(editor, alphabet, automaton_type, allow_eps=include_eps)
            st.session_state[val_key] = ("ok", f"{automaton_type} input is valid and ready to run.")
        except Exception as ex:
            st.session_state[val_key] = ("error", str(ex))

    if val_key in st.session_state:
        status, msg = st.session_state[val_key]
        (st.success if status == "ok" else st.error)(msg)
        if status == "ok":
            try:
                validated_json = _editor_export_for_explainer(editor, alphabet, automaton_type, allow_eps=include_eps)
            except Exception:
                validated_json = None

    return editor, alphabet, validated_json


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ─────────────────────────────────────────────────────────────────────────────

EXPLAINER_LABELS = {
    "DFA Minimization": "dfa-min",
    "NFA ε-Removal": "nfa-eps",
    "CFG → CNF": "cnf",
    "Turing Machine": "tm",
    "Pumping Lemma — Explanation": "pl-explain",
    "Pumping Lemma — Interactive": "pl-interactive",
}
label_choice = st.sidebar.selectbox("Explainer", list(EXPLAINER_LABELS.keys()), index=0)
tab = EXPLAINER_LABELS[label_choice]
st.sidebar.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Tab: DFA Minimization
# ─────────────────────────────────────────────────────────────────────────────

if tab == "dfa-min":
    st.header("DFA Minimization")
    mode = st.radio("Input mode", ["Visual Editor", "Paste / Upload JSON", "Preset", "Random"], horizontal=True)

    out_dir = st.text_input("Output directory", OUT_BASE)
    example_id = st.text_input("Example ID (optional — integer)")

    args = {
        "from_file": None, "preset": False, "random": False,
        "seed": 42, "num_states": None, "num_symbols": 2,
        "out_dir": out_dir, "example_id": None, "latex_only": False,
    }
    dfa_builder_json = None

    if mode == "Visual Editor":
        dfa_alphabet = _split_csv(st.text_input("Alphabet (comma-separated)", value="a,b", key="dfa_component_alphabet"))
        if callable(automata_editor_component):
            component_value = automata_editor_component(
                automaton_type="DFA",
                alphabet=dfa_alphabet,
                key="dfa_automata_component",
                default=None,
            )
            if isinstance(component_value, dict):
                dfa_builder_json = component_value
                with st.expander("Current component JSON", expanded=False):
                    st.code(json.dumps(dfa_builder_json, indent=2), language="json")
            else:
                st.info("Build the DFA in the visual editor. JSON syncs automatically.")
        else:
            st.error("Automata editor component is unavailable. Ensure interfaces/automata_editor_component.py and frontend/dist are in the runtime image.")

    elif mode == "Paste / Upload JSON":
        file_path, text_used = _json_text_or_file("dfa", "dfa_sample.json", "DFA JSON file")
        if text_used:
            tmp_path = os.path.join(OUT_BASE, "dfa_input.json")
            try:
                json.loads(text_used)
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(text_used)
                args["from_file"] = tmp_path
            except Exception as ex:
                st.error(f"Invalid JSON: {ex}")
        elif file_path:
            args["from_file"] = file_path

    elif mode == "Preset":
        args["preset"] = True

    else:  # Random
        col1, col2, col3 = st.columns(3)
        args["random"] = True
        args["num_states"] = col1.number_input("States", 2, 20, 5, 1)
        args["num_symbols"] = col2.number_input("Alphabet size", 1, 5, 2, 1)
        args["seed"] = col3.number_input("Seed", 0, 1_000_000, 42, 1)

    if example_id.strip():
        try:
            args["example_id"] = int(example_id.strip())
        except Exception:
            st.warning("Example ID must be an integer.")

    if dfa_builder_json:
        tmp_path = os.path.join(OUT_BASE, "dfa_input.json")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(dfa_builder_json, indent=2))
        args["from_file"] = tmp_path

    st.markdown("---")
    if st.button("▶ Run DFA Minimization", type="primary"):
        if mode == "Visual Editor" and not dfa_builder_json:
            st.error("Validate the DFA input first (click **✔ Validate** above).")
            st.stop()
        os.makedirs(out_dir, exist_ok=True)
        with st.spinner("Running DFA Minimization and compiling PDF…"):
            handle_dfa_min(Namespace(**args))
        latest = _latest_pdf_under(out_dir)
        if latest:
            st.success(f"Generated: {latest}")
            download_file_button("⬇ Download PDF", latest)
            if st.checkbox("Preview PDF inline", value=True, key="dfa_preview"):
                preview_pdf_inline(latest)
        else:
            st.error("No PDF found. Check logs in the output directory.")


# ─────────────────────────────────────────────────────────────────────────────
# Tab: NFA ε-Removal
# ─────────────────────────────────────────────────────────────────────────────

elif tab == "nfa-eps":
    st.header("NFA ε-Removal")
    mode = st.radio("Input mode", ["Visual Editor", "Paste / Upload JSON", "Preset"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="e_removal")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")

    nfa_file = None
    nfa_builder_json = None

    if mode == "Visual Editor":
        nfa_alphabet = _split_csv(st.text_input("Alphabet (comma-separated)", value="a,b", key="nfa_component_alphabet"))
        if callable(automata_editor_component):
            component_value = automata_editor_component(
                automaton_type="NFA",
                alphabet=nfa_alphabet,
                key="nfa_automata_component",
                default=None,
            )
            if isinstance(component_value, dict):
                nfa_builder_json = component_value
                with st.expander("Current component JSON", expanded=False):
                    st.code(json.dumps(nfa_builder_json, indent=2), language="json")
            else:
                st.info("Build the NFA in the visual editor. JSON syncs automatically.")
        else:
            st.error("Automata editor component is unavailable. Ensure interfaces/automata_editor_component.py and frontend/dist are in the runtime image.")

    elif mode == "Paste / Upload JSON":
        file_path, text_used = _json_text_or_file(
            "nfa", "nfa_eps_sample.json", 'NFA JSON (use "" for ε)',
        )
        if text_used:
            try:
                json.loads(text_used)
                nfa_file = os.path.join(OUT_BASE, "nfa_input.json")
                with open(nfa_file, "w", encoding="utf-8") as f:
                    f.write(text_used)
            except Exception as ex:
                st.error(f"Invalid JSON: {ex}")
        elif file_path:
            nfa_file = file_path

    st.markdown("---")
    if st.button("▶ Run NFA ε-Removal", type="primary"):
        if mode == "Visual Editor" and not nfa_builder_json:
            st.error("Validate the NFA input first.")
            st.stop()
        if nfa_builder_json:
            nfa_file = os.path.join(OUT_BASE, "nfa_input.json")
            with open(nfa_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(nfa_builder_json, indent=2))
        args = Namespace(from_file=nfa_file, preset=(mode == "Preset"), out=out_tex, latex_only=not gen_pdf)
        with st.spinner("Generating explainer and compiling PDF…"):
            handle_nfa_eps(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("⬇ Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="nfa_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")


# ─────────────────────────────────────────────────────────────────────────────
# Tab: CFG → CNF
# ─────────────────────────────────────────────────────────────────────────────

elif tab == "cnf":
    st.header("CFG → Chomsky Normal Form")
    mode = st.radio("Input mode", ["Table", "Text", "Paste / Upload JSON", "Preset"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="cnf_converter")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")

    grammar_file = None
    grammar_builder = None

    if mode in ("Table", "Text"):
        st.subheader("CFG Builder")
        if mode == "Table":
            st.caption("One row per variable. Use `|` to separate alternatives. Use `e` for ε.")
            df = pd.DataFrame([["S", "aA | b"], ["A", "S | e | AB"]], columns=["Variable", "Productions"])
            edited = st.data_editor(df, key="cfg_table", use_container_width=True, num_rows="dynamic")
            if st.button("✔ Validate CFG", type="primary"):
                try:
                    grammar: dict = {}
                    for _, row in edited.iterrows():
                        var = str(row["Variable"]).strip()
                        prods = str(row["Productions"]).strip()
                        if not var:
                            continue
                        alts = [a.strip() for a in prods.split("|") if a.strip()]
                        if not alts:
                            raise ValueError(f"Missing productions for '{var}'.")
                        grammar[var] = alts
                    if not grammar:
                        raise ValueError("Provide at least one production.")
                    grammar_builder = grammar
                    st.session_state["cfg_validated"] = grammar
                    st.success("✓ CFG is valid.")
                except Exception as ex:
                    st.error(str(ex))
        else:
            example = "S -> aA | b\nA -> S | e | AB\nB -> bbb | ASA"
            text = st.text_area("Grammar (one rule per line, `->` separator)", value=example, height=180)
            if st.button("✔ Validate CFG", type="primary"):
                try:
                    grammar_builder = _parse_cfg_text(text)
                    st.session_state["cfg_validated"] = grammar_builder
                    st.success("✓ CFG is valid.")
                except Exception as ex:
                    st.error(str(ex))

        if "cfg_validated" in st.session_state and st.session_state["cfg_validated"]:
            grammar_builder = st.session_state["cfg_validated"]

    elif mode == "Paste / Upload JSON":
        file_path, text_used = _json_text_or_file("cnf", "grammar_sample.json", "Grammar JSON (use 'e' for ε)")
        if text_used:
            try:
                json.loads(text_used)
                grammar_file = os.path.join(OUT_BASE, "grammar_input.json")
                with open(grammar_file, "w", encoding="utf-8") as f:
                    f.write(text_used)
            except Exception as ex:
                st.error(f"Invalid JSON: {ex}")
        elif file_path:
            grammar_file = file_path

    st.markdown("---")
    if st.button("▶ Run CNF Converter", type="primary"):
        if mode in ("Table", "Text") and not grammar_builder:
            st.error("Validate the CFG first.")
            st.stop()
        if grammar_builder:
            grammar_file = os.path.join(OUT_BASE, "grammar_input.json")
            with open(grammar_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(grammar_builder, indent=2))
        args = Namespace(from_file=grammar_file, preset=(mode == "Preset"), out=out_tex, latex_only=not gen_pdf)
        with st.spinner("Converting grammar and compiling PDF…"):
            handle_cnf(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("⬇ Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="cnf_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")


# ─────────────────────────────────────────────────────────────────────────────
# Tab: Turing Machine
# ─────────────────────────────────────────────────────────────────────────────

elif tab == "tm":
    st.header("Turing Machine Simulator")
    mode = st.radio("Input mode", ["Table", "Paste / Upload JSON", "Preset"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="tm_steps")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")

    col1, col2, col3 = st.columns(3)
    left = col1.number_input("Plot Left Index", value=-5)
    right = col2.number_input("Plot Right Index", value=15)
    max_steps = col3.number_input("Max Steps", value=500)

    tm_file = None
    tm_builder = None

    if mode == "Table":
        st.subheader("TM Builder")
        col_l, col_r = st.columns(2)
        with col_l:
            tape_string = st.text_input("Tape input string", value="0101#0101")
            blank_symbol = st.text_input("Blank symbol", value="⊔")
        with col_r:
            initial_state = st.text_input("Initial state", value="q1")
            accept_state = st.text_input("Accept state", value="qaccept")
            reject_state = st.text_input("Reject state", value="qreject")

        st.caption("Transition table — one row per (state, read) pair. Move must be **L**, **R**, or **S**.")
        df = pd.DataFrame(
            [["q1", "0", "x", "R", "q2"], ["q2", "1", "y", "R", "q1"]],
            columns=["State", "Read", "Write", "Move", "Next"],
        )
        edited = st.data_editor(df, key="tm_transitions", use_container_width=True, num_rows="dynamic")

        if st.button("✔ Validate TM", type="primary"):
            try:
                tf: dict = {}
                for _, row in edited.iterrows():
                    state = str(row["State"]).strip()
                    read = str(row["Read"]).strip()
                    write = str(row["Write"]).strip()
                    move = str(row["Move"]).strip().upper()
                    nxt = str(row["Next"]).strip()
                    if not (state and read and write and move and nxt):
                        raise ValueError("All transition fields are required.")
                    if move not in {"L", "R", "S"}:
                        raise ValueError("Move must be L, R, or S.")
                    tf[f"({state},{read})"] = [write, move, nxt]
                tm_builder = {
                    "tape_string": tape_string,
                    "blank_symbol": blank_symbol,
                    "initial_state": initial_state,
                    "accept_state": accept_state,
                    "reject_state": reject_state,
                    "transition_function": tf,
                }
                st.session_state["tm_validated"] = tm_builder
                st.success("✓ TM input is valid.")
            except Exception as ex:
                st.error(str(ex))

        if "tm_validated" in st.session_state:
            tm_builder = st.session_state["tm_validated"]

    elif mode == "Paste / Upload JSON":
        file_path, text_used = _json_text_or_file("tm", "tm_sample.json", "TM JSON")
        if text_used:
            try:
                json.loads(text_used)
                tm_file = os.path.join(OUT_BASE, "tm_input.json")
                with open(tm_file, "w", encoding="utf-8") as f:
                    f.write(text_used)
            except Exception as ex:
                st.error(f"Invalid JSON: {ex}")
        elif file_path:
            tm_file = file_path

    st.markdown("---")
    if st.button("▶ Run TM Explainer", type="primary"):
        if mode == "Table" and not tm_builder:
            st.error("Validate the TM first.")
            st.stop()
        if tm_builder:
            tm_file = os.path.join(OUT_BASE, "tm_input.json")
            with open(tm_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(tm_builder, indent=2))
        args = Namespace(
            from_file=tm_file, preset=(mode == "Preset"), out=out_tex,
            left=int(left), right=int(right), max_steps=int(max_steps), latex_only=not gen_pdf,
        )
        with st.spinner("Simulating Turing Machine and compiling PDF…"):
            handle_tm(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("⬇ Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="tm_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")


# ─────────────────────────────────────────────────────────────────────────────
# Tabs: Pumping Lemma (Explanation / Interactive)
# ─────────────────────────────────────────────────────────────────────────────

elif tab in ("pl-explain", "pl-interactive"):
    _pl_dir = _THIS_DIR / "pumping_lemma"
    if str(_pl_dir) not in sys.path:
        sys.path.insert(0, str(_pl_dir))

    import importlib as _il

    if tab == "pl-explain":
        st.header("Pumping Lemma — Explanation")
        try:
            import explanation as _pl_explanation
            _il.reload(_pl_explanation)
            _pl_explanation.render_explanation()
        except Exception as _ex:
            st.error(f"Unable to load pumping lemma explanation: {_ex}")
    else:
        st.header("Pumping Lemma — Interactive")
        try:
            import interactive as _pl_interactive
            _il.reload(_pl_interactive)
            _pl_interactive.render_interactive()
        except Exception as _ex:
            st.error(f"Unable to load pumping lemma interactive: {_ex}")
