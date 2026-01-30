#!/usr/bin/env python3

# File: pydebugger/syntax.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-05
# Description: 
# License: MIT

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import Terminal256Formatter, TerminalTrueColorFormatter
from pygments.style import Style
from pygments.styles import get_style_by_name
from pygments.token import Token
import textwrap
import re

class Syntax:
    def __init__(
        self,
        value,
        lexer="auto",
        theme="default",
        line_numbers=False,
        tab_size=4,
        code_width=80,
        word_wrap=False,
        true_color=False,
        start_line=1,
        line_number_format="{:>4}: ",
        highlight_line=None
    ):
        """
        Initialize Syntax object for code highlighting.
        
        Args:
            value (str): The code to highlight
            lexer (str): Name of the lexer or 'auto' for auto-detection
            theme (str): Pygments theme name or custom style
            line_numbers (bool or str): 
                False: no line numbers
                True: line numbers starting from start_line
                "relative": relative line numbers
                "both": absolute and relative line numbers
            tab_size (int): Tab size for indentation
            code_width (int): Maximum width for code wrapping
            word_wrap (bool): Whether to wrap long lines
            true_color (bool): Use true color (24-bit) if terminal supports
            start_line (int): Starting line number (default: 1)
            line_number_format (str): Format string for line numbers
            highlight_line (int or list): Line number(s) to highlight
        """
        self.value = value
        self.lexer_name = lexer
        self.theme = theme
        self.line_numbers = line_numbers
        self.tab_size = tab_size
        self.code_width = code_width
        self.word_wrap = word_wrap
        self.true_color = true_color
        self.start_line = start_line
        self.line_number_format = line_number_format
        self.highlight_line = highlight_line
        
        # Process tabs
        if tab_size != 4:
            self.value = self.value.replace('\t', ' ' * tab_size)
        
        # Calculate line count
        self.line_count = len(self.value.split('\n'))
        
        # Setup lexer
        self._setup_lexer()
        
        # Setup formatter and style
        self._setup_formatter()
    
    @classmethod
    def print(
        cls,
        value,
        lexer="auto",
        theme="default",
        line_numbers=False,
        tab_size=4,
        code_width=80,
        word_wrap=False,
        true_color=False,
        start_line=1,
        line_number_format="{:>4}: ",
        highlight_line=None,
        **kwargs
    ):
        """
        Class method to directly print syntax highlighted code.
        
        Args:
            value (str): The code to highlight
            lexer (str): Name of the lexer or 'auto' for auto-detection
            theme (str): Pygments theme name or custom style
            line_numbers (bool or str): 
                False: no line numbers
                True: line numbers starting from start_line
                "relative": relative line numbers
                "both": absolute and relative line numbers
            tab_size (int): Tab size for indentation
            code_width (int): Maximum width for code wrapping
            word_wrap (bool): Whether to wrap long lines
            true_color (bool): Use true color (24-bit) if terminal supports
            start_line (int): Starting line number (default: 1)
            line_number_format (str): Format string for line numbers
            highlight_line (int or list): Line number(s) to highlight
            **kwargs: Additional arguments for backward compatibility
        """
        # Create instance with all parameters
        instance = cls(
            value=value,
            lexer=lexer,
            theme=theme,
            line_numbers=line_numbers,
            tab_size=tab_size,
            code_width=code_width,
            word_wrap=word_wrap,
            true_color=true_color,
            start_line=start_line,
            line_number_format=line_number_format,
            highlight_line=highlight_line
        )
        
        # Print the highlighted code
        print(instance.highlight())
    
    def _setup_lexer(self):
        """Setup the appropriate lexer for the code."""
        if self.lexer_name.lower() == 'auto':
            try:
                self.lexer = guess_lexer(self.value)
                self.lexer_name = self.lexer.name.lower()
            except:
                self.lexer = get_lexer_by_name('text')
                self.lexer_name = 'text'
        else:
            try:
                self.lexer = get_lexer_by_name(self.lexer_name)
            except:
                # Fallback to text lexer if specified lexer not found
                self.lexer = get_lexer_by_name('text')
                self.lexer_name = 'text'
    
    def _setup_formatter(self):
        """Setup formatter with the specified theme."""
        # Get style
        if isinstance(self.theme, str):
            try:
                self.style = get_style_by_name(self.theme)
            except:
                self.style = get_style_by_name('default')
        elif issubclass(self.theme, Style):
            self.style = self.theme
        else:
            self.style = get_style_by_name('default')
        
        # Choose formatter based on color support
        if self.true_color:
            FormatterClass = TerminalTrueColorFormatter
        else:
            FormatterClass = Terminal256Formatter
        
        # Configure formatter options
        formatter_args = {
            'style': self.style,
        }
        
        # Handle line numbers
        if self.line_numbers:
            if self.line_numbers in ["relative", "both"]:
                # For relative line numbers, we need custom formatting
                formatter_args['linenos'] = False  # We'll handle manually  # type: ignore
            else:
                formatter_args['linenos'] = True  # type: ignore
                formatter_args['linenostart'] = self.start_line  # type: ignore
        else:
            formatter_args['linenos'] = False  # type: ignore
        
        if self.true_color:
            formatter_args['truecolor'] = True  # type: ignore
        
        self.formatter = FormatterClass(**formatter_args)  # type: ignore
    
    def _wrap_code(self, code):
        """Wrap code lines if word_wrap is enabled."""
        if not self.word_wrap or self.code_width <= 0:
            return code
        
        wrapped_lines = []
        for line in code.split('\n'):
            if len(line) <= self.code_width:
                wrapped_lines.append(line)
            else:
                # Wrap preserving indentation
                indent = len(line) - len(line.lstrip())
                initial_indent = ' ' * indent
                subsequent_indent = ' ' * (indent + 4)  # Extra indent for wrapped lines
                
                wrapped = textwrap.fill(
                    line,
                    width=self.code_width,
                    initial_indent=initial_indent,
                    subsequent_indent=subsequent_indent,
                    break_long_words=False,
                    break_on_hyphens=False
                )
                wrapped_lines.append(wrapped)
        
        return '\n'.join(wrapped_lines)
    
    def _add_line_numbers(self, highlighted_code):
        """Add line numbers to the highlighted code."""
        if not self.line_numbers:
            return highlighted_code
        
        lines = highlighted_code.split('\n')
        total_lines = len(lines)
        
        # Calculate max digits for formatting
        max_line_num = self.start_line + total_lines - 1
        digits = len(str(max_line_num))
        
        # Update format string if dynamic width is desired
        if '{:' in self.line_number_format:
            # User provided custom format, use as is
            fmt = self.line_number_format
        else:
            # Create dynamic format based on line count
            fmt = f"{{:>{digits}}}: "
        
        result_lines = []
        
        for i, line in enumerate(lines):
            line_num = self.start_line + i
            
            if self.line_numbers == "relative":
                # Relative line numbers (like in vim)
                rel_num = i + 1
                line_prefix = fmt.format(rel_num)
            elif self.line_numbers == "both":
                # Both absolute and relative
                rel_num = i + 1
                abs_prefix = f"{line_num:>{digits}}"
                rel_prefix = f"{rel_num:>{digits}}"
                line_prefix = f"{abs_prefix} {rel_prefix}: "
            else:
                # Absolute line numbers
                line_prefix = fmt.format(line_num)
            
            # Check if this line should be highlighted
            is_highlighted = False
            if self.highlight_line is not None:
                if isinstance(self.highlight_line, int):
                    is_highlighted = (line_num == self.highlight_line)
                elif isinstance(self.highlight_line, (list, tuple, set)):
                    is_highlighted = (line_num in self.highlight_line)
            
            if is_highlighted:
                # Add highlight indicator (you can customize this)
                line_prefix = f"\033[1;41m{line_prefix}\033[0m"
            
            result_lines.append(f"{line_prefix}{line}")
        
        return '\n'.join(result_lines)
    
    def highlight(self):
        """Highlight the code and return formatted string."""
        # Wrap code if needed
        code_to_highlight = self._wrap_code(self.value)
        
        # Highlight the code
        highlighted = highlight(code_to_highlight, self.lexer, self.formatter)
        
        # Add line numbers if needed (for custom formats)
        if self.line_numbers in ["relative", "both"]:
            highlighted = self._add_line_numbers(highlighted)
        
        return highlighted
    
    def to_string(self):
        """Alias for highlight() for convenience."""
        return self.highlight()
    
    def __str__(self):
        """String representation returns highlighted code."""
        return self.highlight()
    
    def __repr__(self):
        """Representation showing configuration."""
        return (f"Syntax(value=..., lexer='{self.lexer_name}', "
                f"theme='{self.theme if isinstance(self.theme, str) else self.theme.__name__}', "
                f"line_numbers={repr(self.line_numbers)}, start_line={self.start_line}, "
                f"tab_size={self.tab_size}, code_width={self.code_width}, "
                f"word_wrap={self.word_wrap})")
    
    def print_instance(self, **kwargs):
        """
        Instance method to print with optional overrides.
        
        Args:
            **kwargs: Parameters to override from current instance
        """
        if kwargs:
            # Create a copy of current configuration with overrides
            config = self.get_config()
            config.update(kwargs)
            
            # Create a new instance with overridden config
            temp_instance = self.__class__(self.value, **config)
            print(temp_instance.highlight())
        else:
            # Use current instance configuration
            print(self.highlight())
    
    def get_info(self):
        """Get information about the current configuration."""
        return {
            'lexer': self.lexer_name,
            'theme': self.theme if isinstance(self.theme, str) else self.theme.__name__,
            'line_numbers': self.line_numbers,
            'start_line': self.start_line,
            'tab_size': self.tab_size,
            'code_width': self.code_width,
            'word_wrap': self.word_wrap,
            'true_color': self.true_color,
            'highlight_line': self.highlight_line,
            'line_count': self.line_count,
            'char_count': len(self.value)
        }
    
    def get_config(self):
        """Get configuration dictionary for recreating instance."""
        return {
            'lexer': self.lexer_name,
            'theme': self.theme,
            'line_numbers': self.line_numbers,
            'tab_size': self.tab_size,
            'code_width': self.code_width,
            'word_wrap': self.word_wrap,
            'true_color': self.true_color,
            'start_line': self.start_line,
            'line_number_format': self.line_number_format,
            'highlight_line': self.highlight_line
        }
    
    def change_lexer(self, new_lexer):
        """Change the lexer after initialization."""
        self.lexer_name = new_lexer
        self._setup_lexer()
        return self
    
    def change_theme(self, new_theme):
        """Change the theme after initialization."""
        self.theme = new_theme
        self._setup_formatter()
        return self
    
    def change_line_numbers(self, setting, start_line=None):
        """Change line number settings."""
        self.line_numbers = setting
        if start_line is not None:
            self.start_line = start_line
        self._setup_formatter()
        return self
    
    def highlight_lines(self, lines):
        """Set which lines to highlight."""
        self.highlight_line = lines
        return self
    
    @classmethod
    def available_themes(cls):
        """Get list of available themes."""
        from pygments.styles import get_all_styles
        return list(get_all_styles())
    
    @classmethod
    def available_lexers(cls):
        """Get list of available lexers."""
        from pygments.lexers import get_all_lexers
        return [lexer[0] for lexer in get_all_lexers()]
    
    @staticmethod
    def detect_language(code):
        """Detect programming language of the code."""
        try:
            lexer = guess_lexer(code)
            return lexer.name, lexer.aliases
        except:
            return "Text", ["text"]


