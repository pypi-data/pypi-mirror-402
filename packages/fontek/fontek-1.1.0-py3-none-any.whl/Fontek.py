import msvcrt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import track, Progress, BarColumn, TimeRemainingColumn
from rich.text import Text
from rich import print as rprint
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.rule import Rule
from rich.columns import Columns
from rich.tree import Tree
from rich.style import Style
import time

Colors = {
    # Reds
    "red"        : "255;0;0",
    "maroon"     : "128;0;0",
    "crimson"    : "220;20;60",
    "pink"       : "255;192;203",
    "hotpink"    : "255;105;180",

    # Oranges & Browns
    "orange"     : "255;165;0",
    "darkorange" : "255;140;0",
    "brown"      : "165;42;42",
    "darkbrown"  : "100;64;0",
    "chocolate"  : "210;105;30",
    "coral"      : "255;127;80",

    # Yellows
    "yellow"     : "255;255;0",
    "gold"       : "255;215;0",
    "khaki"      : "240;230;140",

    # Greens
    "lightgreen" : "144;238;144",
    "darkgreen"  : "0;100;0",
    "green"      : "0;255;0",
    "lime"       : "50;205;50",
    "olive"      : "128;128;0",
    "seagreen"   : "46;139;87",

    # Blues
    "blue"       : "0;0;255",
    "navy"       : "0;0;128",
    "royalblue"  : "65;105;225",
    "skyblue"    : "135;206;235",
    "cyan"       : "0;255;255",
    "teal"       : "0;128;128",

    # Purples
    "purple"     : "128;0;128",
    "violet"     : "238;130;238",
    "indigo"     : "75;0;130",
    "magenta"    : "255;0;255",
    "orchid"     : "218;112;214",

    # Grays & Neutrals
    "black"      : "0;0;0",
    "gray"       : "128;128;128",
    "darkgray"   : "169;169;169",
    "lightgray"  : "211;211;211",
    "white"      : "255;255;255",
    "silver"     : "192;192;192"
}
def ColorPrint(text=None, fg=None, bg=None, font=None, end=None):
    fg_code = f"\033[38;2;{Colors[fg.lower()]}m" if isinstance(fg, str) else ""
    bg_code = f"\033[48;2;{Colors[bg.lower()]}m" if isinstance(bg, str) else ""
    style = ""
    if font == "bold": style = "\033[1m"
    elif font == "italic": style = "\033[3m"
    elif font == "underline": style = "\033[4m"

    print(f"{style}{fg_code}{bg_code}{text}\033[0m") if not end else print(f"{style}{fg_code}{bg_code}{text}\033[0m", end=end)

def ColorUP(text=None, fg=None, bg=None, font=None):
    fg_code = f"\033[38;2;{Colors[fg.lower()]}m" if isinstance(fg, str) else ""
    bg_code = f"\033[48;2;{Colors[bg.lower()]}m" if isinstance(bg, str) else ""
    
    style = ""
    if font == "bold":
        style = "\033[1m"
    elif font == "italic":
        style = "\033[3m"
    elif font == "underline":
        style = "\033[4m"

    return f"{style}{fg_code}{bg_code}{text}\033[0m"

