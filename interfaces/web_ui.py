import io
import json
import base64
import os
from argparse import Namespace

import streamlit as st

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interfaces.auto_explainer_cli import (
    handle_dfa_min,
    handle_nfa_eps,
    handle_cnf,
    handle_tm,
)


st.set_page_config(page_title="CS474 Auto-Explainers", layout="wide")
st.title("CS474 Auto‑Explainers (Web)")
st.write("Generate step-by-step PDFs for DFA Minimization, NFA ε‑removal, CNF conversion, and Turing Machines.")

OUT_BASE = os.environ.get("EXPLAINER_OUT", os.path.join(os.getcwd(), "out"))
os.makedirs(OUT_BASE, exist_ok=True)


def _latest_pdf_under(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    newest = None
    newest_mtime = -1
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith('.pdf'):
                p = os.path.join(root, f)
                m = os.path.getmtime(p)
                if m > newest_mtime:
                    newest, newest_mtime = p, m
    return newest


def _read_preset_json(name: str) -> str | None:
    """Read an example JSON from interfaces/presets/<name>.json and return its text."""
    try:
        base = os.path.join(os.path.dirname(__file__), 'presets')
        with open(os.path.join(base, name), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def _json_text_or_file(kind: str, preset_filename: str, upload_label: str):
    """Render a small UI that lets users upload a file OR paste JSON (with a preset loader).

    Returns a tuple (json_file_path, used_text) where exactly one is set when valid.
    """
    mode = st.radio(f"{kind.upper()} Source", ["Upload file", "Paste JSON"], horizontal=True, key=f"{kind}_src")
    file_path = None
    text_used = None

    if mode == "Upload file":
        up = st.file_uploader(upload_label, type=["json"], key=f"{kind}_uploader")
        if up:
            tmp_path = os.path.join(OUT_BASE, f"{kind}_input.json")
            with open(tmp_path, 'wb') as f:
                f.write(up.read())
            file_path = tmp_path
    else:
        # Pre-fill editor with example JSON if empty
        state_key = f"{kind}_text"
        if not st.session_state.get(state_key):
            sample = _read_preset_json(preset_filename)
            if sample:
                st.session_state[state_key] = sample
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area("Paste JSON here", height=220, key=state_key)
        with col2:
            if st.button("Load Example", key=f"{kind}_load_example"):
                sample = _read_preset_json(preset_filename)
                if sample:
                    st.session_state[state_key] = sample
                else:
                    st.warning("Example JSON unavailable in this image.")
        if st.button("Validate JSON", key=f"{kind}_validate"):
            try:
                json.loads(st.session_state.get(f"{kind}_text", ""))
                st.success("JSON is valid.")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        # When running, we will persist this content to a temp file
        text_used = st.session_state.get(f"{kind}_text") or None

    return file_path, text_used


# Human-friendly labels mapped to internal codes
EXPLAINER_LABELS = {
    "DFA Minimization": "dfa-min",
    "NFA without Epsilon Transitions": "nfa-eps",
    "CFG to CNF": "cnf",
    "Turing Machine": "tm",
}
label_choice = st.sidebar.selectbox("Explainer", list(EXPLAINER_LABELS.keys()), index=0)
tab = EXPLAINER_LABELS[label_choice]


def download_file_button(label: str, file_path: str):
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        st.download_button(label, data=data, file_name=os.path.basename(file_path), mime='application/pdf')
    else:
        st.info("No PDF available yet.")


def preview_pdf_inline(file_path: str, height: int = 800):
    """Render a PDF inline using a base64 data URL inside an iframe."""
    if not (file_path and os.path.exists(file_path)):
        st.info("No PDF to preview.")
        return
    try:
        with open(file_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        src = f"data:application/pdf;base64,{b64}"
        st.markdown(
            f'<iframe src="{src}" width="100%" height="{height}px" style="border: 1px solid #ddd;"></iframe>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Could not preview PDF: {e}")


if tab == "dfa-min":
    st.header("DFA Minimization")
    mode = st.radio("Input Mode", ["Preset", "Random", "From JSON"], horizontal=True)

    out_dir = st.text_input("Output Base Directory", OUT_BASE)
    example_id = st.text_input("Example ID (optional)")

    args = {
        'from_file': None,
        'preset': False,
        'random': False,
        'seed': 42,
        'num_states': None,
        'num_symbols': 2,
        'out_dir': out_dir,
        'example_id': None,
        'latex_only': False,
    }

    if mode == "From JSON":
        file_path, text_used = _json_text_or_file('dfa', 'dfa_sample.json', 'DFA JSON')
        if text_used:
            tmp_path = os.path.join(OUT_BASE, "dfa_input.json")
            try:
                json.loads(text_used)  # validate
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(text_used)
                args['from_file'] = tmp_path
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        elif file_path:
            args['from_file'] = file_path
    elif mode == "Preset":
        args['preset'] = True
    else:
        args['random'] = True
        args['num_states'] = st.number_input("States", min_value=2, max_value=20, value=5, step=1)
        args['num_symbols'] = st.number_input("Alphabet Size", min_value=1, max_value=5, value=2, step=1)
        args['seed'] = st.number_input("Seed", min_value=0, max_value=1_000_000, value=42, step=1)

    if example_id.strip():
        try:
            args['example_id'] = int(example_id.strip())
        except Exception:
            st.warning("Example ID must be an integer.")

    if st.button("Run DFA Minimization"):
        os.makedirs(out_dir, exist_ok=True)
        with st.spinner("Running DFA Minimization and compiling PDF…"):
            handle_dfa_min(Namespace(**args))
        latest = _latest_pdf_under(out_dir)
        if latest:
            st.success(f"Generated: {latest}")
            download_file_button("Download PDF", latest)
            if st.checkbox("Preview PDF inline", value=True, key="dfa_preview"):
                preview_pdf_inline(latest)
        else:
            st.error("No PDF found. Check logs inside the output directory.")


elif tab == "nfa-eps":
    st.header("NFA without Epsilon Transitions")
    mode = st.radio("Input Mode", ["Preset", "From JSON"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="e_removal")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")

    nfa_file = None
    if mode == "From JSON":
        file_path, text_used = _json_text_or_file('nfa', 'nfa_eps_sample.json', 'NFA JSON (use empty string "" for ε)')
        if text_used:
            try:
                json.loads(text_used)
                nfa_file = os.path.join(OUT_BASE, "nfa_input.json")
                with open(nfa_file, 'w', encoding='utf-8') as f:
                    f.write(text_used)
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        elif file_path:
            nfa_file = file_path

    if st.button("Run NFA ε‑Removal"):
        args = Namespace(from_file=nfa_file, preset=(mode == "Preset"), out=out_tex, latex_only=not gen_pdf)
        with st.spinner("Generating explainer and compiling PDF…"):
            handle_nfa_eps(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="nfa_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")


elif tab == "cnf":
    st.header("CFG to CNF")
    mode = st.radio("Input Mode", ["Preset", "From JSON"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="cnf_converter")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")

    grammar_file = None
    if mode == "From JSON":
        file_path, text_used = _json_text_or_file('cnf', 'grammar_sample.json', "Grammar JSON (use 'e' for ε)")
        if text_used:
            try:
                json.loads(text_used)
                grammar_file = os.path.join(OUT_BASE, "grammar_input.json")
                with open(grammar_file, 'w', encoding='utf-8') as f:
                    f.write(text_used)
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        elif file_path:
            grammar_file = file_path

    if st.button("Run CNF Converter"):
        args = Namespace(from_file=grammar_file, preset=(mode == "Preset"), out=out_tex, latex_only=not gen_pdf)
        with st.spinner("Converting grammar and compiling PDF…"):
            handle_cnf(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="cnf_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")


elif tab == "tm":
    st.header("Turing Machine")
    mode = st.radio("Input Mode", ["Preset", "From JSON"], horizontal=True)
    gen_pdf = st.checkbox("Generate PDF", value=True)
    out_name = st.text_input("Output filename (no extension)", value="tm_steps")
    out_tex = os.path.join(OUT_BASE, f"{out_name}.tex")
    left = st.number_input("Plot Left Index", value=-5)
    right = st.number_input("Plot Right Index", value=15)
    max_steps = st.number_input("Max Steps", value=500)

    tm_file = None
    if mode == "From JSON":
        file_path, text_used = _json_text_or_file('tm', 'tm_sample.json', "TM JSON (tuple keys as '(state,symbol)')")
        if text_used:
            try:
                json.loads(text_used)
                tm_file = os.path.join(OUT_BASE, "tm_input.json")
                with open(tm_file, 'w', encoding='utf-8') as f:
                    f.write(text_used)
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
        elif file_path:
            tm_file = file_path

    if st.button("Run TM Explainer"):
        args = Namespace(from_file=tm_file, preset=(mode == "Preset"), out=out_tex,
                         left=int(left), right=int(right), max_steps=int(max_steps), latex_only=not gen_pdf)
        with st.spinner("Simulating Turing Machine and compiling PDF…"):
            handle_tm(args)
        pdf_path = os.path.splitext(out_tex)[0] + ".pdf"
        if gen_pdf and os.path.exists(pdf_path):
            st.success(f"Generated: {pdf_path}")
            download_file_button("Download PDF", pdf_path)
            if st.checkbox("Preview PDF inline", value=True, key="tm_preview"):
                preview_pdf_inline(pdf_path)
        else:
            st.info(f"LaTeX generated at {out_tex}")
