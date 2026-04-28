# Phase 3 Problems:

This phase is a wrap-up of the project in making auto-explainers.

a) First, create a simulator/auto-explainer for Turing machines that shows how the configurations progress as the machine runs. See an example of this on page 4 of Lesson 19's notes. I should be able to plug any TM and any input string I want, and the output would be a series of figures that depict the tape as it is moving.

b) Second, using the encoding scheme we did in Lesson 23 (Universal TM), implement that machine with a given string (representing another TM and an input string to that TM) and show the Universal TM running. The auto-explainer would explain the different parts of the input TM/input string work. This machine of course uses 3 tapes, so you may need to find a way to visualize that. I also would recommend using different colors for the TM's individual transitions and input string. 

c) Next, create an auto-explainer for performing a reduction (starting in Lesson 29). This is likely impossible to do *all* possible reductions as the reasoning for each reduction is different. What I would look into are some of the examples we use and to generalize them in a way that is auto-explainable. There will be diagrams for visualizing the reduction in the lesson notes, so you may want to look at that. (Side note: if you can find a way to make those LaTeX figures auto-creatable and look "nice", that would be amazing! GPT has not been very helpful with this for me.)


d) If you want to be REALLY adventurous (this is not a requirement, but something cool to have), create a parser that takes a Python program (or any other programming language, even one you come up with), and outputs an equivalent Turing machine. Then the auto-explainer would show how the pieces of the program fit together on the tape.

 
For these problems, you ARE allowed to use Generative AI to any extent that you wish. Remember when you submit your final paper to accurately document any GenAI usage in your writeup according to the directions in the Phase 3 PDF on Canvas.