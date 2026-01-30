# from .make_colors import make_colors, MakeColors, make_color, make, getSort, print, color_map, MakeColor, convert, translate, Console
# from .colors import *
from .make_colors import *
from .syntax import Syntax

from . import __version__ as version
__version__ 	= version.version
__email__		= "cumulus13@gmail.com"
__author__		= "Hadi Cahyadi"

__all__ = ['MakeColors', 'MakeColor', 'color_map', 'getSort', 'parse_rich_markup', 'make_colors', 'make_color', "Console", "Confirm", 'make', 'colorize', "Color", "Colors", "MakeColorsHelpFormatter", "SimpleCustomHelpFormatter", "print", "Syntax", "hex_to_ansi"]

