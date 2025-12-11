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

        with open(f"{self.FORMAT_PATH}/format.tex", "r", encoding="utf-8") as f:
            self.format = f.read()
        with open(f"{self.FORMAT_PATH}/introduction.tex", "r", encoding="utf-8") as f:
            self.introduction = f.read()
        with open(f"{self.FORMAT_PATH}/conclusion.tex", "r", encoding="utf-8") as f:
            self.conclusion = f.read()

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

        compile_dir = self.OUTPUT_PATH 
        tex_basename = os.path.basename(self.OUT_FILE)  
        cmd = [
            'pdflatex',
            '-interaction=nonstopmode',
            '-halt-on-error',
            tex_basename,
        ]
        try:
            # First pass
            subprocess.run(cmd, check=True, cwd=compile_dir)
            # Second pass for references
            subprocess.run(cmd, check=True, cwd=compile_dir)
        except subprocess.CalledProcessError as e:
            log_path = os.path.join(compile_dir, os.path.splitext(tex_basename)[0] + '.log')
            print(f"pdflatex failed: {e}")
            if os.path.exists(log_path):
                print(f"See LaTeX log: {log_path}")
            raise
