from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
import os

@dataclass
class Slide:
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)

def parse_deck(path: str) -> List[Slide]:
    """
    Parses a markdown file into a list of Slide objects.
    Splits content by separate lines containing only '---'.
    Parses metadata (key: value) at the beginning of each slide.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Presentation file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by '---' that is on its own line
    raw_slides = re.split(r'(?m)^---\s*$', content)

    slides = []
    for raw_slide in raw_slides:
        slide_text = raw_slide.strip()
        if not slide_text:
            continue
            
        # Parse metadata
        lines = slide_text.split('\n')
        metadata = {}
        content_lines = []
        parsing_metadata = True
        
        for line in lines:
            if parsing_metadata:
                # Check for key: value pair
                match = re.match(r'^([a-zA-Z0-9_-]+):\s*(.+)$', line)
                if match:
                    key = match.group(1).strip().lower()
                    value = match.group(2).strip()
                    metadata[key] = value
                else:
                    # Stop parsing metadata on first non-match or empty line
                    if line.strip() == "":
                         # empty line separates metadata from content usually, drop it if we had metadata
                         pass
                    else:
                        content_lines.append(line)
                    parsing_metadata = False
            else:
                content_lines.append(line)
        
        final_content = '\n'.join(content_lines).strip()
        slides.append(Slide(content=final_content, metadata=metadata))
    
    if not slides:
        return [Slide(content="# No Content")]

    return slides
