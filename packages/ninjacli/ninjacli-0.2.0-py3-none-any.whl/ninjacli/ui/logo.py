from rich.console import Console
from rich.text import Text

LOGO_ART = """
 ███    ██ ██ ███    ██      ██  █████        ██████ ██      ██ 
 ████   ██ ██ ████   ██      ██ ██   ██      ██      ██      ██ 
 ██ ██  ██ ██ ██ ██  ██      ██ ███████      ██      ██      ██ 
 ██  ██ ██ ██ ██  ██ ██ ██   ██ ██   ██      ██      ██      ██ 
 ██   ████ ██ ██   ████  █████  ██   ██       ██████ ███████ ██ 
"""

def get_logo_text(console: Console | None = None):
    console = console or Console()
    
    colors = [
    "#53f58e",  
    "#4bf3be",  
    "#42f0b3",  
    "#3ae8a8",  
    "#2fd995",  
    ]
    
    lines = LOGO_ART.splitlines()
    text = Text(justify="center")
    for i, line in enumerate(lines):
        color_index = min(i, len(colors) - 1)
        text.append(line + "\n", style=f"bold {colors[color_index]}")
    return text