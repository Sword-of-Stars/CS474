from jinja2 import Template, Environment
import subprocess
import os
import sys
from enum import Enum
from typing import Dict, Any, Optional
import shutil

class OutputFormat(Enum):
    LATEX = "latex"
    MARKDOWN = "markdown"
    HTML = "html"

class Solution:
    def __init__(self, 
                 output_format: OutputFormat = OutputFormat.LATEX,
                 format_path: str = "phase1/nfa_to_dfa_conversion/templates", 
                 outfile: str = None):
        """
        Initialize the Solution with configurable output format.
        Uses PlasTeX to convert LaTeX to HTML/Markdown instead of separate templates.
        
        Args:
            output_format: Output format (LATEX, MARKDOWN, or HTML)
            format_path: Base path to template directories
            outfile: Custom output file path (optional)
        """
        self.output_format = output_format
        self.FORMAT_PATH = format_path
        
        # Set up paths
        if outfile is None:
            base_dir = "phase1/nfa_to_dfa_conversion/out"
            if output_format == OutputFormat.LATEX:
                self.OUT_FILE = os.path.join(base_dir, "e_removal.tex")
            elif output_format == OutputFormat.MARKDOWN:
                self.OUT_FILE = os.path.join(base_dir, "e_removal.md")
            else:  # HTML
                self.OUT_FILE = os.path.join(base_dir, "e_removal.html")
        else:
            self.OUT_FILE = outfile
            
        self.OUTPUT_PATH = os.path.dirname(self.OUT_FILE)
        
        # For non-LaTeX formats, we'll create an intermediate LaTeX file
        if output_format != OutputFormat.LATEX:
            self.latex_intermediate = os.path.join(self.OUTPUT_PATH, "intermediate.tex")
        else:
            self.latex_intermediate = None
        
        self.has_generated_latex = False
        self.has_generated_content = False
        
        # Load LaTeX templates (we always use LaTeX templates as the source)
        self._load_latex_templates()
        
        # Dynamic content storage
        self.dynamic_content = ""

    def _load_latex_templates(self):
        """Load LaTeX template files."""
        try:
            format_file = os.path.join(self.FORMAT_PATH, "format.tex")
            intro_file = os.path.join(self.FORMAT_PATH, "introduction.tex")
            conclusion_file = os.path.join(self.FORMAT_PATH, "conclusion.tex")
            
            self.format = self._read_template(format_file)
            self.introduction = self._read_template(intro_file)
            self.conclusion = self._read_template(conclusion_file)
            
            if self.format and self.introduction and self.conclusion:
                print(f"Loaded LaTeX templates from {self.FORMAT_PATH}")
            else:
                print("Warning: Some LaTeX templates were empty or missing")
                
        except Exception as e:
            print(f"Error loading LaTeX templates: {e}")
            self.format = self.introduction = self.conclusion = ""

    def _read_template(self, filepath: str) -> str:
        """Read template file with error handling."""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding='utf-8') as f:
                return f.read()
        else:
            print(f"Warning: Template file {filepath} not found")
            return ""

    def add_dynamic_content(self, template_name: str, data: Dict[str, Any]):
        """
        Add dynamic content using Jinja2 template rendering.
        Always uses LaTeX templates.
        
        Args:
            template_name: Name of the template file (with or without extension)
            data: Data dictionary to pass to the template
        """
        # Remove extension if provided
        if template_name.endswith('.tex'):
            template_name = os.path.splitext(template_name)[0]
        
        # Always use LaTeX template
        template_file = os.path.join(self.FORMAT_PATH, f"{template_name}.tex")
        
        try:
            template_str = self._read_template(template_file)
            if not template_str:
                print(f"Warning: Empty or missing template {template_file}")
                return
            
            # Create Jinja2 template
            template = Template(template_str)
            template.environment = Environment(trim_blocks=True, lstrip_blocks=True)
            
            # Render template with data
            rendered_content = template.render(data)
            self.dynamic_content += rendered_content
            print(f"Successfully rendered LaTeX template: {template_file}")
            
        except Exception as e:
            print(f"Error rendering template {template_file}: {e}")
            raise

    def generate_latex(self):
        """Generate LaTeX content."""
        return self.generate_content()

    def generate_content(self):
        """Generate the complete content."""
        # Ensure output directory exists
        os.makedirs(self.OUTPUT_PATH, exist_ok=True)
        
        # Combine all content
        full_latex_content = self.format + self.introduction + self.dynamic_content + self.conclusion
        
        if self.output_format == OutputFormat.LATEX:
            # Write directly to output file
            with open(self.OUT_FILE, "w", encoding='utf-8') as f:
                f.write(full_latex_content)
            print(f"[SOLUTION] LaTeX file generated at {self.OUT_FILE}")
            
        else:
            # Write to intermediate LaTeX file
            with open(self.latex_intermediate, "w", encoding='utf-8') as f:
                f.write(full_latex_content)
            print(f"[SOLUTION] Intermediate LaTeX file created at {self.latex_intermediate}")
            
            # Convert using PlasTeX
            if self.output_format == OutputFormat.HTML:
                self._convert_latex_to_html()
            elif self.output_format == OutputFormat.MARKDOWN:
                self._convert_latex_to_markdown()
        
        self.has_generated_content = True
        self.has_generated_latex = True
        
        return full_latex_content
    
    def _convert_latex_to_html(self):
        """Convert LaTeX to HTML using PlasTeX."""
        try:
            print("Converting LaTeX to HTML using PlasTeX...")
            
            # Call plastex as a Python module to avoid PATH issues
            result = subprocess.run([
                sys.executable,  # Use the current Python interpreter
                "-m", "plasTeX",
                "--renderer=HTML5",
                f"--dir={self.OUTPUT_PATH}",
                "--filename=e_removal.html",
                self.latex_intermediate
            ], capture_output=True, text=True, check=True)
            
            print(f"[SOLUTION] HTML file generated at {self.OUT_FILE}")
            
            if result.stdout:
                print("PlasTeX output:", result.stdout)
                
        except subprocess.CalledProcessError as e:
            print(f"PlasTeX conversion failed: {e}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            self._print_plastex_installation()
            raise
            
        except FileNotFoundError:
            print("Error: plastex module not found.")
            self._print_plastex_installation()
            raise
    
    def _convert_latex_to_markdown(self):
        """Convert LaTeX to Markdown using pandoc (via intermediate step)."""
        try:
            print("Converting LaTeX to Markdown using pandoc...")
            
            # Use pandoc to convert LaTeX to Markdown
            result = subprocess.run([
                "pandoc",
                self.latex_intermediate,
                "-f", "latex",
                "-t", "markdown",
                "-o", self.OUT_FILE,
                "--wrap=none"
            ], capture_output=True, text=True, check=True)
            
            print(f"[SOLUTION] Markdown file generated at {self.OUT_FILE}")
            
        except subprocess.CalledProcessError as e:
            print(f"Pandoc conversion failed: {e}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            self._print_pandoc_installation()
            raise
            
        except FileNotFoundError:
            print("Error: pandoc not found.")
            self._print_pandoc_installation()
            raise

    def generate_pdf(self, try_alternative=True):
        """Generate PDF from the source file."""
        if not self.has_generated_content:
            self.generate_content()
        
        if self.output_format == OutputFormat.LATEX:
            self._generate_pdf_from_latex(self.OUT_FILE)
        elif self.output_format == OutputFormat.MARKDOWN:
            self._generate_pdf_from_markdown()
        elif self.output_format == OutputFormat.HTML:
            self._generate_pdf_from_html(try_alternative)
    
    def _generate_pdf_from_latex(self, latex_file):
        """Generate PDF from LaTeX file in nonstop mode and halt on error."""
        try:
            print("Generating PDF from LaTeX using pdflatex...")
            latex_basename = os.path.basename(latex_file)
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={self.OUTPUT_PATH}",
                latex_basename,
            ]
            # First pass
            subprocess.run(cmd, check=True, cwd=self.OUTPUT_PATH)
            # Second pass for references
            subprocess.run(cmd, check=True, cwd=self.OUTPUT_PATH)

            pdf_name = os.path.splitext(os.path.basename(latex_file))[0] + ".pdf"
            pdf_path = os.path.join(self.OUTPUT_PATH, pdf_name)
            print(f"[SOLUTION] PDF generated successfully: {pdf_path}")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log_path = os.path.join(self.OUTPUT_PATH, os.path.splitext(os.path.basename(latex_file))[0] + ".log")
            print(f"pdflatex failed: {e}")
            if os.path.exists(log_path):
                print(f"See LaTeX log: {log_path}")
            self._print_pdflatex_installation()
            raise
    
    def _generate_pdf_from_markdown(self):
        """Generate PDF from Markdown using pandoc."""
        try:
            print("Generating PDF from Markdown using pandoc...")
            pdf_path = os.path.join(self.OUTPUT_PATH, "e_removal.pdf")
            
            result = subprocess.run([
                "pandoc",
                self.OUT_FILE,
                "-o", pdf_path,
                "--pdf-engine=xelatex",
                "--variable", "geometry:margin=1in"
            ], capture_output=True, text=True, check=True)
            
            print(f"[SOLUTION] PDF generated successfully: {pdf_path}")
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Pandoc PDF generation failed: {e}")
            self._print_pandoc_installation()
            raise
    
    def _generate_pdf_from_html(self, try_alternative=True):
        """Generate PDF from HTML using weasyprint or wkhtmltopdf."""
        pdf_path = os.path.join(self.OUTPUT_PATH, "e_removal.pdf")
        
        # Try weasyprint first
        success = self._try_weasyprint(pdf_path)
        
        # Try wkhtmltopdf as alternative
        if not success and try_alternative:
            print("Trying alternative: wkhtmltopdf...")
            success = self._try_wkhtmltopdf(pdf_path)
        
        if not success:
            print("All HTML→PDF conversion attempts failed.")
    
    def _try_weasyprint(self, pdf_path):
        """Try to generate PDF using weasyprint."""
        try:
            print("Generating PDF from HTML using weasyprint...")
            result = subprocess.run([
                "weasyprint",
                self.OUT_FILE,
                pdf_path
            ], capture_output=True, text=True, check=True)
            
            print(f"[SOLUTION] PDF generated successfully: {pdf_path}")
            return True
            
        except FileNotFoundError:
            print("weasyprint not found.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"weasyprint failed: {e}")
            return False
    
    def _try_wkhtmltopdf(self, pdf_path):
        """Try to generate PDF using wkhtmltopdf."""
        try:
            result = subprocess.run([
                "wkhtmltopdf",
                "--page-size", "A4",
                "--margin-top", "1in",
                "--margin-bottom", "1in",
                "--margin-left", "1in",
                "--margin-right", "1in",
                self.OUT_FILE,
                pdf_path
            ], capture_output=True, text=True, check=True)
            
            print(f"[SOLUTION] PDF generated successfully: {pdf_path}")
            return True
            
        except FileNotFoundError:
            print("wkhtmltopdf not found.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"wkhtmltopdf failed: {e}")
            return False

    # ----------------------- Helper Guidance -----------------------
    def _print_pdflatex_installation(self):
        print("pdflatex not found or failed. Ensure a LaTeX distribution is installed and on PATH.")
        print("- Windows: install MiKTeX (https://miktex.org/download) and enable 'install missing packages on-the-fly'.")
        print("- macOS: install MacTeX (https://www.tug.org/mactex/).")
        print("- Linux: install TeX Live (e.g., sudo apt-get install texlive-full).")
        print("After installation, reopen your terminal so PATH updates take effect.")

    def _print_plastex_installation(self):
        print("plasTeX is required for LaTeX→HTML. Install via: pip install plasTeX")
        print("If using a virtual environment, make sure it is active when running the tool.")

    def _print_pandoc_installation(self):
        print("pandoc is required for LaTeX/Markdown conversions. Install from https://pandoc.org/installing.html")
        print("On Windows/macOS use the installer; on Linux use your package manager or the tarball.")

    
    def check_dependencies(self) -> dict:
        """Check if conversion tools are available."""
        tools = ['pdflatex', 'plastex', 'pandoc', 'weasyprint', 'wkhtmltopdf']
        status = {}
        
        for tool in tools:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                status[tool] = {
                    'available': result.returncode == 0,
                    'version': result.stdout.split('\n')[0] if result.returncode == 0 else None
                }
            except (FileNotFoundError, subprocess.TimeoutExpired):
                status[tool] = {'available': False, 'version': None}
        
        return status
    
    def print_dependency_status(self):
        """Print the status of all conversion tools."""
        status = self.check_dependencies()
        print("\n=== Dependency Status ===")
        
        requirements = {
            'LaTeX → PDF': ['pdflatex'],
            'LaTeX → HTML': ['plastex'],
            'LaTeX → Markdown': ['pandoc'],
            'Markdown → PDF': ['pandoc', 'pdflatex'],
            'HTML → PDF': ['weasyprint', 'wkhtmltopdf']
        }
        
        for conversion, tools in requirements.items():
            available_tools = [tool for tool in tools if status[tool]['available']]
            if available_tools:
                print(f"✓ {conversion}: {', '.join(available_tools)}")
            else:
                print(f"❌ {conversion}: No tools available (need: {', '.join(tools)})")
        
        print()
        return status


# Factory functions for easy creation
def create_latex_solution(format_path: str = "phase1/nfa_to_dfa_conversion/templates", 
                         outfile: str = None) -> Solution:
    """Create a Solution instance for LaTeX output."""
    return Solution(OutputFormat.LATEX, format_path, outfile)

def create_markdown_solution(format_path: str = "phase1/nfa_to_dfa_conversion/templates", 
                            outfile: str = None) -> Solution:
    """Create a Solution instance for Markdown output (via LaTeX conversion)."""
    return Solution(OutputFormat.MARKDOWN, format_path, outfile)

def create_html_solution(format_path: str = "phase1/nfa_to_dfa_conversion/templates", 
                        outfile: str = None) -> Solution:
    """Create a Solution instance for HTML output (via LaTeX conversion)."""
    return Solution(OutputFormat.HTML, format_path, outfile)


# Example usage
if __name__ == "__main__":
    # Check what tools are available
    solution = Solution()
    solution.print_dependency_status()
    
    # Example data
    example_data = {
        "e_closure_table": {1: {1, 3}, 2: {2}, 3: {3}, 4: {3, 4}, 5: {5}},
        "transitions": {1: {"a": {2}, "b": set()}, 2: {"a": {3, 4}, "b": {2}}},
        "aggregate_closure": {1: {"a": {2, 3, 4}, "b": set()}},
        "partial_closure": {1: {"a": {2}, "b": set()}},
        "empty_set": r'\varnothing'
    }
    
    # LaTeX version (original workflow)
    print("\n=== Generating LaTeX Version ===")
    latex_solution = create_latex_solution()
    latex_solution.add_dynamic_content("e_removal", example_data)
    latex_solution.generate_pdf()
    
    # HTML version (converted from LaTeX using PlasTeX)
    print("\n=== Generating HTML Version ===")
    html_solution = create_html_solution()
    html_solution.add_dynamic_content("e_removal", example_data)
    html_solution.generate_content()
    html_solution.generate_pdf()
    
    # Markdown version (converted from LaTeX using pandoc)
    print("\n=== Generating Markdown Version ===")
    markdown_solution = create_markdown_solution()
    markdown_solution.add_dynamic_content("e_removal", example_data)
    markdown_solution.generate_content()
    markdown_solution.generate_pdf()
    
    print("\n=== All formats generated! ===")
