from pathlib import Path
import json

import streamlit as st
import streamlit.components.v1 as components

TOPIC_DIR = Path(__file__).resolve().parent
STYLE_PATH = TOPIC_DIR / "style.css"
DATA_PATH = TOPIC_DIR / "proof_blocks.json"


def load_proof_data() -> dict:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {}


def normalize_problems(data: dict) -> list[dict]:
    if "problems" in data and isinstance(data["problems"], list):
        return data["problems"]
    if "steps" in data:
        return [
            {
                "id": "default",
                "title": "Proof Blocks",
                "language_definition": data.get("language_definition", ""),
                "steps": data.get("steps", []),
            }
        ]
    return []


PROOF_DATA = load_proof_data()
PROBLEMS = normalize_problems(PROOF_DATA)

INDEX_FEEDBACK = {
    "1": "First, state the type of proof.",
    "2": "State our overarching assumption here.",
    "3": "Here, we need to define the pumping constant $p$.",
    "4": "Now, choose a string.",
    "5": "Consider all possible decompositions of $w$.",
    "6": "Choose a value of $i$.",
    "7": "Show that there is a contradiction.",
    "8": "What are we trying to prove?",
}


def load_topic_css() -> str:
    if STYLE_PATH.exists():
        return STYLE_PATH.read_text(encoding="utf-8")
    return ""


def build_component_html(css_text: str, problems: list[dict]) -> str:
    problems_json = json.dumps(problems)
    index_feedback_json = json.dumps(INDEX_FEEDBACK)

    html_template = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<script>
