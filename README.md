---
title: CS474 Auto Explainer
sdk: docker
app_port: 8080
---

# Project Description

Theoretical Computer Science educators often need to generate solutions to problems, in a variety of forms (PDF, HTML, Markdown, LaTeX, etc.). However, these often involve creating diagrams and precise mathematical statements. Further, these solutions should have an explanation of what is occurring in each step, or how the solution was obtained. In summary, these solutions almost always need to be created by hand.

 
In this project you will create an *automatic* solution generator for CS educators, for a variety of classic theory problems and conversions.

 
**NB**: this is a *difficult* project and will require lots of programming and potential headaches. However, this will be very useful for educators, and may lead to publication at a CS education venue.

 

## Phase 1 Problems:

Throughout all three phases, you are allowed to use any programming language of your choice.

Further, you will need some way of automatically creating the machine diagrams. One difficult, but great way of doing this is to use TikZ, which is the backbone for all the CS474 figures. However, you are allowed to use any automaton diagram creator you wish.

Also further, you can use any existing automaton library that you wish to extend already-implemented methods. One that I've used a lot is: https://github.com/caleb531/automata.

 

(a) Design a class that will model an "unformatted" solution. This should have methods that will create an HTML output of the corresponding solution, or Markdown, or LaTeX, etc. The format of the solution should involve a preamble, a list of steps, and a conclusion. Note that you will be updating this class throughout CS474 as there are many different types of problem solutions, and you may potentially have to change your design accordingly.

 

You are not required to have all the conversions to Markdown, LaTeX, etc. implemented by this phase. However, you should have at least one done so that you can demonstrate your tool by the time Phase 1 Draft is due.

 

(b) Create an auto-explainer for creating a DFA for the language L_{b,n} = {w in {0, 1, ..., b-1}* : w represents a multiple of the integer n}. There is a standard solution for how to create a DFA for this. However, what you're doing is making an *explainer* of how students can generate that DFA, and why the DFA you created is correct.

(c) Create an auto-explainer for the NFA to DFA conversion. The preamble here will be the starter NFA, and each step carries out one additional state made in the corresponding DFA. The course notes have an in-depth example of what I would expect the output to be, although it does not have to be exactly the same.

(d) Create an auto-explainer for proving the following language not regular: L_m = {a^i b^j : i < j + m}, where m is any nonnegative integer. The steps are the same as those of the Pumping Lemma from the course notes.

(e) Create an auto-explainer for DFA minimization.

 

You are NOT permitted to use Generative AI for these problems.

## Streamlit Automata Editor Build

The DFA/NFA visual editor is now a Streamlit custom component backed by a Vite + React frontend.

One-time build steps:

1. `pip install -r requirements.txt`
2. Build frontend:
   - macOS/Linux: `bash build_frontend.sh`
   - Windows: `build_frontend.bat`
3. Run app: `streamlit run interfaces/web_ui.py`

Development mode (optional):

1. In one terminal: `cd frontend && npm install && npm run dev`
2. In another terminal: set `AUTOMATA_DEV=1` and run `streamlit run interfaces/web_ui.py`
