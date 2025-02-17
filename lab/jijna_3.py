from jinja2 import Template
import os, subprocess

my_template = open("lab/template_2.tex", "r").read()

j_template = Template(my_template)

with open("lab/testy.tex", "w") as f:
    f.write(j_template.render())

tex_filepath = "lab/testy.tex"
output_dir = "lab/part_c/out/" # Directory where you want PDFs

subprocess.run(["luatex",
                 "-output-directory=" + output_dir,
                 tex_filepath])