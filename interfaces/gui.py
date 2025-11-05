import os
import sys
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
from argparse import Namespace

# Ensure repository root imports work when running from interfaces/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from interfaces.auto_explainer_cli import (
    handle_dfa_min,
    handle_nfa_eps,
    handle_cnf,
    handle_tm,
)


class AutoExplainerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto-Explainers")
        self.geometry("920x720")
        self.dark_mode = tk.BooleanVar(value=False)

        # ----- Styling -----
        self.style = ttk.Style()
        # Prefer native looks where available
        for theme in ("vista", "xpnative", "clam", "default"):
            try:
                self.style.theme_use(theme)
                break
            except Exception:
                continue
        base_pad = {"padding": 6}
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        self.style.configure("Card.TLabelframe", relief="solid")
        self.style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        self.configure(bg="#f7fafc")

        # Banner
        banner = ttk.Frame(self)
        banner.pack(side=tk.TOP, fill=tk.X)
        banner.configure(style="Banner.TFrame")
        # emulate a banner with a colored background using a plain Frame
        self._banner_bg = tk.Frame(banner, bg="#2b6cb0")
        self._banner_bg.pack(fill=tk.X)
        tk.Label(self._banner_bg, text="CS474 Auto‑Explainers", fg="white", bg="#2b6cb0",
                 font=("Segoe UI", 14, "bold"), pady=10).pack(side=tk.LEFT, padx=14, pady=4)
        # Dark mode toggle on the right
        dm_holder = tk.Frame(self._banner_bg, bg="#2b6cb0")
        dm_holder.pack(side=tk.RIGHT, padx=12)
        tk.Checkbutton(dm_holder, text="Dark Mode", variable=self.dark_mode,
                       command=self._apply_theme, fg="white", bg="#2b6cb0",
                       activebackground="#2b6cb0", activeforeground="white").pack(side=tk.RIGHT)

        # Brief description under banner
        desc = ttk.Frame(self)
        desc.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 0))
        ttk.Label(desc,
                  text="Generate step-by-step explainers and PDFs for DFA minimization, NFA ε-removal, CNF conversion, and Turing Machines.",
                  wraplength=820).pack(side=tk.LEFT)

        # Top: tool selection
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=10)
        ttk.Label(top, text="Select Explainer:").pack(side=tk.LEFT)
        self.tool_var = tk.StringVar(value="dfa-min")
        tool_combo = ttk.Combobox(top, textvariable=self.tool_var, state="readonly",
                                  values=["dfa-min", "nfa-eps", "cnf", "tm"])
        tool_combo.pack(side=tk.LEFT, padx=8)
        tool_combo.bind('<<ComboboxSelected>>', lambda e: self._show_tool_frame())

        # Center: stacked frames for each tool's options
        self.container = ttk.Frame(self)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=6)

        self.frames = {}
        self.frames['dfa-min'] = self._build_dfa_min_frame(self.container)
        self.frames['nfa-eps'] = self._build_nfa_eps_frame(self.container)
        self.frames['cnf'] = self._build_cnf_frame(self.container)
        self.frames['tm'] = self._build_tm_frame(self.container)

        # Bottom: run + output
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=12, pady=8)

        self.run_btn = ttk.Button(bottom, text="Run Explainer", command=self._on_run)
        self.run_btn.pack(side=tk.LEFT)

        self.open_out_btn = ttk.Button(bottom, text="Open Output Folder", command=self._open_output_folder)
        self.open_out_btn.pack(side=tk.LEFT, padx=6)

        # Progress indicator
        self.prog = ttk.Progressbar(bottom, mode='indeterminate', length=180)
        self.prog.pack(side=tk.RIGHT)

        self.status = scrolledtext.ScrolledText(self, height=16, wrap=tk.WORD, font=("Consolas", 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.status.configure(background="#ffffff")
        self._append_status("Ready. Select an explainer and options, then Run.\n")

        self._show_tool_frame()
        self._apply_theme()

    # ---------- UI Builders ----------
    def _build_dfa_min_frame(self, parent):
        frm = ttk.Frame(parent)

        # Mode selection
        mode = ttk.LabelFrame(frm, text="Input Mode", style="Card.TLabelframe")
        mode.pack(fill=tk.X, pady=6)
        self.dfa_mode = tk.StringVar(value='preset')
        ttk.Radiobutton(mode, text="Preset", variable=self.dfa_mode, value='preset').pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode, text="From JSON", variable=self.dfa_mode, value='file').pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode, text="Random", variable=self.dfa_mode, value='random').pack(side=tk.LEFT, padx=6)

        # File path
        file_row = ttk.Frame(frm)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="DFA JSON:").pack(side=tk.LEFT)
        self.dfa_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.dfa_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="Browse", command=lambda: self._browse(self.dfa_file)).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Show Example JSON", command=lambda: self._show_json_example('dfa')).pack(side=tk.LEFT, padx=6)
        ttk.Button(file_row, text="Load Example", command=lambda: self._load_example_path(self.dfa_file, 'interfaces/presets/dfa_sample.json')).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Edit JSON", command=lambda: self._open_json_editor('dfa', self.dfa_file)).pack(side=tk.LEFT, padx=6)

        # Random params
        rnd = ttk.LabelFrame(frm, text="Random DFA Parameters", style="Card.TLabelframe")
        rnd.pack(fill=tk.X, pady=6)
        self.dfa_states = tk.IntVar(value=5)
        self.dfa_symbols = tk.IntVar(value=2)
        self.dfa_seed = tk.IntVar(value=42)
        for label, var in [("States", self.dfa_states), ("Symbols", self.dfa_symbols), ("Seed", self.dfa_seed)]:
            row = ttk.Frame(rnd)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", width=10).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var, width=10).pack(side=tk.LEFT)

        # Output
        out = ttk.LabelFrame(frm, text="Output", style="Card.TLabelframe")
        out.pack(fill=tk.X, pady=6)
        self.dfa_out_dir = tk.StringVar(value='training_data')
        self.dfa_example = tk.StringVar(value='')
        row = ttk.Frame(out)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Base Dir:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.dfa_out_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=lambda: self._browse_dir(self.dfa_out_dir)).pack(side=tk.LEFT)
        row2 = ttk.Frame(out)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Example ID (optional):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.dfa_example, width=10).pack(side=tk.LEFT)

        ttk.Label(frm, text="Note: PDF is always produced for DFA minimization.").pack(anchor=tk.W, pady=(2, 0))

        return frm

    def _build_nfa_eps_frame(self, parent):
        frm = ttk.Frame(parent)
        mode = ttk.LabelFrame(frm, text="Input Mode", style="Card.TLabelframe")
        mode.pack(fill=tk.X, pady=6)
        self.nfa_mode = tk.StringVar(value='preset')
        ttk.Radiobutton(mode, text="Preset", variable=self.nfa_mode, value='preset').pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode, text="From JSON", variable=self.nfa_mode, value='file').pack(side=tk.LEFT, padx=6)

        file_row = ttk.Frame(frm)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="NFA JSON:").pack(side=tk.LEFT)
        self.nfa_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.nfa_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="Browse", command=lambda: self._browse(self.nfa_file)).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Show Example JSON", command=lambda: self._show_json_example('nfa')).pack(side=tk.LEFT, padx=6)
        ttk.Button(file_row, text="Load Example", command=lambda: self._load_example_path(self.nfa_file, 'interfaces/presets/nfa_eps_sample.json')).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Edit JSON", command=lambda: self._open_json_editor('nfa', self.nfa_file)).pack(side=tk.LEFT, padx=6)

        out = ttk.LabelFrame(frm, text="Output", style="Card.TLabelframe")
        out.pack(fill=tk.X, pady=6)
        self.nfa_out_dir = tk.StringVar(value='phase1/nfa_to_dfa_conversion/out')
        self.nfa_out_name = tk.StringVar(value='e_removal')
        row = ttk.Frame(out)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Folder:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.nfa_out_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=lambda: self._browse_dir(self.nfa_out_dir)).pack(side=tk.LEFT)
        row2 = ttk.Frame(out)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Filename (no ext):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.nfa_out_name, width=24).pack(side=tk.LEFT)

        self.nfa_generate_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Generate PDF (uncheck to generate LaTeX only)", variable=self.nfa_generate_pdf).pack(anchor=tk.W)
        return frm

    def _build_cnf_frame(self, parent):
        frm = ttk.Frame(parent)
        mode = ttk.LabelFrame(frm, text="Input Mode", style="Card.TLabelframe")
        mode.pack(fill=tk.X, pady=6)
        self.cnf_mode = tk.StringVar(value='preset')
        ttk.Radiobutton(mode, text="Preset", variable=self.cnf_mode, value='preset').pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode, text="From JSON", variable=self.cnf_mode, value='file').pack(side=tk.LEFT, padx=6)

        file_row = ttk.Frame(frm)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="Grammar JSON:").pack(side=tk.LEFT)
        self.cnf_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.cnf_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="Browse", command=lambda: self._browse(self.cnf_file)).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Show Example JSON", command=lambda: self._show_json_example('cnf')).pack(side=tk.LEFT, padx=6)
        ttk.Button(file_row, text="Load Example", command=lambda: self._load_example_path(self.cnf_file, 'interfaces/presets/grammar_sample.json')).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Edit JSON", command=lambda: self._open_json_editor('cnf', self.cnf_file)).pack(side=tk.LEFT, padx=6)

        out = ttk.LabelFrame(frm, text="Output", style="Card.TLabelframe")
        out.pack(fill=tk.X, pady=6)
        self.cnf_out_dir = tk.StringVar(value='phase2/out')
        self.cnf_out_name = tk.StringVar(value='cnf_converter')
        row = ttk.Frame(out)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Folder:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.cnf_out_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=lambda: self._browse_dir(self.cnf_out_dir)).pack(side=tk.LEFT)
        row2 = ttk.Frame(out)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Filename (no ext):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.cnf_out_name, width=24).pack(side=tk.LEFT)

        self.cnf_generate_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Generate PDF (uncheck to generate LaTeX only)", variable=self.cnf_generate_pdf).pack(anchor=tk.W)
        return frm

    def _build_tm_frame(self, parent):
        frm = ttk.Frame(parent)
        mode = ttk.LabelFrame(frm, text="Input Mode", style="Card.TLabelframe")
        mode.pack(fill=tk.X, pady=6)
        self.tm_mode = tk.StringVar(value='preset')
        ttk.Radiobutton(mode, text="Preset", variable=self.tm_mode, value='preset').pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode, text="From JSON", variable=self.tm_mode, value='file').pack(side=tk.LEFT, padx=6)

        file_row = ttk.Frame(frm)
        file_row.pack(fill=tk.X, pady=4)
        ttk.Label(file_row, text="TM JSON:").pack(side=tk.LEFT)
        self.tm_file = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.tm_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(file_row, text="Browse", command=lambda: self._browse(self.tm_file)).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Show Example JSON", command=lambda: self._show_json_example('tm')).pack(side=tk.LEFT, padx=6)
        ttk.Button(file_row, text="Load Example", command=lambda: self._load_example_path(self.tm_file, 'interfaces/presets/tm_sample.json')).pack(side=tk.LEFT)
        ttk.Button(file_row, text="Edit JSON", command=lambda: self._open_json_editor('tm', self.tm_file)).pack(side=tk.LEFT, padx=6)

        bounds = ttk.LabelFrame(frm, text="Plot Window / Steps", style="Card.TLabelframe")
        bounds.pack(fill=tk.X, pady=6)
        self.tm_left = tk.IntVar(value=-5)
        self.tm_right = tk.IntVar(value=15)
        self.tm_steps = tk.IntVar(value=500)
        for label, var in [("Left", self.tm_left), ("Right", self.tm_right), ("Max Steps", self.tm_steps)]:
            row = ttk.Frame(bounds)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", width=12).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=var, width=10).pack(side=tk.LEFT)

        out = ttk.LabelFrame(frm, text="Output", style="Card.TLabelframe")
        out.pack(fill=tk.X, pady=6)
        self.tm_out_dir = tk.StringVar(value='phase3/turing_machines/out')
        self.tm_out_name = tk.StringVar(value='tm_steps')
        row = ttk.Frame(out)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Folder:").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=self.tm_out_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=lambda: self._browse_dir(self.tm_out_dir)).pack(side=tk.LEFT)
        row2 = ttk.Frame(out)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Filename (no ext):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.tm_out_name, width=24).pack(side=tk.LEFT)

        self.tm_generate_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Generate PDF (uncheck to generate LaTeX only)", variable=self.tm_generate_pdf).pack(anchor=tk.W)
        return frm

    # ---------- Helpers ----------
    def _show_tool_frame(self):
        for name, frame in self.frames.items():
            frame.pack_forget()
        active = self.frames[self.tool_var.get()]
        active.pack(fill=tk.BOTH, expand=True)

    def _browse(self, var: tk.StringVar):
        path = filedialog.askopenfilename(title="Select JSON file", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            var.set(path)

    def _browse_save(self, var: tk.StringVar):
        path = filedialog.asksaveasfilename(title="Save .tex path", defaultextension=".tex",
                                            filetypes=[("LaTeX", "*.tex"), ("All files", "*.*")])
        if path:
            var.set(path)

    def _browse_dir(self, var: tk.StringVar):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            var.set(path)

    def _load_example_path(self, var: tk.StringVar, example_rel: str):
        if os.path.exists(example_rel):
            var.set(example_rel)
        else:
            # Try repo root relative
            repo_rel = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', example_rel))
            var.set(repo_rel if os.path.exists(repo_rel) else example_rel)

    def _show_json_example(self, kind: str):
        mapping = {
            'dfa': 'interfaces/presets/dfa_sample.json',
            'nfa': 'interfaces/presets/nfa_eps_sample.json',
            'cnf': 'interfaces/presets/grammar_sample.json',
            'tm':  'interfaces/presets/tm_sample.json',
        }
        path = mapping.get(kind)
        if not path or not os.path.exists(path):
            # attempt repo-relative
            path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', path or ''))
            path = path2 if os.path.exists(path2) else path
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("JSON Example", f"Could not load example: {e}")
            return
        win = tk.Toplevel(self)
        win.title("JSON Example")
        win.geometry("700x500")
        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert(tk.END, content)
        def copy_clip():
            try:
                self.clipboard_clear()
                self.clipboard_append(txt.get("1.0", tk.END))
                messagebox.showinfo("Copied", "JSON copied to clipboard")
            except Exception:
                pass
        bar = ttk.Frame(win)
        bar.pack(fill=tk.X)
        ttk.Button(bar, text="Copy to Clipboard", command=copy_clip).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(bar, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=6, pady=6)

    def _open_json_editor(self, kind: str, bind_var: tk.StringVar):
        import json
        schemas = {
            'dfa': {
                'required': ['states', 'input_symbols', 'transitions', 'initial_state', 'final_states'],
                'hint': (
                    'DFA schema:\n'
                    '{\n  "states": ["1","2"],\n  "input_symbols": ["a","b"],\n'
                    '  "transitions": {"1":{"a":"2","b":"1"}},\n  "initial_state": "1",\n  "final_states": ["2"]\n}\n'
                )
            },
            'nfa': {
                'required': ['states', 'input_symbols', 'transitions', 'initial_state', 'final_states'],
                'hint': (
                    'NFA schema (use "" for ε):\n'
                    '{\n  "states": [1,2,3],\n  "input_symbols": ["a","b"],\n'
                    '  "transitions": {"1": {"a": [2], "": [3]}},\n  "initial_state": 1,\n  "final_states": [3]\n}\n'
                )
            },
            'cnf': {
                'required': [],
                'hint': (
                    'Grammar schema (use "e" for ε):\n'
                    '{"S": ["AaB", "b"], "A": ["e", "AB"], "B": ["bbb", "ASA"]}\n'
                )
            },
            'tm': {
                'required': ['tape_string', 'blank_symbol', 'initial_state', 'accept_state', 'reject_state', 'transition_function'],
                'hint': (
                    'TM schema (tuple keys as strings):\n'
                    '{\n  "tape_string": "0101#0101",\n  "blank_symbol": "⊔",\n  "initial_state": "q1",\n'
                    '  "accept_state": "qaccept", "reject_state": "qreject",\n  "transition_function": {"(q1,0)": ["x","R","q2"]}\n}\n'
                )
            },
        }
        example_map = {
            'dfa': 'interfaces/presets/dfa_sample.json',
            'nfa': 'interfaces/presets/nfa_eps_sample.json',
            'cnf': 'interfaces/presets/grammar_sample.json',
            'tm':  'interfaces/presets/tm_sample.json',
        }

        win = tk.Toplevel(self)
        win.title(f"Edit {kind.upper()} JSON")
        win.geometry("880x600")
        container = ttk.Frame(win)
        container.pack(fill=tk.BOTH, expand=True)

        hints = tk.Text(container, height=6, wrap=tk.WORD, bg="#f1f5f9")
        hints.pack(fill=tk.X, padx=10, pady=(10, 0))
        hints.insert(tk.END, schemas[kind]['hint'])
        hints.configure(state=tk.DISABLED)

        editor = scrolledtext.ScrolledText(container, wrap=tk.WORD, font=("Consolas", 10))
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load existing or example
        content = ""
        path = bind_var.get().strip()
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                content = ""
        if not content:
            ex = example_map[kind]
            if not os.path.exists(ex):
                ex = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', ex))
            try:
                with open(ex, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                content = "{}"
        editor.insert(tk.END, content)

        bar = ttk.Frame(container)
        bar.pack(fill=tk.X, padx=10, pady=(0, 10))

        def do_validate():
            try:
                data = json.loads(editor.get("1.0", tk.END))
            except Exception as e:
                messagebox.showerror("Invalid JSON", f"JSON parsing failed: {e}")
                return None
            missing = [k for k in schemas[kind]['required'] if k not in data]
            if missing:
                messagebox.showwarning("Schema", f"Missing required keys: {', '.join(missing)}")
                return None
            messagebox.showinfo("Valid", "JSON looks valid for this explainer.")
            return data

        def do_save_as():
            data = do_validate()
            if data is None:
                return
            out = filedialog.asksaveasfilename(title="Save JSON", defaultextension=".json",
                                               filetypes=[("JSON", "*.json")])
            if not out:
                return
            try:
                with open(out, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                bind_var.set(out)
                messagebox.showinfo("Saved", f"Saved to {out}")
            except Exception as e:
                messagebox.showerror("Save failed", str(e))

        def do_apply_temp():
            data = do_validate()
            if data is None:
                return
            tmp_dir = os.path.join('interfaces', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = os.path.join(tmp_dir, f'{kind}_edited.json')
            try:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                bind_var.set(tmp_path)
                messagebox.showinfo("Applied", f"Using edited JSON: {tmp_path}")
            except Exception as e:
                messagebox.showerror("Apply failed", str(e))

        ttk.Button(bar, text="Validate", command=do_validate).pack(side=tk.LEFT)
        ttk.Button(bar, text="Save As…", command=do_save_as).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Apply (Temp)", command=do_apply_temp).pack(side=tk.LEFT)
        ttk.Button(bar, text="Close", command=win.destroy).pack(side=tk.RIGHT)

    def _append_status(self, text: str):
        self.status.configure(state=tk.NORMAL)
        self.status.insert(tk.END, text)
        self.status.see(tk.END)
        self.status.configure(state=tk.NORMAL)

    def _set_running(self, running: bool):
        self.run_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        if running:
            try:
                self.prog.start(10)
            except Exception:
                pass
        else:
            try:
                self.prog.stop()
            except Exception:
                pass

    def _open_output_folder(self):
        # Best-effort: open commonly used output folders
        candidates = [
            'training_data',
            'phase1/nfa_to_dfa_conversion/out',
            'phase2/out',
            'phase3/turing_machines/out'
        ]
        for c in candidates:
            if os.path.isdir(c):
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(os.path.abspath(c))  # type: ignore[attr-defined]
                    elif sys.platform == 'darwin':
                        os.system(f'open "{c}"')
                    else:
                        os.system(f'xdg-open "{c}"')
                    return
                except Exception:
                    pass
        messagebox.showinfo("Open Output", "No output folder found yet. Run an explainer first.")

    # ---------- Execution ----------
    def _on_run(self):
        tool = self.tool_var.get()
        self._append_status(f"\n=== Running: {tool} ===\n")
        self._set_running(True)

        def run():
            try:
                if tool == 'dfa-min':
                    args = Namespace(
                        from_file=self.dfa_file.get() if self.dfa_mode.get() == 'file' else None,
                        preset=(self.dfa_mode.get() == 'preset'),
                        random=(self.dfa_mode.get() == 'random'),
                        seed=self.dfa_seed.get(),
                        num_states=(self.dfa_states.get() if self.dfa_mode.get() == 'random' else None),
                        num_symbols=(self.dfa_symbols.get() if self.dfa_mode.get() == 'random' else 2),
                        out_dir=self.dfa_out_dir.get(),
                        example_id=(int(self.dfa_example.get()) if self.dfa_example.get().strip() else None),
                        latex_only=False,
                    )
                    handle_dfa_min(args)
                elif tool == 'nfa-eps':
                    out_dir = self.nfa_out_dir.get().strip()
                    out_name = self.nfa_out_name.get().strip() or 'e_removal'
                    out_path = os.path.join(out_dir, out_name + '.tex')
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    args = Namespace(
                        from_file=self.nfa_file.get() if self.nfa_mode.get() == 'file' else None,
                        preset=(self.nfa_mode.get() == 'preset'),
                        out=out_path,
                        latex_only=not self.nfa_generate_pdf.get(),
                    )
                    handle_nfa_eps(args)
                elif tool == 'cnf':
                    out_dir = self.cnf_out_dir.get().strip()
                    out_name = self.cnf_out_name.get().strip() or 'cnf_converter'
                    out_path = os.path.join(out_dir, out_name + '.tex')
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    args = Namespace(
                        from_file=self.cnf_file.get() if self.cnf_mode.get() == 'file' else None,
                        preset=(self.cnf_mode.get() == 'preset'),
                        out=out_path,
                        latex_only=not self.cnf_generate_pdf.get(),
                    )
                    handle_cnf(args)
                elif tool == 'tm':
                    out_dir = self.tm_out_dir.get().strip()
                    out_name = self.tm_out_name.get().strip() or 'tm_steps'
                    out_path = os.path.join(out_dir, out_name + '.tex')
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    args = Namespace(
                        from_file=self.tm_file.get() if self.tm_mode.get() == 'file' else None,
                        preset=(self.tm_mode.get() == 'preset'),
                        out=out_path,
                        left=self.tm_left.get(),
                        right=self.tm_right.get(),
                        max_steps=self.tm_steps.get(),
                        latex_only=not self.tm_generate_pdf.get(),
                    )
                    handle_tm(args)
                self._append_status("Done.\n")
            except Exception as e:
                self._append_status("Error: " + str(e) + "\n")
                self._append_status(traceback.format_exc() + "\n")
            finally:
                self._set_running(False)

        threading.Thread(target=run, daemon=True).start()

    # ---------- Theming ----------
    def _apply_theme(self):
        dark = self.dark_mode.get()
        if dark:
            bg = "#0f172a"  # slate-900
            txt_bg = "#0b1220"
            txt_fg = "#e2e8f0"
            banner = "#0b2a55"
            self.configure(bg=bg)
            try:
                self._banner_bg.configure(bg=banner)
                for child in self._banner_bg.winfo_children():
                    try:
                        child.configure(bg=banner, fg="white")
                    except Exception:
                        pass
            except Exception:
                pass
            self.status.configure(background=txt_bg, foreground=txt_fg, insertbackground=txt_fg)
        else:
            bg = "#f7fafc"
            self.configure(bg=bg)
            try:
                self._banner_bg.configure(bg="#2b6cb0")
                for child in self._banner_bg.winfo_children():
                    try:
                        child.configure(bg="#2b6cb0", fg="white")
                    except Exception:
                        pass
            except Exception:
                pass
            self.status.configure(background="#ffffff", foreground="#000000", insertbackground="#000000")


if __name__ == '__main__':
    app = AutoExplainerGUI()
    app.mainloop()
