import streamlit as st
import sys
from pathlib import Path

# Add the current directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

import explanation
import interactive

st.markdown("## Pumping Lemma")
view = st.radio(
    "View",
    options=["explanation", "interactive"],
    horizontal=True,
    label_visibility="collapsed",
)

if view == "explanation":
    explanation.render_explanation()
else:
    interactive.render_interactive()
