from jinja2 import Template, Environment
import subprocess

import os

class Solution():
    def __init__(self, format_path="phase1/dfa_minimization/templates", 
                 outfile="phase1/dfa_minimization/out/dfa_min_steps.tex"):
        self.FORMAT_PATH = format_path
        self.OUT_FILE = outfile
        self.OUTPUT_PATH = os.path.dirname(self.OUT_FILE)

        self.has_generated_latex = False

        #=== Static Files ===#
        self.format = open(f"{self.FORMAT_PATH}/format.tex", "r").read()
        self.introduction = open(f"{self.FORMAT_PATH}/introduction.tex", "r").read()
        self.conclusion = open(f"{self.FORMAT_PATH}/conclusion.tex", "r").read()

        #=== Dynamic Content ===#
        self.dynamic_content = ""


    def add_dynamic_content(self, template, data):
        template_str = open(f"{self.FORMAT_PATH}/{template}", "r").read()
        template = Template(template_str)
        template.environment = Environment(trim_blocks=True)
        self.dynamic_content += template.render(data)

    def generate_latex(self):
        with open(self.OUT_FILE, "w", encoding="utf-8") as f:
            f.write(self.format)
            f.write(self.introduction)
            f.write(self.dynamic_content)
            f.write(self.conclusion)

        self.has_generated_latex = True
        print(f"[SOLUTION] LaTeX file generated at {self.OUT_FILE}")

    def generate_pdf(self):
        if not self.has_generated_latex:
            self.generate_latex()
        
        subprocess.run(["pdflatex",
                 "-output-directory=" + self.OUTPUT_PATH,
                 self.OUT_FILE,  "-interaction=nonstopmode"])