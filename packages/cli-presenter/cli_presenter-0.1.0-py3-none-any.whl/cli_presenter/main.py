import typer
import sys
import shutil
import os
from .app import PresenterApp
from .parser import parse_deck, Slide
from .exporter import export_to_html, export_to_pdf_playwright

app = typer.Typer()

DEFAULT_THEME_TCSS = """
SlideWidget {
    background: $surface;
    color: $text;
}

.layout-title {
    background: $primary;
    color: $text;
}
"""

DEFAULT_TEMPLATE_CSS = """
/* Corporate Layout - CLI Presenter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

@page { size: 1920px 1080px; margin: 0; }

body { 
    margin: 0; 
    font-family: 'Inter', sans-serif; 
    background: #f0f2f5; 
    color: #334155; 
    -webkit-font-smoothing: antialiased;
}

.slide { 
    width: 1920px; 
    height: 1080px; 
    background: white; 
    position: relative; 
    display: flex; 
    flex-direction: column; 
    box-sizing: border-box; 
    padding: 80px 120px; 
    margin: 20px auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    overflow: hidden;
}

/* Print / PDF Fixes */
@media print {
    body { background: white; }
    .slide { margin: 0; box-shadow: none; page-break-after: always; border: none; }
}

/* Typography */
h1 { 
    font-size: 72px; 
    font-weight: 700; 
    color: #1e293b; 
    margin-bottom: 40px; 
    border-bottom: 4px solid #3b82f6; 
    padding-bottom: 20px;
    display: inline-block;
}

h2 { font-size: 48px; color: #334155; margin-bottom: 30px; }
p, li { font-size: 36px; line-height: 1.6; color: #475569; margin-bottom: 16px; }

ul { margin-left: 40px; }
li::marker { color: #3b82f6; font-weight: bold; }

/* Layouts */
.layout-title { 
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: white;
    justify-content: center; 
    align-items: center; 
    text-align: center;
}

.layout-title h1 {
    color: white;
    font-size: 100px;
    border-bottom: none;
    margin-bottom: 20px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.layout-title h2 {
    color: #94a3b8;
    font-size: 48px;
    font-weight: 300;
}

.layout-center { 
    justify-content: center; 
    align-items: center; 
    text-align: center;
}

/* Components */
.logo {
    position: absolute;
    top: 60px;
    right: 60px;
    height: 60px;
    width: auto;
    opacity: 0.9;
}

pre {
    background: #f8fafc;
    border-radius: 12px;
    padding: 40px;
    border: 1px solid #e2e8f0;
    font-size: 28px;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}

blockquote {
    border-left: 8px solid #3b82f6;
    padding-left: 40px;
    font-style: italic;
    color: #475569;
    font-size: 48px;
    margin: 80px 0;
}

.mermaid { 
    display: flex; 
    justify-content: center; 
    margin-top: 40px; 
}
"""

UPDATED_TEMPLATE_MD = """layout: title
logo: https://textual.textualize.io/img/textual.png
# CLI Presenter
## The Ultimate Terminal Presentation Tool

---
layout: default
logo: https://textual.textualize.io/img/textual.png
# Features Overview

- **Markdown Based**: Write simple, portable slide decks.
- **TUI & HTML**: Present in the terminal, export to the web.
- **Rich Content**: Support for images, code blocks, and diagrams.
- **Themable**: Custom CSS for both terminal and PDF.

---
layout: center
# Centered Layout
This content is centered vertically and horizontally.
Great for quotes or big impact statements.

> "Simplicity is the ultimate sophistication."

---
layout: default
# Code Highlighting

```python
def hello_world():
    print("Hello from CLI Presenter!")
```

---
layout: default
# Mermaid Diagrams

```mermaid
graph LR;
    A[Markdown] -->|Parse| B(Slide Objects);
    B -->|Render| C{Output};
    C -->|TUI| D[Terminal];
    C -->|HTML| E[Browser/PDF];
```

---
layout: title
# Thank You
Run `cli-presenter export template.md` to see these diagrams in action!
"""

@app.command()
def init():
    """
    Initialize a new presentation template in the current directory.
    Creates template.md, theme.tcss (for TUI), and template.css (for PDF).
    """
    files_to_create = {
        "template.md": UPDATED_TEMPLATE_MD,
        "theme.tcss": DEFAULT_THEME_TCSS,
        "template.css": DEFAULT_TEMPLATE_CSS
    }
    
    for filename, content in files_to_create.items():
        if os.path.exists(filename):
            typer.secho(f"Warning: {filename} already exists. Skipping.", fg=typer.colors.YELLOW)
        else:
            try:
                with open(filename, "w") as f:
                    f.write(content)
                typer.secho(f"Created {filename}", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"Error creating {filename}: {e}", fg=typer.colors.RED)

@app.command()
def present(file: str = typer.Argument(..., help="Path to the markdown presentation file")):
    """
    Run the presentation from a markdown file.
    Use SPACE/RIGHT to advance, LEFT to go back, Q to quit.
    """
    try:
        if not os.path.exists(file):
             typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED)
             raise typer.Exit(code=1)
             
        slides = parse_deck(file)
        presentation = PresenterApp(slides)
        presentation.run()
    except Exception as e:
        typer.secho(f"Error running presentation: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def export(
    file: str = typer.Argument(..., help="Path to input markdown file"),
    output: str = typer.Option("presentation", "--output", "-o", help="Base filename for output (extension ignored)"),
    css: str = typer.Option("template.css", "--css", "-c", help="Path to CSS file for styling"),
    skip_pdf: bool = typer.Option(False, "--skip-pdf", help="Skip PDF generation")
):
    """
    Export the presentation to both HTML and PDF.
    """
    try:
        if not os.path.exists(file):
             typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED)
             raise typer.Exit(code=1)
        
        slides = parse_deck(file)
        css_path = css if os.path.exists(css) else None
        
        # Determine base path (strip extension if user provided one)
        base_path = os.path.splitext(output)[0]
        html_output = f"{base_path}.html"
        pdf_output = f"{base_path}.pdf"
        
        # 1. Export HTML
        typer.secho(f"Exporting HTML to {html_output}...", fg=typer.colors.BLUE)
        export_to_html(slides, html_output, css_path)
        typer.secho(f"HTML Export successful: {html_output}", fg=typer.colors.GREEN)
        
        # 2. Export PDF
        if not skip_pdf:
            try:
                typer.secho(f"Exporting PDF to {pdf_output}...", fg=typer.colors.BLUE)
                export_to_pdf_playwright(html_output, pdf_output)
                typer.secho(f"PDF Export successful: {pdf_output}", fg=typer.colors.GREEN)
            except ImportError:
                 typer.secho("PDF Export skipped: Playwright not installed.", fg=typer.colors.YELLOW)
                 typer.secho("Run 'pip install playwright && playwright install' to enable PDF export.", fg=typer.colors.WHITE)
            except Exception as e:
                 typer.secho(f"PDF Export failed: {e}", fg=typer.colors.RED)
        
    except Exception as e:
        typer.secho(f"Error exporting: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def main():
    """
    Entry point for the CLI. Handles command aliasing for convenience.
    """
    # Shim to allow 'cli-presenter file.md' to map to 'cli-presenter present file.md'
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        # logic: if the first arg is not a known command or flag, assume it's a file for 'present'
        # Known commands: init
        # Flags usually start with -
        known_commands = ["init", "export"]
        if cmd not in known_commands and not cmd.startswith("-") and cmd not in ["--help", "--version"]:
            sys.argv.insert(1, "present")
    
    app()

if __name__ == "__main__":
    main()
