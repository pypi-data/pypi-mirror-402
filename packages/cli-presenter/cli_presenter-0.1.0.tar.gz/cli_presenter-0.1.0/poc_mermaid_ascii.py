
import sys
from playwright.sync_api import sync_playwright
# Default PIL is often installed as 'Pillow' but imported as 'PIL'
try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Please 'pip install Pillow'")
    sys.exit(1)

MERMAID_HTML = """
<!DOCTYPE html>
<html>
<body>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true });
    </script>
    <div class="mermaid">
    graph TD;
        A[Start] -->|Process| B(Do Work);
        B --> C{Decision};
        C -->|Yes| D[Success];
        C -->|No| E[Failure];
    </div>
</body>
</html>
"""

ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]

def resize_image(image, new_width=100):
    width, height = image.size
    ratio = height / width / 1.65  # Adjust for terminal character aspect ratio
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

def grayify(image):
    grayscale_image = image.convert("L")
    return grayscale_image

def pixels_to_ascii(image):
    pixels = image.getdata()
    characters = "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])
    return characters

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(MERMAID_HTML)
        # Wait for mermaid to render
        try:
            page.wait_for_selector('.mermaid svg', timeout=5000)
        except:
            print("Mermaid didn't render in time")
            return

        # Screenshot the mermaid div
        element = page.locator('.mermaid')
        png_bytes = element.screenshot()
        browser.close()

        # Write to temp file to load specific logic if needed, or just BytesIO
        import io
        image = Image.open(io.BytesIO(png_bytes))

        # Convert to ASCII
        new_width = 80
        new_image_data = pixels_to_ascii(grayify(resize_image(image, new_width)))
        
        # Format
        pixel_count = len(new_image_data)
        ascii_image = "\n".join([new_image_data[index:(index+new_width)] for index in range(0, pixel_count, new_width)])
        
        print("\n--- ASCII RENDER ---\n")
        print(ascii_image)
        print("\n--------------------\n")

if __name__ == "__main__":
    main()
