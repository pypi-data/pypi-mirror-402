import re
import sys
import textwrap
from typing import Any, List, Dict, Optional, Union, Iterable, Iterator, Tuple
from dataclasses import dataclass, field


@dataclass
class Column:
    """Represents a table column with formatting options."""
    header: str = ""
    footer: str = ""
    justify: str = "left"
    style: str = ""
    width: Optional[int] = None
    ratio: Optional[int] = None
    overflow: str = "fold"
    no_wrap: bool = False
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    
    def __post_init__(self):
        """Clean markup from header and footer."""
        if self.header:
            self.header = self._strip_markup(self.header)
        if self.footer:
            self.footer = self._strip_markup(self.footer)
    
    @staticmethod
    def _strip_markup(text: str) -> str:
        """Remove Rich markup from text."""
        if not text:
            return text
        return re.sub(r'\[/?[^][]*\]', '', text)


@dataclass
class Row:
    """Represents a table row with cells."""
    cells: List[Any] = field(default_factory=list)
    style: str = ""
    
    def __post_init__(self):
        """Clean markup from cell values."""
        self.cells = [self._clean_cell(cell) for cell in self.cells]
    
    @staticmethod
    def _clean_cell(cell: Any) -> str:
        """Convert cell to string and clean markup."""
        if cell is None:
            return ""
        cell_str = str(cell)
        return re.sub(r'\[/?[^][]*\]', '', cell_str)