window.MathJax = {
  tex: {
    inlineMath: [['\\(', '\\)'], ['$', '$']]
  },
  svg: {
    fontCache: 'global'
  }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
__TOPIC_CSS__
</style>
</head>
<body>
<div class="wrapper">
  <div class="proof-container">
    <h3>Reorder the Pumping Lemma Proof Steps</h3>
    <p>Drag proof blocks from the bank to the workspace and order them correctly.</p>
    <div class="language-definition">
      <div class="language-row">
        <span class="language-label">Language:</span>
        <div class="dropdown" id="problemDropdown">
          <button type="button" class="dropdown-button" id="problemButton" aria-haspopup="listbox" aria-expanded="false">
            <span id="problemButtonText">Select language</span>
            <span class="dropdown-caret" aria-hidden="true">▾</span>
          </button>
          <div class="dropdown-menu" id="problemMenu" role="listbox" aria-label="Choose language"></div>
        </div>
      </div>
    </div>

    <div class="board">
      <div class="panel">
        <h4>Proof Block Bank</h4>
        <div id="bank" class="dropzone">
        </div>
      </div>

      <div class="panel">
        <h4>Workspace</h4>
        <div id="workspace" class="dropzone"></div>
        <div class="actions">
          <button type="button" id="checkBtn">Check Order</button>
          <span id="result"></span>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const bank = document.getElementById("bank");
const workspace = document.getElementById("workspace");
const result = document.getElementById("result");
const actions = document.querySelector(".actions");
const indexFeedback = __INDEX_FEEDBACK__;
const problems = __PROBLEMS__;
const problemDropdown = document.getElementById("problemDropdown");
const problemButton = document.getElementById("problemButton");
const problemButtonText = document.getElementById("problemButtonText");
const problemMenu = document.getElementById("problemMenu");
let dragged = null;
let draggedSource = null;
let stepMeta = {};
let expectedCount = 0;

function stripMathDelimiters(text) {
  if (!text) return "";
  if (text.startsWith("\\(") && text.endsWith("\\)")) {
    return text.slice(2, -2);
  }
  if (text.startsWith("$") && text.endsWith("$")) {
    return text.slice(1, -1);
  }
  return text;
}

function renderMathInElement(el, texWithDelims) {
  if (!window.MathJax || !window.MathJax.tex2svgPromise) {
    return;
  }
  const tex = stripMathDelimiters(texWithDelims);
  if (!tex) return;
  window.MathJax.tex2svgPromise(tex, { display: false })
    .then((node) => {
      el.innerHTML = "";
      el.appendChild(node);
    })
    .catch(() => {});
}

function getLanguageDisplay(problem, index) {
  const lang = problem.language_definition || "";
  const langTex = lang && !lang.includes("$") && !lang.includes("\\(") ? `\\(${lang}\\)` : lang;
  const fallback = stripMathDelimiters(langTex) || problem.title || `Problem ${index + 1}`;
  return { langTex, fallback };
}

function shuffle(items) {
  const array = [...items];
  for (let i = array.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function buildStepMeta(steps) {
  const meta = {};
  steps.forEach((step) => {
    meta[step.id] = {
      index: step.index,
      is_distractor: step.is_distractor,
      feedback: step.feedback,
      must_precede: step.must_precede || [],
      must_precede_feedback: step.must_precede_feedback,
    };
  });
  return meta;
}

function setProblem(problemIndex) {
  const problem = problems[problemIndex];
  if (!problem) return;

  const { langTex, fallback } = getLanguageDisplay(problem, problemIndex);
  problemButtonText.textContent = fallback;
  if (langTex) {
    renderMathInElement(problemButtonText, langTex);
  }

  const steps = problem.steps || [];
  stepMeta = buildStepMeta(steps);
  expectedCount = Math.max(...Object.values(stepMeta).map((meta) => meta.index));

  bank.innerHTML = "";
  workspace.innerHTML = "";
  clearFeedback();
  result.textContent = "";
  result.className = "";

  shuffle(steps).forEach((step) => {
    const div = document.createElement("div");
    div.className = "step";
    div.setAttribute("draggable", "true");
    div.dataset.id = step.id;
    div.innerHTML = step.content;
    bank.appendChild(div);
    wireDragEvents(div);
  });

  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise();
  }
}

function clearFeedback() {
  document.querySelectorAll(".feedback").forEach((el) => el.remove());
  document.querySelectorAll(".step.incorrect").forEach((el) => el.classList.remove("incorrect"));
  document.querySelectorAll(".step[data-has-feedback='1']").forEach((el) => el.removeAttribute("data-has-feedback"));
}

function removeFeedbackForStep(stepEl) {
  if (!stepEl) return;
  stepEl.classList.remove("incorrect");
  stepEl.removeAttribute("data-has-feedback");
  const stepId = stepEl.dataset.id;
  if (!stepId) return;
  document.querySelectorAll(`.feedback[data-for="${stepId}"]`).forEach((el) => el.remove());
}

function insertFeedbackAfter(stepEl, message) {
  return insertFeedbackAfterNode(stepEl, message, stepEl.dataset.id || "");
}

function insertFeedbackAfterNode(anchorEl, message, stepId) {
  const feedback = document.createElement("div");
  feedback.className = "feedback";
  feedback.innerHTML = message;
  feedback.dataset.for = stepId || "";
  if (stepId) {
    const stepEl = document.querySelector(`.step[data-id="${stepId}"]`);
    if (stepEl) {
      stepEl.classList.add("incorrect");
      stepEl.dataset.hasFeedback = "1";
    }
  }
  anchorEl.insertAdjacentElement("afterend", feedback);
  return feedback;
}

function insertGeneralFeedback(message) {
  const feedback = document.createElement("div");
  feedback.className = "feedback feedback-general";
  feedback.innerHTML = message;
  actions.insertAdjacentElement("afterend", feedback);
}

function wireDragEvents(el) {
  el.addEventListener("dragstart", () => {
    dragged = el;
    draggedSource = el.parentElement;
    el.classList.add("dragging");
  });

  el.addEventListener("dragend", () => {
    el.classList.remove("dragging");
    dragged = null;
    draggedSource = null;
  });

  el.addEventListener("dragover", (e) => {
    e.preventDefault();
  });
}

function wireContainerEvents(container) {
  let insertLine = null;

  function ensureInsertLine() {
    if (!insertLine) {
      insertLine = document.createElement("div");
      insertLine.className = "insert-line";
    }
    return insertLine;
  }

  function removeInsertLine() {
    if (insertLine && insertLine.parentElement) {
      insertLine.parentElement.removeChild(insertLine);
    }
  }

  function getDragAfterElement(containerEl, y) {
    const draggableElements = [...containerEl.querySelectorAll(".step:not(.dragging)")];
    let closest = { offset: Number.NEGATIVE_INFINITY, element: null };

    draggableElements.forEach((child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        closest = { offset, element: child };
      }
    });

    return closest.element;
  }

  container.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!dragged) return;
    const afterElement = getDragAfterElement(container, e.clientY);
    const line = ensureInsertLine();
    if (afterElement == null) {
      container.appendChild(line);
    } else {
      container.insertBefore(line, afterElement);
    }
  });

  container.addEventListener("drop", (e) => {
    e.preventDefault();
    if (!dragged) return;
    const afterElement = getDragAfterElement(container, e.clientY);
    if (afterElement == null) {
      container.appendChild(dragged);
    } else {
      container.insertBefore(dragged, afterElement);
    }

    if (draggedSource === workspace && container === bank) {
      removeFeedbackForStep(dragged);
    }

    removeInsertLine();
  });

  container.addEventListener("dragleave", (e) => {
    if (e.relatedTarget && container.contains(e.relatedTarget)) {
      return;
    }
    removeInsertLine();
  });

  container.addEventListener("dragend", () => {
    removeInsertLine();
  });
}

