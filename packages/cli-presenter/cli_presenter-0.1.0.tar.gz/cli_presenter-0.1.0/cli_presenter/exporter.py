import os
import markdown
from jinja2 import Template
from typing import List
from .parser import Slide

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Presentation</title>
    <style>
        {{ css }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true });
    </script>
    <script>
        // Simple navigation script for the HTML export
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function showSlide(n) {
            slides[currentSlide].style.display = 'none';
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].style.display = 'flex';
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                showSlide(currentSlide + 1);
            } else if (e.key === 'ArrowLeft') {
                showSlide(currentSlide - 1);
            }
        });
        
        // Show all slides for printing
        window.onbeforeprint = () => {
             slides.forEach(s => s.style.display = 'flex');
        };
        window.onafterprint = () => {
             slides.forEach(s => s.style.display = 'none');
             slides[currentSlide].style.display = 'flex';
        };
    </script>
</head>
<body>
    {% for slide in slides %}
    <div class="slide layout-{{ slide.metadata.get('layout', 'default') }}">
        {% if slide.metadata.get('logo') %}
        <img src="{{ slide.metadata.get('logo') }}" class="logo" alt="Logo">
        {% endif %}
        <div class="content">
            {{ slide.html_content }}
        </div>
    </div>
    {% endfor %}
    <script>
        // Initialize
        slides.forEach(s => s.style.display = 'none');
        if(slides.length > 0) slides[0].style.display = 'flex';
    </script>
</body>
</html>
"""

def export_to_html(slides: List[Slide], output_path: str, css_path: str = None):
    import re
    
    # regex to find mermaid blocks: ```mermaid ... ```
    # Using DOTALL so . matches newlines
    mermaid_pattern = re.compile(r'```mermaid\s+(.*?)```', re.DOTALL)
    
    for slide in slides:
        # Pre-process: Extract mermaid blocks to prevent codehilite from messing them up
        mermaid_blocks = []
        
        def replace_mermaid(match):
            placeholder = f"MERMAID_PLACEHOLDER_{len(mermaid_blocks)}"
            # Keep the content, but strip whitespace potentially
            content = match.group(1).strip()
            mermaid_blocks.append(content)
            return placeholder

        # Temporarily replace mermaid blocks
        processed_content = mermaid_pattern.sub(replace_mermaid, slide.content)
        
        # Render markdown
        html = markdown.markdown(processed_content, extensions=['fenced_code', 'codehilite'])
        
        # Restore mermaid blocks as <pre class="mermaid">
        for i, block_content in enumerate(mermaid_blocks):
            # Escape HTML entities in the graph definition just in case, though mermaid usually handles them?
            # actually mermaid needs raw text usually, but inside HTML it might need escaping if it contains < or >
            # Let's trust the raw block content but be careful about HTML structure.
            # <pre class="mermaid"> needs the raw text.
            mermaid_html = f'<pre class="mermaid">{block_content}</pre>'
            html = html.replace(f"MERMAID_PLACEHOLDER_{i}", mermaid_html)
            
        slide.html_content = html

    # Load CSS
    css_content = ""
    if css_path and os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    else:
        # Default CSS (Corporate Style)
        css_content = """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        @page { size: 1920px 1080px; margin: 0; }

        body { 
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            background: #f0f2f5; 
            color: #334155; 
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
        }

        blockquote {
            border-left: 8px solid #3b82f6;
            padding-left: 40px;
            font-style: italic;
            color: #475569;
            font-size: 48px;
            margin: 80px 0;
        }

        pre.mermaid { 
            background: transparent; 
            display: flex; 
            justify-content: center; 
            margin-top: 40px;
        }
        """

    # Render HTML
    template = Template(HTML_TEMPLATE)
    html_string = template.render(slides=slides, css=css_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_string)

def export_to_pdf_playwright(html_path: str, pdf_path: str):
    """
    Converts a local HTML file to PDF using Playwright.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
         raise ImportError("Playwright is missing. Run 'pip install playwright' and 'playwright install'.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # file:// protocol requires absolute path
        abs_html_path = os.path.abspath(html_path)
        page.goto(f"file://{abs_html_path}")
        # Wait for mermaid or other content if needed?
        page.wait_for_load_state("networkidle") 
        # Generate PDF
        page.pdf(path=pdf_path, width="1920px", height="1080px", print_background=True)
        browser.close()
