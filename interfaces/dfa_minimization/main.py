import argparse
import os
import sys

# Ensure repository root is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from interfaces.auto_explainer_cli import handle_dfa_min


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DFA Minimization Auto‑Explainer")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--from-file", help="Path to DFA JSON input")
    src.add_argument("--preset", action="store_true", help="Use a small preset DFA")
    src.add_argument("--random", action="store_true", help="Generate a random DFA")
    p.add_argument("--num-states", type=int, default=5, help="States for random DFA")
    p.add_argument("--num-symbols", type=int, default=2, help="Alphabet size for random DFA")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument("--out-dir", default="training_data", help="Base directory for outputs")
    p.add_argument("--example-id", type=int, help="Explicit example id (optional)")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    # Delegate to shared handler
    handle_dfa_min(args)


if __name__ == "__main__":
    main()