# Simple test function
def test_syntax():
    """Test function to demonstrate Syntax class usage."""
    code = """def hello():
    return "Hello, World!"

print(hello())"""
    
    print("=" * 80)
    print("TEST 1: Class method print (langsung tanpa instance)")
    print("=" * 80)
    Syntax.print(
        value=code,
        lexer="python",
        theme="monokai",
        line_numbers=True,
        start_line=1
    )
    
    print("\n" + "=" * 80)
    print("TEST 2: Create instance then print")
    print("=" * 80)
    syntax = Syntax(
        value=code,
        lexer="python",
        theme="solarized-dark",
        line_numbers="relative"  # type: ignore
    )
    syntax.print_instance()
    
    print("\n" + "=" * 80)
    print("TEST 3: Instance with override")
    print("=" * 80)
    syntax.print_instance(theme="vim", line_numbers=True, start_line=10)
    
    print("\n" + "=" * 80)
    print("TEST 4: Direct string conversion")
    print("=" * 80)
    print(Syntax("const x = 10;", lexer="javascript", theme="github-dark"))


# Main execution
if __name__ == "__main__":
    test_syntax()

    code = """def Console():
    HAS_RICH = False
    HAS_MAKE_COLORS = False
    console = None  # type: ignore
    Table = None
    box = None
    Syntax = None

    try:
        from rich.console import Console
        console = Console(width=os.get_terminal_size()[0])  # type: ignore
        from rich.syntax import Syntax
        from rich import box
        from rich.table import Table
        HASH_RICH = True
    except:
        try:
                from make_colors import make_colors, Console  # type: ignore
                console = Console()
                HAS_MAKE_COLORS = True
        except:
                pass

    if not console:
        class console:
                def print(self, msg):
                        print(msg)

    return HAS_RICH, HAS_MAKE_COLORS, console, Table, box, Syntax

"""
    # Basic
    syntax = Syntax(code, lexer="python", theme="fruity", line_numbers=True)
    print(syntax)

    # With all options
    syntax = Syntax(
        value=code,
        lexer="python",
        theme="solarized-dark",
        line_numbers=True,
        tab_size=2,
        code_width=80,
        word_wrap=True,
        true_color=True
    )

    # Print directly
    # syntax.print()
    # print(syntax)
    Syntax.print(
        value=code,
        lexer="python",
        theme="solarized-dark",
        line_numbers=True,
        tab_size=2,
        code_width=80,
        word_wrap=True,
        true_color=True
    )

    # Get highlighted string
    highlighted = syntax.highlight()

    # Change settings
    syntax.change_lexer("javascript").change_theme("friendly")