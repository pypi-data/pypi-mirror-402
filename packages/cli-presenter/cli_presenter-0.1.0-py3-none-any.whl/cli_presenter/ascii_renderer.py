import io
import re
from functools import lru_cache
try:
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:
    Image = None

# Denser block char set for diagrams
# Standard comprehensive gradient for detail
ASCII_CHARS = ["@", "%", "#", "*", "+", "=", "-", ":", ".", " ", " "]

def pixels_to_ascii(image, width=150):
    # Handle transparency
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    
    # 1. Grayscale
    image = image.convert("L")
    
    # 2. Moderate Contrast (Text needs to not be washed out, but not binary)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    
    # Resize
    w, h = image.size
    aspect = h / w / 0.5 
    new_h = int(width * aspect)
    image = image.resize((width, new_h), Image.Resampling.LANCZOS)
    
    pixels = image.getdata()
    
    # Map
    chars = []
    for p in pixels:
        # Simple gradient mapping
        idx = int((p / 255) * (len(ASCII_CHARS) - 1))
        # Ensure distinct background
        if p > 240: 
             chars.append(" ")
        else:
             chars.append(ASCII_CHARS[idx])
        
    result = ""
    for i in range(0, len(chars), width):
        result += "".join(chars[i:i+width]) + "\n"
        
    return result

@lru_cache(maxsize=32)
def render_mermaid_to_ascii(mermaid_code: str) -> str:
    """
    Renders mermaid code to ASCII using Playwright.
    Cached to avoid re-spawning browser.
    """
    try:
        from playwright.sync_api import sync_playwright
        # Image is imported at top level
    except ImportError:
        return "Install 'playwright' and 'Pillow' for ASCII diagrams."

    html = f"""
    <!DOCTYPE html>
    <body>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        <div class="mermaid">
        {mermaid_code}
        </div>
    </body>
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # Use high DPI for sharper source text
            context = browser.new_context(device_scale_factor=2.0)
            page = context.new_page()
            page.set_content(html)
            try:
                page.wait_for_selector('.mermaid svg', timeout=3000)
                element = page.locator('.mermaid')
                png_bytes = element.screenshot()
                
                image = Image.open(io.BytesIO(png_bytes))
                return pixels_to_ascii(image)
                
            except Exception as e:
                return f"Error rendering mermaid: {e}"
            finally:
                browser.close()
    except Exception as e:
        return f"Playwright Error: {e}"
