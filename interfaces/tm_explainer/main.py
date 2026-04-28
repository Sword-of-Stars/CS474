import argparse
import os
import sys

# Ensure repository root is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from interfaces.auto_explainer_cli import handle_tm


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Turing Machine Auto‑Explainer")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-file", help="Path to Turing Machine JSON input")
    src.add_argument("--preset", action="store_true", help="Use a preset TM example")
    p.add_argument("--out", default=None, help="Output .tex path (PDF next to it unless --latex-only)")
    p.add_argument("--latex-only", action="store_true", help="Generate LaTeX only without compiling PDF")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    handle_tm(args)


if __name__ == "__main__":
    main()