class Table:
    """
    A fallback table implementation compatible with rich.table.Table.
    Grid tables can be with or without borders.
    """
    
    @classmethod
    def grid(
        cls,
        *,
        padding: Tuple[int, int] = (0, 1),
        pad_edge: bool = True,
        expand: bool = False,
        collapse_padding: bool = False,
        safe_box: Optional[bool] = None,
        show_borders: bool = True,  # Control borders for grid tables
    ) -> "Table":
        """
        Create a grid-style table.
        
        Args:
            padding: Padding (horizontal, vertical)
            pad_edge: Pad edges
            expand: Expand to fit width
            collapse_padding: Collapse padding
            safe_box: Safe box mode (ignored)
            show_borders: Whether to show borders
            
        Returns:
            Grid-style Table instance
        """
        return cls(
            box="grid",
            padding=padding,
            pad_edge=pad_edge,
            expand=expand,
            collapse_padding=collapse_padding,
            show_header=False,
            show_footer=False,
            show_edge=show_borders,  # Outer borders
            show_lines=show_borders,  # Inner borders
        )
    
    @classmethod
    def borderless_grid(
        cls,
        *,
        padding: Tuple[int, int] = (0, 1),
        pad_edge: bool = False,
        expand: bool = False,
        collapse_padding: bool = True,
    ) -> "Table":
        """
        Create a borderless grid-style table.
        
        Args:
            padding: Padding (horizontal, vertical)
            pad_edge: Pad edges
            expand: Expand to fit width
            collapse_padding: Collapse padding
            
        Returns:
            Borderless grid-style Table instance
        """
        return cls.grid(
            padding=padding,
            pad_edge=pad_edge,
            expand=expand,
            collapse_padding=collapse_padding,
            show_borders=False,
        )
    
    @classmethod
    def minimal(cls, **kwargs) -> "Table":
        """Create a minimal table (borderless)."""
        kwargs.setdefault('show_edge', False)
        kwargs.setdefault('show_lines', False)
        return cls(box="minimal", **kwargs)
    
    @classmethod
    def simple(cls, **kwargs) -> "Table":
        """Create a simple table (with borders)."""
        kwargs.setdefault('show_edge', True)
        kwargs.setdefault('show_lines', False)
        return cls(box="simple", **kwargs)
    
    def __init__(
        self,
        title: Optional[str] = None,
        *,
        caption: Optional[str] = None,
        width: Optional[int] = None,
        box: Optional[str] = None,
        safe_box: Optional[bool] = None,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        expand: bool = False,
        row_styles: Optional[List[str]] = None,
        title_style: Optional[str] = None,
        title_justify: str = "center",
        caption_style: Optional[str] = None,
        caption_justify: str = "center",
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        border_style: Optional[str] = None,
        pad_edge: bool = True,
        padding: Tuple[int, int] = (0, 1),
        collapse_padding: bool = False,
    ):
        """
        Initialize a new Table.
        """
        self.title = self._clean_markup(title) if title else None
        self.caption = self._clean_markup(caption) if caption else None
        self.width = width
        self.box_style = box or "regular"
        self.show_header = show_header
        self.show_footer = show_footer
        self.show_edge = show_edge
        self.show_lines = show_lines
        self.expand = expand
        self.title_justify = title_justify
        self.caption_justify = caption_justify
        self.pad_edge = pad_edge
        self.padding = padding
        self.collapse_padding = collapse_padding
        
        self.columns: List[Column] = []
        self.rows: List[Row] = []
        self._column_widths: List[int] = []
        
        # Set up box characters based on style
        self._setup_box_chars()
    
    def _setup_box_chars(self) -> None:
        """Set up box drawing characters based on table style."""
        if self.box_style == "grid":
            # Grid style - light borders
            self.box_chars = {
                "horizontal": "─",
                "vertical": "│",
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "top_tee": "┬",
                "bottom_tee": "┴",
                "left_tee": "├",
                "right_tee": "┤",
                "cross": "┼",
                "half_left": "",
                "half_right": "",
            }
        elif self.box_style == "simple":
            # Simple style - basic ASCII
            self.box_chars = {
                "horizontal": "-",
                "vertical": "|",
                "top_left": "+",
                "top_right": "+",
                "bottom_left": "+",
                "bottom_right": "+",
                "top_tee": "+",
                "bottom_tee": "+",
                "left_tee": "+",
                "right_tee": "+",
                "cross": "+",
                "half_left": "",
                "half_right": "",
            }
        elif self.box_style == "minimal":
            # Minimal style - no borders
            self.box_chars = {
                "horizontal": " ",
                "vertical": " ",
                "top_left": "",
                "top_right": "",
                "bottom_left": "",
                "bottom_right": "",
                "top_tee": "",
                "bottom_tee": "",
                "left_tee": "",
                "right_tee": "",
                "cross": " ",
                "half_left": "",
                "half_right": "",
            }
        else:
            # Regular style
            self.box_chars = {
                "horizontal": "─",
                "vertical": "│",
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "top_tee": "┬",
                "bottom_tee": "┴",
                "left_tee": "├",
                "right_tee": "┤",
                "cross": "┼",
                "half_left": "",
                "half_right": "",
            }
    
    @staticmethod
    def _clean_markup(text: str) -> str:
        """Remove Rich markup from text."""
        if not text:
            return text
        return re.sub(r'\[/?[^][]*\]', '', text)
    
    def add_column(
        self,
        header: str = "",
        *,
        footer: str = "",
        header_style: Optional[str] = None,
        footer_style: Optional[str] = None,
        justify: str = "left",
        style: str = "",
        width: Optional[int] = None,
        ratio: Optional[int] = None,
        no_wrap: bool = False,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        overflow: str = "fold",
    ) -> None:
        """
        Add a column to the table.
        """
        column = Column(
            header=header,
            footer=footer,
            justify=justify,
            style=style,
            width=width,
            ratio=ratio,
            overflow=overflow,
            no_wrap=no_wrap,
            min_width=min_width,
            max_width=max_width,
        )
        self.columns.append(column)
    
    def add_row(
        self,
        *cells: Any,
        style: Optional[str] = None,
    ) -> None:
        """
        Add a row to the table.
        """
        cleaned_cells = []
        for cell in cells:
            if cell is None:
                cleaned_cells.append("")
            elif hasattr(cell, '__rich__') or hasattr(cell, '__rich_console__'):
                cleaned_cells.append(self._clean_markup(str(cell)))
            else:
                cleaned_cells.append(self._clean_markup(str(cell)))
        
        row = Row(cells=cleaned_cells, style=style or "")
        self.rows.append(row)
    
    def _calculate_column_widths(self, available_width: int) -> List[int]:
        """
        Calculate optimal column widths.
        """
        num_cols = len(self.columns)
        if num_cols == 0:
            return []
        
        # Start with minimum widths based on content
        min_widths = []
        for i, column in enumerate(self.columns):
            min_width = 0
            
            if self.show_header and column.header:
                min_width = max(min_width, len(column.header))
            
            if self.show_footer and column.footer:
                min_width = max(min_width, len(column.footer))
            
            for row in self.rows:
                if i < len(row.cells):
                    cell_width = len(row.cells[i])
                    min_width = max(min_width, cell_width)
            
            if column.min_width:
                min_width = max(min_width, column.min_width)
            if column.max_width:
                min_width = min(min_width, column.max_width)
            if column.width:
                min_width = column.width
            
            min_width = max(min_width, 1)
            min_widths.append(min_width)
        
        total_min_width = sum(min_widths)
        
        # Add space for borders if they exist
        border_space = 0
        if (self.show_edge or self.show_lines) and self.box_chars["vertical"]:
            # Count vertical borders
            vertical_borders = 0
            if self.show_edge:
                vertical_borders += 2  # Left and right
            
            if self.show_lines or self.box_style == "grid":
                vertical_borders += (num_cols - 1)  # Between columns
            
            border_space += vertical_borders * len(self.box_chars["vertical"])
        
        total_min_width += border_space + (2 * num_cols * self.padding[0])
        
        if self.expand or total_min_width <= available_width:
            if self.expand and total_min_width < available_width:
                extra_space = available_width - total_min_width
                ratios = [col.ratio or 1 for col in self.columns]
                total_ratio = sum(ratios)
                
                for i in range(num_cols):
                    extra = int(extra_space * ratios[i] / total_ratio)
                    min_widths[i] += extra
            
            return min_widths
        
        if available_width > 20:
            ratios = [col.ratio or 1 for col in self.columns]
            total_ratio = sum(ratios)
            
            available_for_cells = available_width - border_space - (2 * num_cols * self.padding[0])
            widths = []
            for i, ratio in enumerate(ratios):
                width = max(1, int(available_for_cells * ratio / total_ratio))
                widths.append(width)
            
            return widths
        
        return min_widths
    
    def _render_row(self, cells: List[str]) -> str:
        """Render a single row."""
        if not self.columns:
            return ""
        
        row_parts = []
        
        for i, (cell, column, width) in enumerate(zip(cells, self.columns, self._column_widths)):
            # Handle cell content
            cell_content = str(cell) if cell is not None else ""
            
            # Handle overflow
            if column.no_wrap and len(cell_content) > width:
                cell_content = cell_content[:width-3] + "..."
            elif column.overflow == "fold" and len(cell_content) > width and width > 0:
                wrapped = textwrap.wrap(cell_content, width=width)
                cell_content = wrapped[0] if wrapped else ""
                if len(wrapped) > 1:
                    cell_content = cell_content[:-3] + "..."
            elif column.overflow == "ellipsis" and len(cell_content) > width:
                cell_content = cell_content[:width-3] + "..."
            
            # Justify text
            if column.justify == "center":
                justified = cell_content.center(width) if width > 0 else cell_content
            elif column.justify == "right":
                justified = cell_content.rjust(width) if width > 0 else cell_content
            else:  # left
                justified = cell_content.ljust(width) if width > 0 else cell_content
            
            # Add padding
            left_pad = " " * self.padding[0]
            right_pad = " " * self.padding[0]
            
            if self.collapse_padding:
                if i == 0:
                    left_pad = ""
                if i == len(cells) - 1:
                    right_pad = ""
            
            padded = left_pad + justified + right_pad
            
            # Add vertical border if needed
            if i > 0 and (self.show_lines or self.box_style == "grid") and self.box_chars["vertical"]:
                row_parts.append(self.box_chars["vertical"])
            
            row_parts.append(padded)
        
        # Add outer borders if needed
        if self.show_edge and self.box_chars["vertical"]:
            return self.box_chars["vertical"] + "".join(row_parts) + self.box_chars["vertical"]
        else:
            return "".join(row_parts)
    
    def _render_horizontal_border(self, left: str, middle: str, right: str) -> str:
        """Render a horizontal border."""
        if not self.columns:
            return ""
        
        parts = []
        for i, width in enumerate(self._column_widths):
            if i == 0:
                parts.append(left)
            
            if width > 0 and self.box_chars["horizontal"]:
                parts.append(self.box_chars["horizontal"] * (width + 2 * self.padding[0]))
            else:
                parts.append("")
            
            if i < len(self._column_widths) - 1:
                parts.append(middle)
            else:
                parts.append(right)
        
        return "".join(parts)
    
    def _render_table(self, console_width: int) -> Iterator[str]:
        """Render the table as an iterator of lines."""
        if not self.columns:
            yield "No columns defined"
            return
        
        # Calculate column widths
        self._column_widths = self._calculate_column_widths(console_width)
        
        # Render title
        if self.title:
            title_line = self.title
            if self.title_justify == "center":
                title_line = title_line.center(console_width)
            elif self.title_justify == "right":
                title_line = title_line.rjust(console_width)
            yield title_line
            yield ""
        
        # Top border
        if self.show_edge and self.box_chars["top_left"]:
            yield self._render_horizontal_border(
                self.box_chars["top_left"],
                self.box_chars["top_tee"],
                self.box_chars["top_right"]
            )
        
        # Header
        if self.show_header:
            headers = [col.header for col in self.columns]
            yield self._render_row(headers)
            
            # Header separator
            if (self.show_lines or self.box_style == "grid") and self.box_chars["horizontal"]:
                if self.show_edge:
                    yield self._render_horizontal_border(
                        self.box_chars["left_tee"],
                        self.box_chars["cross"],
                        self.box_chars["right_tee"]
                    )
                else:
                    yield self._render_horizontal_border(
                        "",
                        self.box_chars["horizontal"],
                        ""
                    )
        
        # Rows
        for row_idx, row in enumerate(self.rows):
            yield self._render_row(row.cells)
            
            # Row separator (except last row)
            if (self.show_lines or self.box_style == "grid") and row_idx < len(self.rows) - 1 and self.box_chars["horizontal"]:
                if self.show_edge:
                    yield self._render_horizontal_border(
                        self.box_chars["left_tee"],
                        self.box_chars["cross"],
                        self.box_chars["right_tee"]
                    )
                else:
                    yield self._render_horizontal_border(
                        "",
                        self.box_chars["horizontal"],
                        ""
                    )
        
        # Footer
        if self.show_footer:
            # Footer separator
            if (self.show_lines or self.box_style == "grid") and self.box_chars["horizontal"]:
                if self.show_edge:
                    yield self._render_horizontal_border(
                        self.box_chars["left_tee"],
                        self.box_chars["cross"],
                        self.box_chars["right_tee"]
                    )
                else:
                    yield self._render_horizontal_border(
                        "",
                        self.box_chars["horizontal"],
                        ""
                    )
            
            footers = [col.footer for col in self.columns]
            yield self._render_row(footers)
        
        # Bottom border
        if self.show_edge and self.box_chars["bottom_left"]:
            yield self._render_horizontal_border(
                self.box_chars["bottom_left"],
                self.box_chars["bottom_tee"],
                self.box_chars["bottom_right"]
            )
        
        # Caption
        if self.caption:
            yield ""
            caption_line = self.caption
            if self.caption_justify == "center":
                caption_line = caption_line.center(console_width)
            elif self.caption_justify == "right":
                caption_line = caption_line.rjust(console_width)
            yield caption_line
    
    def __rich_console__(self, console, options) -> Iterator[str]:
        """Rich console protocol implementation."""
        width = min(self.width or options.max_width, options.max_width)
        yield from self._render_table(width)
    
    def __str__(self) -> str:
        """String representation of the table."""
        return "\n".join(self._render_table(80))
    
    def get_string(self, width: Optional[int] = None) -> str:
        """
        Get the table as a string.
        """
        return "\n".join(self._render_table(width or 80))


