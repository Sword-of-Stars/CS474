from pdflatex import PDFLaTeX

# Create a PDF from a .tex file
pdfl = PDFLaTeX.from_texfile('my_file.tex')
pdf, log, completed_process = pdfl.create_pdf()