def ColorInput(prompt=None, questionFG=None, questionBG=None, questionFont=None,
               answerFG=None, answerBG=None, answerFont=None, styleReturn=False):
    
    q_fg = f"\033[38;2;{Colors[questionFG.lower()]}m" if questionFG else ""
    q_bg = f"\033[48;2;{Colors[questionBG.lower()]}m" if questionBG else ""
    q_style = ""
    if questionFont == "bold": q_style = "\033[1m"
    elif questionFont == "italic": q_style = "\033[3m"
    elif questionFont == "underline": q_style = "\033[4m"

    if prompt:
        print(f"{q_style}{q_fg}{q_bg}{prompt}\033[0m", end="", flush=True)

    chars = []
    styled_chars = []
    cursor_pos = 0
    
    while True:
        key = msvcrt.getch()

        if key == b'\r':
            print()
            break
        elif key == b'\x08':
            if cursor_pos > 0:
                chars.pop(cursor_pos - 1)
                styled_chars.pop(cursor_pos - 1)
                cursor_pos -= 1
                print("\b \b", end="", flush=True)
        elif key in (b"\x00", b"\xe0"):
            second_byte = msvcrt.getch()
            if second_byte == b'K':  # Left arrow
                if cursor_pos > 0:
                    cursor_pos -= 1
                    print("\033[D", end="", flush=True)
            elif second_byte == b'M':  # Right arrow
                if cursor_pos < len(chars):
                    cursor_pos += 1
                    print("\033[C", end="", flush=True)
            elif second_byte == b'H':  # Up arrow
                pass
            elif second_byte == b'P':  # Down arrow
                pass
        else:
            ch = key.decode(errors="ignore")
            chars.insert(cursor_pos, ch)

            a_fg = f"\033[38;2;{Colors[answerFG.lower()]}m" if answerFG else ""
            a_bg = f"\033[48;2;{Colors[answerBG.lower()]}m" if answerBG else ""
            a_style = ""
            if answerFont == "bold": a_style = "\033[1m"
            elif answerFont == "italic": a_style = "\033[3m"
            elif answerFont == "underline": a_style = "\033[4m"

            styled_char = f"{a_style}{a_fg}{a_bg}{ch}\033[0m"
            styled_chars.insert(cursor_pos, styled_char)
            
            # Rebuild display from cursor position
            display_from_cursor = "".join(styled_chars[cursor_pos:])
            print(styled_char + display_from_cursor, end="", flush=True)
            
            # Move cursor back to correct position
            for _ in range(len(display_from_cursor)):
                print("\b", end="", flush=True)
            
            cursor_pos += 1
    
    if styleReturn:
        return "".join(styled_chars)
    else:
        return "".join(chars)

def ColorInputEcho(prompt=None, questionFG=None, questionBG=None, questionFont=None,
                   answerFG=None, answerBG=None, answerFont=None, styleReturn=False):
    q_fg = f"\033[38;2;{Colors[questionFG.lower()]}m" if questionFG else ""
    q_bg = f"\033[48;2;{Colors[questionBG.lower()]}m" if questionBG else ""
    q_style = ""
    if questionFont == "bold": q_style = "\033[1m"
    elif questionFont == "italic": q_style = "\033[3m"
    elif questionFont == "underline": q_style = "\033[4m"

    if prompt:
        print(f"{q_style}{q_fg}{q_bg}{prompt}\033[0m", end="", flush=True)

    chars = []
    styled_chars = []
    cursor_pos = 0
    print()
    
    while True:
        key = msvcrt.getch()

        if key == b'\r':  # Enter
            print()
            break
        elif key == b'\x08':  # Backspace
            if cursor_pos > 0:
                chars.pop(cursor_pos - 1)
                styled_chars.pop(cursor_pos - 1)
                cursor_pos -= 1
                # Redraw line
                print("\r" + "".join(styled_chars) + " ", end="", flush=True)
                # Move cursor to correct position
                print("\r" + "".join(styled_chars[:cursor_pos]), end="", flush=True)
        elif key in (b"\x00", b"\xe0"):  # Special keys (arrows, F-keys)
            second_byte = msvcrt.getch()
            if second_byte == b'K':  # Left arrow
                if cursor_pos > 0:
                    cursor_pos -= 1
                    print("\r" + "".join(styled_chars[:cursor_pos]), end="", flush=True)
            elif second_byte == b'M':  # Right arrow
                if cursor_pos < len(chars):
                    cursor_pos += 1
                    print("\r" + "".join(styled_chars[:cursor_pos]), end="", flush=True)
            elif second_byte == b'H':  # Up arrow - move to start
                cursor_pos = 0
                print("\r" + "".join(styled_chars[:cursor_pos]), end="", flush=True)
            elif second_byte == b'P':  # Down arrow - move to end
                cursor_pos = len(chars)
                print("\r" + "".join(styled_chars), end="", flush=True)
        else:
            ch = key.decode(errors="ignore")
            chars.insert(cursor_pos, ch)

            a_fg = f"\033[38;2;{Colors[answerFG.lower()]}m" if answerFG else ""
            a_bg = f"\033[48;2;{Colors[answerBG.lower()]}m" if answerBG else ""
            a_style = ""
            if answerFont == "bold": a_style = "\033[1m"
            elif answerFont == "italic": a_style = "\033[3m"
            elif answerFont == "underline": a_style = "\033[4m"

            styled_char = f"{a_style}{a_fg}{a_bg}{ch}\033[0m"
            styled_chars.insert(cursor_pos, styled_char)
            
            # Redraw entire line and reposition cursor
            print("\r" + "".join(styled_chars), end="", flush=True)
            cursor_pos += 1
            
            # Move cursor back to position after the inserted character
            for _ in range(len(styled_chars) - cursor_pos):
                print("\b", end="", flush=True)

    if styleReturn:
        return "".join(styled_chars)
    else:
        return "".join(chars)

