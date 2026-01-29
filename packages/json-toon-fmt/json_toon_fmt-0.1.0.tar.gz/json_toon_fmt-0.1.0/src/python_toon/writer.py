"""
Line writter module.
"""

class LineWriter:

    def __init__(self, spacing: int = 2):
        self.lines: list[str] = []
        self.spacing = spacing
    
    def add(self, depth: int, content: str):
        spacing= ' ' * (depth * self.spacing)
        self.lines.append(f"{spacing}{content}")
    
    def to_string(self) -> str:
        return '\n'.join(self.lines)
    