# Example usage demonstrating both bordered and borderless grid tables
if __name__ == "__main__":
    print("=" * 80)
    print("GRID TABLES WITH AND WITHOUT BORDERS")
    print("=" * 80)
    
    # Example data
    log_data = [
        ("2024-01-15 14:30:25", "Database.connect", "Connected to DB", "line 142", "✅"),
        ("2024-01-15 14:31:10", "User.login", "User authenticated", "line 89", "✅"),
        ("2024-01-15 14:32:45", "Payment.process", "Processing payment", "line 256", "⚠️"),
        ("2024-01-15 14:33:20", "Email.send", "Failed to send", "line 178", "❌"),
    ]
    
    # 1. Grid table WITH borders (default)
    print("\n1. Grid Table WITH Borders (default):")
    print("-" * 40)
    
    tbl1 = Table.grid(padding=(0, 1), pad_edge=False, expand=True)
    tbl1.add_column(justify="left", no_wrap=True, width=25)
    tbl1.add_column(justify="left", no_wrap=False)
    tbl1.add_column(justify="left", overflow="fold", ratio=60)
    tbl1.add_column(justify="left", no_wrap=True, width=10)
    tbl1.add_column(justify="right", no_wrap=True, width=8)
    
    for data in log_data:
        tbl1.add_row(*data)
    
    print(tbl1.get_string(width=100))
    
    # 2. Grid table WITHOUT borders
    print("\n\n2. Grid Table WITHOUT Borders:")
    print("-" * 40)
    
    tbl2 = Table.grid(padding=(0, 1), pad_edge=False, expand=True, show_borders=False)
    tbl2.add_column(justify="left", no_wrap=True, width=25)
    tbl2.add_column(justify="left", no_wrap=False)
    tbl2.add_column(justify="left", overflow="fold", ratio=60)
    tbl2.add_column(justify="left", no_wrap=True, width=10)
    tbl2.add_column(justify="right", no_wrap=True, width=8)
    
    for data in log_data:
        tbl2.add_row(*data)
    
    print(tbl2.get_string(width=100))
    
    # 3. Using borderless_grid convenience method
    print("\n\n3. Using borderless_grid() convenience method:")
    print("-" * 40)
    
    tbl3 = Table.borderless_grid(padding=(0, 1), pad_edge=False, expand=True)
    tbl3.add_column("Timestamp", justify="left", width=25)
    tbl3.add_column("Component", justify="left", width=20)
    tbl3.add_column("Message", justify="left", overflow="fold")
    tbl3.add_column("Status", justify="center", width=10)
    
    for data in log_data:
        # Remove last column for this example
        tbl3.add_row(data[0], data[1], data[2], data[4])
    
    print(tbl3.get_string(width=100))
    
    # 4. Different border configurations
    print("\n\n4. Different Border Configurations:")
    print("-" * 40)
    
    # Note: For full control, create Table instances directly with desired parameters
    configs = [
        ("Full Borders", {
            "box": "grid",
            "show_edge": True,
            "show_lines": True
        }),
        ("No Borders", {
            "box": "grid",
            "show_edge": False,
            "show_lines": False
        }),
        ("Only Horizontal Lines", {
            "box": "grid",
            "show_edge": False,
            "show_lines": True
        }),
        ("Only Vertical Lines", {
            "box": "grid",
            "show_edge": True,
            "show_lines": False
        }),
    ]
    
    for config_name, config_params in configs:
        print(f"\n{config_name}:")
        # Create table with specific parameters
        tbl = Table(
            **config_params,
            padding=(1, 0),
            show_header=True,
            show_footer=False
        )
        tbl.add_column("Config", width=15)
        tbl.add_column("show_edge", width=15)
        tbl.add_column("show_lines", width=15)
        
        tbl.add_row(
            config_name,
            str(config_params.get("show_edge", "")),
            str(config_params.get("show_lines", ""))
        )
        
        print(tbl.get_string(width=50))
    
    # 5. Your original use case
    print("\n\n5. Your Original Use Case:")
    print("-" * 40)
    
    # This is what you originally wanted
    tbl_original = Table.grid(padding=(0, 1), pad_edge=False, expand=True)
    tbl_original.add_column(justify="left", style="#000000 on #00FFFF", no_wrap=True, width=25)
    tbl_original.add_column(justify="left", style="#FFFFFF on #55007F", no_wrap=False)
    tbl_original.add_column(justify="left", style="white", overflow="fold", ratio=60)
    tbl_original.add_column(justify="left", style="#FFFFFF on #AA007F", no_wrap=True)
    tbl_original.add_column(justify="right", style="#AAAAFF on #000000", no_wrap=True)
    
    # Add sample data
    tbl_original.add_row(
        "2024-01-15 14:30:25.123",
        "DatabaseService.connect()",
        "[INFO] Establishing connection to PostgreSQL database 'production' on host 'db01'",
        "db.py:142",
        "SUCCESS"
    )
    tbl_original.add_row(
        "2024-01-15 14:31:10.456",
        "UserController.login()",
        "[DEBUG] Validating credentials for user 'john.doe@example.com'",
        "controllers.py:89",
        "OK"
    )
    
    print(tbl_original.get_string(width=120))
    
    # 6. Borderless version of your original use case
    print("\n\n6. Borderless Version of Your Use Case:")
    print("-" * 40)
    
    tbl_borderless = Table.borderless_grid(padding=(0, 1), pad_edge=False, expand=True)
    tbl_borderless.add_column(justify="left", style="#000000 on #00FFFF", no_wrap=True, width=25)
    tbl_borderless.add_column(justify="left", style="#FFFFFF on #55007F", no_wrap=False)
    tbl_borderless.add_column(justify="left", style="white", overflow="fold", ratio=60)
    tbl_borderless.add_column(justify="left", style="#FFFFFF on #AA007F", no_wrap=True)
    tbl_borderless.add_column(justify="right", style="#AAAAFF on #000000", no_wrap=True)
    
    tbl_borderless.add_row(
        "2024-01-15 14:30:25.123",
        "DatabaseService.connect()",
        "[INFO] Establishing connection to PostgreSQL database 'production' on host 'db01'",
        "db.py:142",
        "SUCCESS"
    )
    tbl_borderless.add_row(
        "2024-01-15 14:31:10.456",
        "UserController.login()",
        "[DEBUG] Validating credentials for user 'john.doe@example.com'",
        "controllers.py:89",
        "OK"
    )
    
    print(tbl_borderless.get_string(width=120))
    
    print("\n" + "=" * 80)
    print("END OF DEMONSTRATION")
    print("=" * 80)