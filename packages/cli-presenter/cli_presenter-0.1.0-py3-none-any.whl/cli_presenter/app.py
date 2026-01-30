from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Markdown, Static
from textual.containers import Container, ScrollableContainer
from textual.binding import Binding
from textual import work
import asyncio
from typing import List
import os
from .parser import Slide
from .ascii_renderer import render_mermaid_to_ascii
import re

class SlideWidget(ScrollableContainer):
    def __init__(self, slide: Slide, **kwargs):
        super().__init__(**kwargs)
        self.slide = slide
        self.classes = f"layout-{slide.metadata.get('layout', 'default')}"

    def compose(self) -> ComposeResult:
        yield Markdown(self.slide.content, id="slide-content")

    def on_mount(self) -> None:
        """Check for mermaid blocks to replace async."""
        # Check for mermaid block
        mermaid_pattern = re.compile(r'```mermaid\s+(.*?)```', re.DOTALL)
        match = mermaid_pattern.search(self.slide.content)
        if match:
             # Pass the full matched block (group 0) and the inner code (group 1)
             self.load_mermaid_ascii(match.group(0), match.group(1))

    @work(exclusive=True)
    async def load_mermaid_ascii(self, full_block: str, mermaid_code: str) -> None:
        """Background worker to render mermaid."""
        try:
            # New Strategy: Semantic Parsing
            from .mermaid_parser import MermaidParser
            
            def run_parse():
                p = MermaidParser(mermaid_code)
                return p.render_text()
                
            loop = asyncio.get_running_loop()
            ascii_art = await loop.run_in_executor(None, run_parse)
            
            # Use exact string replacement
            new_content = self.slide.content.replace(full_block, f"```text\n{ascii_art}\n```")
            
            # Update the widget
            markdown_widget = self.query_one("#slide-content", Markdown)
            markdown_widget.update(new_content)

        except Exception as e:
            with open("error.log", "a") as f:
                f.write(f"TUI Error: {e}\n")

class PresenterApp(App):
    """A terminal-based presentation tool."""
    
    CSS = """
    SlideWidget {
        width: 100%;
        height: 100%;
        padding: 2 4;
    }
    
    Markdown {
        width: 100%;
        margin: 0 0;
    }
    
    /* Layouts */
    .layout-title {
        align: center middle;
        text-align: center;
    }
    
    .layout-title Markdown {
        text-align: center;
    }

    .layout-center {
        align: center middle;
    }
    
    /* Global style tweaks */
    Screen {
        layers: base overlay;
    }
    """
    
    BINDINGS = [
        Binding("right,space,l", "next_slide", "Next"),
        Binding("left,h", "prev_slide", "Previous"),
        Binding("q,escape", "quit", "Quit"),
        Binding("f", "toggle_fullscreen", "Fullscreen"),
    ]

    def __init__(self, slides: List[Slide], **kwargs):
        super().__init__(**kwargs)
        self.slides = slides
        self.current_slide_index = 0

    def compose(self) -> ComposeResult:
        yield Footer()
        if self.slides:
            yield SlideWidget(self.slides[0], id="current-slide")
        else:
            yield Static("No slides found.")

    def on_mount(self):
        self.title = "CLI Presenter"
        self._update_slide_title()
        
        # Load external theme if present
        if os.path.exists("theme.tcss"):
            self.stylesheet.read("theme.tcss")

    def _update_slide_title(self):
         self.sub_title = f"Slide {self.current_slide_index + 1} / {len(self.slides)}"

    async def update_slide(self):
        slide_widget = self.query_one("#current-slide", SlideWidget)
        await slide_widget.remove()
        
        new_slide = SlideWidget(self.slides[self.current_slide_index], id="current-slide")
        self.mount(new_slide)
        self._update_slide_title()

    async def action_next_slide(self):
        if self.current_slide_index < len(self.slides) - 1:
            self.current_slide_index += 1
            await self.update_slide()

    async def action_prev_slide(self):
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            await self.update_slide()

