FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    libgraphviz-dev \
    build-essential \
    pkg-config \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-plain-generic \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY interfaces/presets interfaces/presets
COPY interfaces/auto_explainer_cli.py interfaces/auto_explainer_cli.py
COPY interfaces/web_ui.py interfaces/web_ui.py
COPY phase1 phase1
COPY phase2 phase2
COPY phase3 phase3
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt || true \
    && pip install --no-cache-dir \
       streamlit \
        jinja2 \
        matplotlib \
        networkx \
        pandas \
        pygraphviz \
        automata-lib

RUN mkdir -p /app/out

ENV MPLBACKEND=Agg
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

EXPOSE 8080

CMD ["streamlit", "run", "interfaces/web_ui.py", "--server.port=8080", "--server.address=0.0.0.0"]
