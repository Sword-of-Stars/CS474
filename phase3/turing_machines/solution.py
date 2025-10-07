from jinja2 import Template, Environment
import subprocess
import os

class Solution():
    def __init__(self, format_path="phase3/turing_machines/templates", 
                 outfile="phase3/turing_machines/out/tm_steps.tex"):
        self.FORMAT_PATH = format_path
        self.OUT_FILE = outfile
        self.OUTPUT_PATH = os.path.dirname(self.OUT_FILE)

        self.has_generated_latex = False

        #=== Static Files ===#
        with open(f"{self.FORMAT_PATH}/format.tex", "r", encoding="utf-8") as f:
            self.format = f.read()
        with open(f"{self.FORMAT_PATH}/introduction.tex", "r", encoding="utf-8") as f:
            self.introduction = f.read()
        with open(f"{self.FORMAT_PATH}/conclusion.tex", "r", encoding="utf-8") as f:
            self.conclusion = f.read()

        #=== Dynamic Content ===#
        self.dynamic_content = ""

    def add_dynamic_content(self, template, data):
        with open(f"{self.FORMAT_PATH}/{template}", "r", encoding="utf-8") as f:
            template_str = f.read()
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
                 self.OUT_FILE, "-interaction=nonstopmode"])