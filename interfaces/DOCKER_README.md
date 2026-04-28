Run in Docker

Prereqs
- Install Docker Desktop (Windows/macOS) or Docker Engine (Linux).

Build
- docker build -t cs474-explainers .

Run
- docker run --rm -p 7860:7860 -v %cd%/out:/app/out cs474-explainers   (Windows PowerShell)
- docker run --rm -p 7860:7860 -v "$(pwd)/out:/app/out" cs474-explainers (macOS/Linux)

Usage
- Open http://localhost:7860 in a browser.
- Choose an explainer, upload JSON or use preset/random, and click Run.
- PDFs and .tex files are written to the mounted out/ folder and available via Download buttons.

Notes
- This container includes TeXLive and Graphviz, so pdflatex and pygraphviz work out of the box.
- The UI wraps the same logic as interfaces/auto_explainer_cli.py; outputs should match the desktop GUI.

