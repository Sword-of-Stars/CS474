from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

TOPIC_DIR = Path(__file__).resolve().parent
STYLE_PATH = TOPIC_DIR / "style.css"


def load_topic_css() -> str:
    if STYLE_PATH.exists():
        return STYLE_PATH.read_text(encoding="utf-8")
    return ""


def lemma_box(title, content):
    st.markdown(
        f"""
        <div style="
            background-color: #f1f3f9;
            padding: 20px;
            border: 1px solid #d1d5db;
            border-left: 6px solid #6366f1;
            border-radius: 4px;
            font-family: 'serif';
            margin-bottom: 20px;
        ">
            <span style="color: #4338ca; font-weight: bold; font-size: 1.1em;">
                {title}
            </span><br><br>
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_minimal_math_step(math_content: str, accent_color: str = "#4a90e2") -> str:
    html_template = r"""
<!DOCTYPE html>
<html>
<head>
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(', '\\)'], ['$', '$']] },
  svg: { fontCache: 'global' }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
  body {
    background-color: transparent !important;
    margin: 0;
    padding: 10px;
    overflow: hidden;
  }

  .step-box {
    display: inline-block;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-left: 6px solid __COLOR__;
    border-radius: 6px;
    padding: 12px 20px;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 1.1em;
    color: #31333F;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
</style>
</head>
<body>
  <div class="step-box">
    __MATH__
  </div>
</body>
</html>
"""
    return html_template.replace("__MATH__", math_content).replace("__COLOR__", accent_color)


def render_explanation() -> None:
    st.subheader("Overview of the Pumping Lemma for Regular Languages")

    st.markdown("We use the pumping lemma to prove that a language is not regular. Let's break down that definition a bit.")
    st.markdown("A **language** is a set of strings. As an example, let's define a language $L$ such that")
    st.latex(r"L=\{0^n1^n:n\geq 0\}")
    st.markdown(
        r"In this case, $L$ accepts strings containing $0$s, then an equal number of $1$s. For example, it would accept strings such as $0011$ and the empty string $\epsilon$ (as $n$ can equal $0$), but would reject strings like $1100$ or $011$."
    )

    st.markdown(
        ""
        "Recall that a language is **regular** if it can be described by a regular expression, or, more relevant to the pumping lemma, if it can be recognized by a DFA. "
        "Equivalently, if a DFA exists for a language, then that language is regular. "
    )

    st.subheader("Building Intuition for the Pumping Lemma")
    st.markdown(
        "Let $L$ be a regular language and let $D$ be a DFA that recognizes $L$. "
        "From its definition, we know that $D$ has some finite number of states; let's call that number $p$."
    )

    st.markdown(
        r"Now consider a string $w$ with length at least $p$. "
        r"When the DFA runs on $w$, it will visit $|w|+1$ states; the start state, and one state for each letter in $w$. "
        r"Since $|w|\geq p$, then $|w|+1 > p$. "
    )

    st.markdown(
        "Since our DFA only has $p$ states, by the Pigeonhole Principle, we visit at least one state in $D$ twice. Let's call that state $q$. "
        "Note the we might visit many of these states more than once, but we're only concerned with the *first* state we repeat. "
        "Abstractly, the path we take when we run $D$ on $w$ looks something like this: "
    )

    st.image(str(TOPIC_DIR / "images" / "pl_01.png"), caption="Abstraction of the run of w on D")

    st.markdown(
        """
                Notice how this breaks our computation down into three chunks:
                1. From the start state to $q$. Let's call this portion $x$.
                2. The loop from $q$ eventually back to itself, one time through. Let's call this $y$.
                3. From $q$ eventually to some accept state. This is called $z$.
                """
    )

    st.image(
        str(TOPIC_DIR / "images" / "pl_02.png"),
        caption="Abstraction of the run of w on D, broken down into x, y, and z.",
    )

    st.markdown("Now we have all the terminology we need to tackle proofs for the pumping lemma itself.")

    st.subheader("Pumping Lemma Proof")

    lemma_text = r"""
      Let $L$ be a regular language, and let $p$ be the number of states in a DFA that accepts $L$. 
      Then for any string $w \in L$ with length $|w| \geq p$, we can break $w$ into three parts ($w = xyz$) where:
      <br>
      1. $|xy| \leq p$ <br>
      2. $|y| \geq 1$ (The loop isn't empty) <br>
      3. $x \underbrace{yyy \dots \dots yy}_{y \text{ is repeated } i \text{ times}} z = xy^iz \in L$ for all $i \geq 0$ (We can "pump" the loop any number of times)
      """

    lemma_box("Lemma 1: The Pumping Lemma (for regular languages)", lemma_text)

    st.markdown(
        "In my experience, the best way to learn a proof method is through an example. "
        "Let's prove that our language above is **not** regular using the pumping lemma. "
    )

    st.latex(r"L=\{0^n1^n:n\geq 0\}")

    st.markdown(
        "*Proof.* The structure of the pumping lemma proof is proof by contradiction. It's good practice (and for partial credit!) to begin by stating the type of proof:"
    )

    css_text = load_topic_css()

    step_0 = build_minimal_math_step("Proof by Contradiction.", css_text)
    components.html(step_0, height=60, scrolling=False)

    st.markdown("We then assume the premise of the lemma above.")
    step_1 = build_minimal_math_step(
        "Assume to the contrary that $L$ is a regular language; then there is some DFA that accepts $L$. ",
        css_text,
    )
    components.html(step_1, height=60, scrolling=False)

    st.markdown("Let's finish out the premise and properly define our pumping constant $p$.")

    step_2 = build_minimal_math_step("Let $p$ be the number of states in our DFA. ", css_text)
    components.html(step_2, height=60, scrolling=False)

    st.markdown(
        """
                Next, we need to choose a string $w$ that is 
        1. in $L$ and 
        2. has length at least $p$. 

        This part's a bit tricky, and is often more of an art than a science. 
        Look here [link] for some tips and common pitfalls to avoid. """
    )

    st.markdown(
        r"In our case, we're going to choose the string $w=0^p1^p$. "
        r"We can see that $w\in L$ because the number of $0$s at the beginning matches the number of $1$s at the end. "
    )

    step_3 = build_minimal_math_step(
        r"Consider the string $w=0^p1^p$. Since $x\in L$ and $|w|\geq p$, the pumping lemma holds for this $w$.",
        css_text,
    )
    components.html(step_3, height=60, scrolling=False)

    st.markdown(
        """
      Now, we consider all possible decompositions of $w$ into $xyz$ such that (1) and (2) of the pumping lemma hold. That is,
      1. $|xy|\leq p$ and
      2. $|y|\geq 1$
    """
    )

    step_4 = build_minimal_math_step(
        r"""
                                     Every decomposition of $w$ into $xyz$ that satisfies (1) and (2) of the pumping lemma looks like:<br>
                                     <ul style="margin-top: 10px; margin-bottom: 0;">
                                        <li>$x=0^{\alpha}$ for some $0 \leq \alpha < p$</li>
                                        <li>$y=0^{\beta}$ for some $\beta \geq 1$</li>
                                        <li>$z=0^{p-\alpha-\beta}1^p$ ($z$ is the rest of the string)</li>
                                    </ul>""",
        css_text,
    )
    components.html(step_4, height=140, scrolling=False)

    st.markdown(
        "While this may look like only one decomposition, it encodes all possible decompositions. "
        "Now, we need to choose a value for $i$, the number of times to pump. "
        r"We need to choose an $i$ such that the resulting string $xy^iz \notin L$, and not all values of $i$ will work."
    )

    step_5 = build_minimal_math_step(
        r"Let $i=2$. Then from our decomposition, $xy^iz=xy^2z=xyyz=0^\alpha 0^\beta 0^\beta 0^{p-\alpha-\beta}1^p=0^{p+\beta}1^p$.",
        css_text,
    )
    components.html(step_5, height=60, scrolling=False)

    st.markdown(r"Finally, we need to show that for our chosen value of $i$ that $xy^iz \notin L$.")

    step_6 = build_minimal_math_step(
        r"""This string starts with $p+\beta$ 0s and ends with $p$ 1s. 
                                     However, from our decomposition, we know that $\beta \geq 1$. 
                                     Thus, the number of 0s is greater than the number of 1s. 
                                     Therefore, $xy^2z\notin L$""",
        css_text,
    )
    components.html(step_6, height=70, scrolling=False)

    st.markdown(r"Now, let's actually prove what we've been trying to all along; that $L$ is not regular.")

    step_7 = build_minimal_math_step(
        r"""Since $xy^iz \notin L$ for all $i \geq 0$, $L$ is not a regular language.""",
        css_text,
    )
    components.html(step_7, height=60, scrolling=False)

    st.markdown("Now that you've seen a worked example, head on over to the [interactive] page and try one for yourself!")