wireContainerEvents(bank);
wireContainerEvents(workspace);

problemMenu.innerHTML = "";
problems.forEach((problem, idx) => {
  const option = document.createElement("div");
  option.className = "dropdown-option";
  option.setAttribute("role", "option");
  option.dataset.index = String(idx);
  const { langTex, fallback } = getLanguageDisplay(problem, idx);
  option.textContent = fallback;
  if (langTex) {
    renderMathInElement(option, langTex);
  }
  option.addEventListener("click", () => {
    setProblem(idx);
    problemMenu.classList.remove("open");
    problemButton.setAttribute("aria-expanded", "false");
  });
  problemMenu.appendChild(option);
});

problemButton.addEventListener("click", () => {
  const isOpen = problemMenu.classList.toggle("open");
  problemButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
});

document.addEventListener("click", (event) => {
  if (!problemDropdown.contains(event.target)) {
    problemMenu.classList.remove("open");
    problemButton.setAttribute("aria-expanded", "false");
  }
});

if (problems.length > 0) {
  setProblem(0);
}

document.getElementById("checkBtn").addEventListener("click", () => {
  clearFeedback();
  const steps = [...workspace.querySelectorAll(".step")];
  const order = steps.map((node) => node.dataset.id);

  let firstIncorrectIndex = -1;
  let firstIncorrectKind = null;
  for (let i = 0; i < order.length; i += 1) {
    const stepId = order[i];
    const expectedIndex = i + 1;
    const meta = stepMeta[stepId];
    if (!meta || meta.index !== expectedIndex) {
      firstIncorrectIndex = i;
      firstIncorrectKind = "index";
      break;
    }
    if (meta.is_distractor) {
      firstIncorrectIndex = i;
      firstIncorrectKind = "distractor";
      break;
    }
    if (meta.must_precede && meta.must_precede.length > 0) {
      const seen = new Set(order.slice(0, i));
      const missing = meta.must_precede.filter((requiredId) => !seen.has(requiredId));
      if (missing.length > 0) {
        firstIncorrectIndex = i;
        firstIncorrectKind = "precede";
        break;
      }
    }
  }

  if (steps.length < expectedCount && firstIncorrectIndex === -1) {
    insertGeneralFeedback("The proof is incomplete. Add the remaining steps to the workspace.");
  } else if (firstIncorrectIndex >= 0) {
    const feedbackIndex = Math.min(firstIncorrectIndex, steps.length - 1);
    if (feedbackIndex >= 0) {
      const stepId = steps[feedbackIndex].dataset.id;
      if (firstIncorrectKind === "index") {
        const indexKey = String(firstIncorrectIndex + 1);
        const indexMessage = indexFeedback[indexKey] || "This step is out of order.";
        insertFeedbackAfter(steps[feedbackIndex], indexMessage);
      } else if (firstIncorrectKind === "precede") {
        const precedentMessage =
          stepMeta[stepId]?.must_precede_feedback || "A required earlier step is missing.";
        insertFeedbackAfter(steps[feedbackIndex], precedentMessage);
      } else {
        const stepFeedback = stepMeta[stepId]?.feedback || "This step is incorrect.";
        insertFeedbackAfter(steps[feedbackIndex], stepFeedback);
      }
    }
  }

  const hasDistractor = steps.some((stepEl) => stepMeta[stepEl.dataset.id]?.is_distractor);
  const ok = steps.length === expectedCount && firstIncorrectIndex === -1 && !hasDistractor;
  result.className = ok ? "correct" : "incorrect";
  result.textContent = ok ? "Correct order." : "Incorrect order.";

  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise();
  }
});

if (window.MathJax && window.MathJax.typesetPromise) {
  window.MathJax.typesetPromise();
}
</script>
</body>
</html>
"""
    return (
        html_template.replace("__TOPIC_CSS__", css_text)
        .replace("__PROBLEMS__", problems_json)
        .replace("__INDEX_FEEDBACK__", index_feedback_json)
    )


def render_interactive() -> None:
    st.subheader("Interactive")
    st.write("Proof steps and distractors are below, shuffled randomly. Drag to reorder them.")

    if not PROBLEMS:
        st.error("No proof blocks found.")
        return

    components.html(
        build_component_html(load_topic_css(), PROBLEMS),
        height=1020,
        scrolling=True,
    )
