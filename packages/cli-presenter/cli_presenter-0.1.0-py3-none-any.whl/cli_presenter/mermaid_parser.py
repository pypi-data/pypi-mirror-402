import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class Node:
    id: str
    text: str = ""
    shape: str = "box"  # box, round, diamond

@dataclass
class Edge:
    source: str
    target: str
    label: Optional[str] = None

class MermaidParser:
    def __init__(self, code: str):
        self.code = code
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._parse()

    def _parse(self):
        # 1. Normalize
        lines = self.code.split('\n')
        
        # Regex for Nodes: A[Label] B(Label) C{Label}
        # We need to capture ID and Text and Shape
        # Shape patterns: [ ], ( ), { }
        
        # We parse line by line.
        # A line might be: A[Text] -->|Label| B(Text)
        
        # Strategy: 
        # 1. Split by arrows "-->", "---", "-.->"
        # 2. Parse individual parts as nodes
        
        arrow_pattern = re.compile(r'\s*(-+\>|={2,}\>|-+\|.*?\|-+\>|\.+>)\s*')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("graph") or line.startswith("%%"):
                continue
            
            # Remove semicolon
            if line.endswith(";"):
                line = line[:-1]
                
            # Split by arrow
            parts = arrow_pattern.split(line)
            # parts will involve [node1, arrow_separator, node2, arrow_separator, node3...]
            # because capturing group in split includes the separator
            
            if len(parts) == 1:
                # Just a node declaration? "A[Text]"
                self._parse_node(parts[0])
            else:
                # Chain: A -> B -> C
                # parts[0] is Node A
                # parts[1] is Arrow
                # parts[2] is Node B
                for i in range(0, len(parts) - 2, 2):
                    src_str = parts[i]
                    arrow_str = parts[i+1]
                    tgt_str = parts[i+2]
                    
                    src_id = self._parse_node(src_str)
                    tgt_id = self._parse_node(tgt_str)
                    
                    # Extract label from arrow if exists: -->|Label|
                    label = None
                    if "|" in arrow_str:
                         # -|Label|- or -->|Label|
                         match = re.search(r'\|(.*?)\|', arrow_str)
                         if match:
                             label = match.group(1)
                    
                    self.edges.append(Edge(src_id, tgt_id, label))

    def _parse_node(self, node_str: str) -> str:
        """Parses a node string, registers it, maps ID. Returns ID."""
        node_str = node_str.strip()
        # Check patterns
        # [box], (round), {diamond}
        
        # Regex to find syntax: ID followed by shape
        # A[Text]
        match = re.match(r'([a-zA-Z0-9_]+)(?:(\[|\(|\{)(.*?)(\]|\)|\}))', node_str)
        
        if match:
            nid = match.group(1)
            opener = match.group(2)
            text = match.group(3)
            
            shape = "box"
            if opener == "(": shape = "round"
            elif opener == "{": shape = "diamond"
            
            # Update if not exists or if this one has content
            if nid not in self.nodes or (text and not self.nodes[nid].text):
                self.nodes[nid] = Node(nid, text, shape)
            return nid
        else:
            # Just ID
            nid = node_str.split(' ')[0] # heuristic
            if nid not in self.nodes:
                self.nodes[nid] = Node(nid, nid)
            return nid

    def render_text(self) -> str:
        """Renders a text representation."""
        if not self.edges:
            return "No connections found."
            
        # Logical Flow Render
        # We try to group by Source
        output = []
        
        # Get formatting helper
        def fmt_node(nid):
            n = self.nodes.get(nid)
            txt = n.text if n.text else n.id
            if n.shape == "round": return f"({txt})"
            if n.shape == "diamond": return f"<{txt}>"
            return f"[{txt}]"
            
        def fmt_edge(label):
            if label: return f"-- {label} -->"
            return "-->"

        # Simple Edge List view (Robust for all graph types)
        for e in self.edges:
            line = f"{fmt_node(e.source)} {fmt_edge(e.label)} {fmt_node(e.target)}"
            output.append(line)
            
        return "\n".join(output)
