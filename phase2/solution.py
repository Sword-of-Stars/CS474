from jinja2 import Template, Environment
import subprocess

import os

class Solution():
    def __init__(self, format_path="phase1/part_c/templates", 
                 outfile="phase1/part_c/out/e_removal.tex"):
        self.FORMAT_PATH = format_path
        self.OUT_FILE = outfile
        self.OUTPUT_PATH = os.path.dirname(self.OUT_FILE)

        self.has_generated_latex = False

        #=== Static Files ===#
        self.format = open(f"{self.FORMAT_PATH}/format.tex", "r", encoding="utf-8").read()
        self.introduction = open(f"{self.FORMAT_PATH}/introduction.tex", "r", encoding="utf-8").read()
        self.conclusion = open(f"{self.FORMAT_PATH}/conclusion.tex", "r", encoding="utf-8").read()

        #=== Dynamic Content ===#
        self.dynamic_content = ""


    def add_dynamic_content(self, template, data):
        template_str = open(f"{self.FORMAT_PATH}/{template}", "r", encoding='utf-8').read()
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
        # Run pdflatex in nonstop mode to avoid interactive prompts
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory=" + self.OUTPUT_PATH,
            self.OUT_FILE,
        ]
        try:
            subprocess.run(cmd, check=True)
            # Second pass for references if needed
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print("pdflatex encountered errors. See the generated .log file for details.")
            raise