def RainbowPrint(text=None):
    rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    for i, ch in enumerate(text):
        color = rainbow[i % len(rainbow)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        print(f"{fg_code}{ch}\033[0m", end="")
    print()

def ColorSeriesPrint(text=None, colors=None):
    for i, ch in enumerate(text):
        color = colors[i % len(colors)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        print(f"{fg_code}{ch}\033[0m", end="")
    print()

def RainbowUP(text=None):
    rainbow = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    styled = []
    for i, ch in enumerate(text):
        color = rainbow[i % len(rainbow)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        styled.append(f"{fg_code}{ch}\033[0m")
    return "".join(styled)

def ColorSeriesUP(text=None, colors=None):
    styled = []
    for i, ch in enumerate(text):
        color = colors[i % len(colors)]
        fg_code = f"\033[38;2;{Colors[color]}m"
        styled.append(f"{fg_code}{ch}\033[0m")
    return "".join(styled)

# ==================== RICH LIBRARY FEATURES ====================

class RichFeatures:
    def __init__(self):
        self.console = Console()

    def RichPrint(self, text=None, style=None, justify="default"):
        """Print text with rich styling
        
        Args:
            text: Text to print
            style: Rich style string (e.g., "bold red", "italic blue on white")
            justify: Text alignment ("default", "left", "center", "right")
        """
        self.console.print(text, style=style, justify=justify)

    def RichTable(self, title=None, rows=None, columns=None, style="bold white on blue"):
        """Create and display a rich table
        
        Args:
            title: Table title
            rows: List of tuples/lists representing rows
            columns: List of column headers
            style: Header style
        
        Returns:
            None (displays table directly)
        """
        table = Table(title=title, style=style)
        
        if columns:
            for col in columns:
                table.add_column(col)
        
        if rows:
            for row in rows:
                table.add_row(*[str(item) for item in row])
        
        self.console.print(table)

    def RichTableReturn(self, title=None, rows=None, columns=None, style="bold white on blue"):
        """Create a rich table and return it without printing
        
        Args:
            title: Table title
            rows: List of tuples/lists representing rows
            columns: List of column headers
            style: Header style
        
        Returns:
            Table object
        """
        table = Table(title=title, style=style)
        
        if columns:
            for col in columns:
                table.add_column(col)
        
        if rows:
            for row in rows:
                table.add_row(*[str(item) for item in row])
        
        return table

    def RichPanel(self, text=None, title=None, style="bold blue", border_style="blue"):
        """Display text in a rich panel
        
        Args:
            text: Text to display
            title: Panel title
            style: Panel style
            border_style: Border style
        """
        panel = Panel(text, title=title, style=style, border_style=border_style)
        self.console.print(panel)

    def RichPanelReturn(self, text=None, title=None, style="bold blue", border_style="blue"):
        """Create a rich panel and return it without printing
        
        Args:
            text: Text to display
            title: Panel title
            style: Panel style
            border_style: Border style
        
        Returns:
            Panel object
        """
        return Panel(text, title=title, style=style, border_style=border_style)

    def RichSyntax(self, code=None, language="python", theme="monokai", line_numbers=True):
        """Display syntax-highlighted code
        
        Args:
            code: Code string
            language: Programming language
            theme: Syntax theme
            line_numbers: Whether to show line numbers
        """
        syntax = Syntax(code, language, theme=theme, line_numbers=line_numbers)
        self.console.print(syntax)

    def RichSyntaxReturn(self, code=None, language="python", theme="monokai", line_numbers=True):
        """Create syntax-highlighted code and return without printing
        
        Args:
            code: Code string
            language: Programming language
            theme: Syntax theme
            line_numbers: Whether to show line numbers
        
        Returns:
            Syntax object
        """
        return Syntax(code, language, theme=theme, line_numbers=line_numbers)

    def RichRule(self, title="", style="blue"):
        """Display a horizontal rule
        
        Args:
            title: Optional title on the rule
            style: Rule style
        """
        self.console.print(Rule(title=title, style=style))

    def RichText(self, text=None, style=None):
        """Create a rich text object for advanced styling
        
        Args:
            text: Text content
            style: Text style
        
        Returns:
            Text object
        """
        return Text(text, style=style)

    def RichProgress(self, sequence=None, description="Processing"):
        """Display a progress bar
        
        Args:
            sequence: Iterable to track
            description: Progress description
        
        Returns:
            Generator yielding items from sequence
        """
        return track(sequence, description=description)

    def RichProgressManual(self, total=100, description="Processing"):
        """Create a manual progress bar for custom usage
        
        Args:
            total: Total number of steps
            description: Progress description
        
        Returns:
            Progress object context manager
        """
        return Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
        )

    def RichLayout(self):
        """Create a rich layout for complex terminal UIs
        
        Returns:
            Layout object
        """
        return Layout()

    def RichTree(self, label, style="bold blue"):
        """Create a tree structure for hierarchical display
        
        Args:
            label: Root label
            style: Tree style
        
        Returns:
            Tree object
        """
        return Tree(label, style=style)

    def RichColumns(self, *renderables, equal=True, expand=True):
        """Display multiple renderables side by side
        
        Args:
            *renderables: Rich renderable objects
            equal: Make columns equal width
            expand: Expand to fill width
        
        Returns:
            Columns object
        """
        return Columns(renderables, equal=equal, expand=expand)

    def RichAlign(self, renderable, align="center"):
        """Align a renderable object
        
        Args:
            renderable: Rich renderable object
            align: Alignment ("left", "center", "right")
        
        Returns:
            Aligned renderable
        """
        return Align(renderable, align=align)

    def RichJSON(self, data):
        """Pretty print JSON data with syntax highlighting
        
        Args:
            data: Dictionary or JSON-serializable data
        """
        import json
        json_str = json.dumps(data, indent=2)
        self.console.print_json(data=json_str)

    def RichStatus(self, status_text):
        """Create a status indicator (context manager)
        
        Args:
            status_text: Status text to display
        
        Returns:
            Status context manager
        """
        return self.console.status(status_text)

    def RichLog(self):
        """Get a rich logger for logging messages
        
        Returns:
            Console object for logging
        """
        return self.console

    def RichSpinner(self, text="Loading", delay=0.1):
        """Create a spinner animation
        
        Args:
            text: Text to display with spinner
            delay: Delay between frames
        """
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for char in spinner_chars:
            self.console.print(f"[cyan]{char}[/cyan] {text}", end="\r")
            time.sleep(delay)
        self.console.print(" " * 50, end="\r")

    def RichBox(self, text=None, fg_color="cyan", bg_color=None, border_style="rounded"):
        """Create a colored box around text
        
        Args:
            text: Text to box
            fg_color: Foreground color
            bg_color: Background color
            border_style: Box style ("rounded", "square", "double", "thick")
        """
        style_str = fg_color if not bg_color else f"{fg_color} on {bg_color}"
        panel = Panel(text, style=style_str, expand=False)
        self.console.print(panel)

    def RichAlert(self, message=None, alert_type="info"):
        """Display an alert message
        
        Args:
            message: Alert message
            alert_type: Type of alert ("info", "warning", "error", "success")
        """
        styles = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        icons = {
            "info": "ℹ",
            "warning": "⚠",
            "error": "✗",
            "success": "✓"
        }
        
        style = styles.get(alert_type, "blue")
        icon = icons.get(alert_type, "•")
        self.console.print(f"[{style}]{icon} {message}[/{style}]")

    def RichInputStyled(self, prompt="", prompt_style="bold cyan", input_style="bold white"):
        """Enhanced input with rich styling
        
        Args:
            prompt: Input prompt
            prompt_style: Prompt style
            input_style: Input text style
        
        Returns:
            User input string
        """
        self.console.print(prompt, style=prompt_style, end="")
        user_input = input()
        return user_input