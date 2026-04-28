from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components


_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND_DIST = _ROOT / "frontend" / "dist"

if os.environ.get("AUTOMATA_DEV") == "1":
    _component = components.declare_component(
        "automata_editor_component",
        url="http://localhost:5173",
    )
else:
    _component = components.declare_component(
        "automata_editor_component",
        path=str(_FRONTEND_DIST),
    )


def automata_editor_component(
    automaton_type: str,
    alphabet: list[str] | None = None,
    key: str | None = None,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return _component(
        automaton_type=automaton_type,
        alphabet=alphabet or [],
        key=key,
        default=default,
    )
