#!/usr/bin/env python3
"""
Hex to ANSI Color Converter
Convert hex colors to ANSI escape codes with human-readable color names
"""

def get_color_database():
    """
    Color database with names
    Returns dictionary mapping (r,g,b) -> name and name -> (r,g,b)
    """
    colors = {
        # Basic colors
        (0, 0, 0): "black",
        (255, 255, 255): "white",
        (128, 128, 128): "gray",
        (192, 192, 192): "silver",
        
        # Primary colors
        (255, 0, 0): "red",
        (0, 255, 0): "lime",
        (0, 0, 255): "blue",
        
        # Secondary colors
        (255, 255, 0): "yellow",
        (255, 0, 255): "magenta",
        (0, 255, 255): "cyan",
        
        # Common colors
        (128, 0, 0): "maroon",
        (0, 128, 0): "green",
        (0, 0, 128): "navy",
        (128, 128, 0): "olive",
        (128, 0, 128): "purple",
        (0, 128, 128): "teal",
        (255, 165, 0): "orange",
        (255, 192, 203): "pink",
        (165, 42, 42): "brown",
        (255, 215, 0): "gold",
        (210, 180, 140): "tan",
        (255, 228, 181): "moccasin",
        (255, 160, 122): "lightsalmon",
        (240, 128, 128): "lightcoral",
        (255, 99, 71): "tomato",
        (255, 127, 80): "coral",
        (255, 69, 0): "orangered",
        (220, 20, 60): "crimson",
        (139, 0, 0): "darkred",
        (255, 20, 147): "deeppink",
        (255, 105, 180): "hotpink",
        (186, 85, 211): "mediumorchid",
        (138, 43, 226): "blueviolet",
        (75, 0, 130): "indigo",
        (72, 61, 139): "darkslateblue",
        (106, 90, 205): "slateblue",
        (123, 104, 238): "mediumslateblue",
        (147, 112, 219): "mediumpurple",
        (0, 191, 255): "deepskyblue",
        (135, 206, 235): "skyblue",
        (173, 216, 230): "lightblue",
        (176, 224, 230): "powderblue",
        (32, 178, 170): "lightseagreen",
        (64, 224, 208): "turquoise",
        (127, 255, 212): "aquamarine",
        (0, 255, 127): "springgreen",
        (144, 238, 144): "lightgreen",
        (152, 251, 152): "palegreen",
        (34, 139, 34): "forestgreen",
        (107, 142, 35): "olivedrab",
        (154, 205, 50): "yellowgreen",
        (173, 255, 47): "greenyellow",
        (255, 255, 224): "lightyellow",
        (255, 250, 205): "lemonchiffon",
        (250, 250, 210): "lightgoldenrodyellow",
        (255, 239, 213): "papayawhip",
        (255, 228, 196): "bisque",
        (255, 218, 185): "peachpuff",
        (244, 164, 96): "sandybrown",
        (210, 105, 30): "chocolate",
        (139, 69, 19): "saddlebrown",
        (160, 82, 45): "sienna",
        (240, 230, 140): "khaki",
        (189, 183, 107): "darkkhaki",
        (255, 240, 245): "lavenderblush",
        (230, 230, 250): "lavender",
        (221, 160, 221): "plum",
        (238, 130, 238): "violet",
        (218, 112, 214): "orchid",
        (255, 0, 255): "fuchsia",
        (199, 21, 133): "mediumvioletred",
        (219, 112, 147): "palevioletred",
        (70, 130, 180): "steelblue",
        (100, 149, 237): "cornflowerblue",
        (30, 144, 255): "dodgerblue",
        (0, 0, 205): "mediumblue",
        (25, 25, 112): "midnightblue",
        (95, 158, 160): "cadetblue",
        (0, 206, 209): "darkturquoise",
        (72, 209, 204): "mediumturquoise",
        (175, 238, 238): "paleturquoise",
        (0, 255, 255): "aqua",
        (0, 139, 139): "darkcyan",
        (32, 178, 170): "lightseagreen",
        (46, 139, 87): "seagreen",
        (60, 179, 113): "mediumseagreen",
        (143, 188, 143): "darkseagreen",
        (128, 128, 0): "olive",
        (85, 107, 47): "darkolivegreen",
        (124, 252, 0): "lawngreen",
        (127, 255, 0): "chartreuse",
        (50, 205, 50): "limegreen",
        (0, 100, 0): "darkgreen",
        (245, 255, 250): "mintcream",
        (240, 255, 240): "honeydew",
        (255, 248, 220): "cornsilk",
        (255, 245, 238): "seashell",
        (245, 245, 220): "beige",
        (255, 228, 225): "mistyrose",
        (255, 222, 173): "navajowhite",
        (245, 222, 179): "wheat",
        (222, 184, 135): "burlywood",
        (188, 143, 143): "rosybrown",
    }
    
    # Create reverse mapping (name -> rgb)
    name_to_rgb = {name.lower(): rgb for rgb, name in colors.items()}
    
    return colors, name_to_rgb

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except (ValueError, IndexError):
        raise ValueError(f"Invalid hex format: #{hex_color}")

def rgb_to_ansi_16(r, g, b):
    """Convert RGB to ANSI 16 color (basic colors)"""
    threshold = 128
    
    if r < threshold and g < threshold and b < threshold:
        if r == g == b:
            return 30 if r < 64 else 90
    
    colors = []
    if r > threshold: colors.append(1)
    if g > threshold: colors.append(2)
    if b > threshold: colors.append(4)
    
    if not colors:
        return 30
    
    base = sum(colors) + 29
    
    if r > 200 or g > 200 or b > 200:
        base += 60
    
    return base

def rgb_to_ansi_256(r, g, b):
    """Convert RGB to ANSI 256 color"""
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round(((r - 8) / 247) * 24) + 232
    
    def to_6cube(val):
        if val < 48:
            return 0
        if val < 115:
            return 1
        return (val - 35) // 40
    
    ir = to_6cube(r)
    ig = to_6cube(g)
    ib = to_6cube(b)
    
    return 16 + (36 * ir) + (6 * ig) + ib

def hex_to_ansi(hex_color, mode='truecolor'):
    """
    Convert hex color to ANSI escape code
    
    Args:
        hex_color (str): Hex color (with or without #)
        mode (str): 'truecolor' (24-bit), '256' (256 colors), or '16' (16 colors)
    
    Returns:
        dict: Dictionary with foreground and background ANSI codes
    """
    r, g, b = hex_to_rgb(hex_color)
    
    if mode == 'truecolor' or mode == '24bit':
        fg = f"\x1b[38;2;{r};{g};{b}m"
        bg = f"\x1b[48;2;{r};{g};{b}m"
    elif mode == '256':
        color_code = rgb_to_ansi_256(r, g, b)
        fg = f"\x1b[38;5;{color_code}m"
        bg = f"\x1b[48;5;{color_code}m"
    elif mode == '16':
        color_code = rgb_to_ansi_16(r, g, b)
        fg = f"\x1b[{color_code}m"
        bg = f"\x1b[{color_code + 10}m"
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    return {
        'fg': fg,
        'bg': bg,
        'reset': '\x1b[0m',
        'rgb': (r, g, b)
    }

def hex_to_color_name(hex_color):
    """
    Convert hex color to human-readable color name
    
    Args:
        hex_color (str): Hex color
    
    Returns:
        str: Closest color name
    """
    r, g, b = hex_to_rgb(hex_color)
    
    color_database, _ = get_color_database()
    
    # Find closest color using euclidean distance
    min_distance = float('inf')
    closest_name = "unknown"
    
    for (cr, cg, cb), name in color_database.items():
        distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    
    # Add modifier based on brightness
    brightness = (r + g + b) / 3
    
    if min_distance < 30:  # Exact match or very close
        return closest_name.title()
    elif brightness < 50:
        return f"Dark {closest_name.title()}"
    elif brightness > 200:
        return f"Light {closest_name.title()}"
    else:
        return closest_name.title()

def color_name_to_hex(color_name):
    """
    Convert color name to hex color
    
    Args:
        color_name (str): Color name (case-insensitive)
    
    Returns:
        str: Hex color with format #RRGGBB
    
    Raises:
        ValueError: If color name not found
    """
    _, name_to_rgb = get_color_database()
    
    # Normalize color name (lowercase, remove extra spaces)
    normalized_name = color_name.lower().strip().replace(" ", "")
    
    if normalized_name in name_to_rgb:
        r, g, b = name_to_rgb[normalized_name]
        return f"#{r:02X}{g:02X}{b:02X}"
    else:
        # Try partial match
        for name, rgb in name_to_rgb.items():
            if normalized_name in name or name in normalized_name:
                r, g, b = rgb
                return f"#{r:02X}{g:02X}{b:02X}"
        
        raise ValueError(f"Color name '{color_name}' not found")

def color_name_to_ansi(color_name, mode='truecolor'):
    """
    Convert color name to ANSI escape code
    
    Args:
        color_name (str): Color name (case-insensitive)
        mode (str): 'truecolor' (24-bit), '256' (256 colors), or '16' (16 colors)
    
    Returns:
        dict: Dictionary with foreground and background ANSI codes
    
    Raises:
        ValueError: If color name not found
    """
    hex_color = color_name_to_hex(color_name)
    return hex_to_ansi(hex_color, mode)

def colored(string, foreground, background=None, attrs=None, mode='truecolor'):
    """
    Colorize a string using ANSI escape codes for terminal output.
    
    Supports hex colors (#FF0000) and human color names (red, skyblue, etc).
    
    Args:
        string (str): The text string to colorize.
                     Example: "Hello World", "Error message", "Success!"
        foreground (str): Foreground color - can be hex (#FF0000) or name (red, blue).
                        Hex format: "#RRGGBB", "RRGGBB", or "#RGB"
                        Name: 'black', 'red', 'green', 'yellow', 'blue', 
                              'magenta', 'cyan', 'white', 'lightred', etc.
                        Example: "red", "#FF0000", "lightgreen", "#0F0"
        background (str, optional): Background color - can be hex or name with optional 'on_' prefix.
                                  Hex format: "#RRGGBB" or "RRGGBB"
                                  Name: 'black', 'on_red', 'lightblue', etc.
                                  Defaults to None (no background).
                                  Example: "on_yellow", "#FFFF00", "lightblue"
        attrs (list, optional): List of text attributes.
                               Valid: 'bold', 'dim', 'italic', 'underline', 'blink', 
                                     'reverse', 'strikethrough', 'strike'
                               Example: ['bold', 'underline']
        mode (str): ANSI color mode - 'truecolor' (24-bit), '256' (256 colors), or '16' (16 colors)
                   Default: 'truecolor'
    
    Returns:
        str: The input string wrapped with ANSI escape codes.
             Format: \x1b[<codes>m{string}\x1b[0m
    
    Example:
        >>> # Using color names
        >>> red_text = colored("Error!", "red")
        >>> print(red_text)  # Prints "Error!" in red
        
        >>> # Using hex colors
        >>> orange_text = colored("Warning!", "#FFA500", "#000000")
        >>> print(orange_text)  # Orange text on black background
        
        >>> # With attributes
        >>> info = colored("Info", "lightblue", "on_white", ['bold', 'underline'])
        >>> print(info)  # Bold underlined light blue text on white background
        
        >>> # Mix hex and name
        >>> mixed = colored("Custom", "#FF69B4", "on_black", ['bold'])
        >>> print(mixed)  # Pink text on black background
    
    Note:
        - Hex colors are auto-detected if starting with # or format RRGGBB
        - Color names are case-insensitive
        - Background can be with or without 'on_' prefix
        - Invalid colors will raise ValueError
    """
    if attrs is None:
        attrs = []
    
    # Text attributes mapping
    attr_codes = {
        'bold': '1',
        'dim': '2',
        'italic': '3',
        'underline': '4',
        'blink': '5',
        'reverse': '7',
        'strikethrough': '9',
        'strike': '9',
        'normal': '22',
        'no_italic': '23',
        'no_underline': '24',
    }
    
    # Basic ANSI color names mapping
    basic_fore_colors = {
        'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
        'blue': '34', 'magenta': '35', 'cyan': '36', 'white': '37',
        'lightblack': '90', 'lightgrey': '90', 'lightred': '91',
        'lightgreen': '92', 'lightyellow': '93', 'lightblue': '94',
        'lightmagenta': '95', 'lightcyan': '96', 'lightwhite': '97',
    }
    
    basic_back_colors = {
        'black': '40', 'red': '41', 'green': '42', 'yellow': '43',
        'blue': '44', 'magenta': '45', 'cyan': '46', 'white': '47',
        'on_black': '40', 'on_red': '41', 'on_green': '42', 'on_yellow': '43',
        'on_blue': '44', 'on_magenta': '45', 'on_cyan': '46', 'on_white': '47',
        'lightblack': '100', 'lightgrey': '100', 'lightred': '101',
        'lightgreen': '102', 'lightyellow': '103', 'lightblue': '104',
        'lightmagenta': '105', 'lightcyan': '106', 'lightwhite': '107',
        'on_lightblack': '100', 'on_lightgrey': '100', 'on_lightred': '101',
        'on_lightgreen': '102', 'on_lightyellow': '103', 'on_lightblue': '104',
        'on_lightmagenta': '105', 'on_lightcyan': '106', 'on_lightwhite': '107',
    }
    
    def is_hex_color(color):
        """Check if color is hex format"""
        if not color:
            return False
        color = color.strip()
        if color.startswith('#'):
            return len(color) in [4, 7]  # #RGB or #RRGGBB
        # Check if it's hex without #
        if len(color) in [3, 6]:
            try:
                int(color, 16)
                return True
            except ValueError:
                return False
        return False
    
    def get_color_code(color, is_background=False):
        """Get ANSI code for color (hex or name)"""
        if not color:
            return None
        
        color_lower = color.lower().strip()
        
        # Try basic ANSI colors first for mode '16'
        if mode == '16':
            if is_background:
                return basic_back_colors.get(color_lower)
            else:
                return basic_fore_colors.get(color_lower)
        
        # Check if hex color
        if is_hex_color(color):
            try:
                result = hex_to_ansi(color, mode)
                if is_background:
                    # Extract code from background ANSI sequence
                    # Format: \x1b[48;2;R;G;Bm or \x1b[48;5;CODEm
                    return result['bg'].replace('\x1b[', '').replace('m', '')
                else:
                    return result['fg'].replace('\x1b[', '').replace('m', '')
            except ValueError:
                raise ValueError(f"Invalid hex color: {color}")
        
        # Try color name
        try:
            result = color_name_to_ansi(color, mode)
            if is_background:
                return result['bg'].replace('\x1b[', '').replace('m', '')
            else:
                return result['fg'].replace('\x1b[', '').replace('m', '')
        except ValueError:
            # Fallback for basic colors in mode 256/truecolor
            if is_background:
                code = basic_back_colors.get(color_lower)
                if code:
                    return code
            else:
                code = basic_fore_colors.get(color_lower)
                if code:
                    return code
            raise ValueError(f"Invalid color: {color}")
    
    # Get color codes
    try:
        foreground_code = get_color_code(foreground, is_background=False)
    except ValueError as e:
        raise ValueError(f"Foreground error: {e}")
    
    background_code = None
    if background:
        try:
            background_code = get_color_code(background, is_background=True)
        except ValueError as e:
            raise ValueError(f"Background error: {e}")
    
    # Build ANSI codes
    codes = []
    
    # Add attributes
    if attrs:
        for attr in attrs:
            attr_lower = attr.lower()
            if attr_lower in attr_codes:
                codes.append(attr_codes[attr_lower])
    
    # Add background
    if background_code:
        codes.append(background_code)
    
    # Add foreground
    if foreground_code:
        codes.append(foreground_code)
    
    # Join all codes with ';'
    ansi_sequence = ";".join(codes)
    # return f"\x1b[{ansi_sequence}m{string}\x1b[0m"
    return f"[{ansi_sequence}m{string}[0m"

def print_color_demo(hex_color, mode='truecolor'):
    """Demo print color with various modes"""
    result = hex_to_ansi(hex_color, mode)
    reset = result['reset']
    
    # Escape ANSI codes for display as text
    fg_display = repr(result['fg'])[1:-1]
    bg_display = repr(result['bg'])[1:-1]
    
    # Get color name
    color_name = hex_to_color_name(hex_color)
    
    print(f"\nHex: {hex_color} | RGB: {result['rgb']} | Name: {color_name} | Mode: {mode}")
    print(f"{result['fg']}██████{reset} Foreground: {fg_display}")
    print(f"{result['bg']}      {reset} Background: {bg_display}")
    print(f"{result['fg']}{result['bg']}  Text  {reset} Combined")

def convert_multiple_colors(hex_colors, mode='truecolor'):
    """Convert multiple hex colors at once"""
    results = {}
    for hex_color in hex_colors:
        try:
            results[hex_color] = hex_to_ansi(hex_color, mode)
        except ValueError as e:
            results[hex_color] = {'error': str(e)}
    return results

# Usage examples
if __name__ == "__main__":
    test_colors = [
        "#FF0000",  # Red
        "#00FF00",  # Green
        "#0000FF",  # Blue
        "#FFFF00",  # Yellow
        "#FF00FF",  # Magenta
        "#00FFFF",  # Cyan
        "#FFFFFF",  # White
        "#000000",  # Black
        "#808080",  # Gray
        "#FFA500",  # Orange
        "FF5733",   # Without #
        "F0F",      # 3-digit format
    ]
    
    print("=" * 60)
    print("HEX TO ANSI COLOR CONVERTER")
    print("=" * 60)
    
    # Demo True Color (24-bit)
    print("\n--- TRUE COLOR (24-bit) ---")
    for color in test_colors[:5]:
        print_color_demo(color, 'truecolor')
    
    # Demo 256 Colors
    print("\n--- 256 COLORS ---")
    for color in test_colors[:5]:
        print_color_demo(color, '256')
    
    # Demo 16 Colors
    print("\n--- 16 COLORS (Basic) ---")
    for color in test_colors[:5]:
        print_color_demo(color, '16')
    
    # Batch conversion example
    print("\n--- BATCH CONVERSION ---")
    results = convert_multiple_colors(["#FF0000", "#00FF00", "#0000FF"], 'truecolor')
    for hex_color, data in results.items():
        if 'error' in data:
            print(f"{hex_color}: {data['error']}")
        else:
            fg_display = repr(data['fg'])[1:-1]
            bg_display = repr(data['bg'])[1:-1]
            color_name = hex_to_color_name(hex_color)
            print(f"{hex_color} ({color_name}): FG={fg_display}, BG={bg_display}")
    
    # Color names demo
    print("\n--- COLOR NAMES ---")
    demo_colors = ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF", "#4B0082", "#EE82EE", 
                   "#FFC0CB", "#A52A2A", "#808080", "#FFD700", "#FF6347", "#40E0D0"]
    for color in demo_colors:
        name = hex_to_color_name(color)
        result = hex_to_ansi(color, 'truecolor')
        print(f"{result['fg']}●{result['reset']} {color:8} -> {name}")
    
    # Name to hex demo
    print("\n--- NAME TO HEX ---")
    color_names = ["red", "orange", "yellow", "green", "blue", "purple", "pink", "brown", 
                   "gray", "black", "white", "cyan", "magenta", "gold"]
    for name in color_names:
        try:
            hex_val = color_name_to_hex(name)
            result = hex_to_ansi(hex_val, 'truecolor')
            print(f"{result['fg']}●{result['reset']} {name:15} -> {hex_val}")
        except ValueError as e:
            print(f"  {name:15} -> Error: {e}")
    
    # Name to ANSI demo
    print("\n--- NAME TO ANSI ---")
    test_names = ["red", "skyblue", "forestgreen"]
    for name in test_names:
        try:
            result = color_name_to_ansi(name, 'truecolor')
            fg_display = repr(result['fg'])[1:-1]
            print(f"{result['fg']}●{result['reset']} {name:15} -> {fg_display}")
        except ValueError as e:
            print(f"  {name:15} -> Error: {e}")
    
    # colored() method demo - THE BEST METHOD!
    print("\n--- COLORED METHOD DEMO ---")
    print("Using color names:")
    print(colored("  ● Red text", "red"))
    print(colored("  ● Green text on yellow", "green", "on_yellow"))
    print(colored("  ● Bold blue underlined", "blue", attrs=['bold', 'underline']))
    
    print("\nUsing hex colors:")
    print(colored("  ● Orange text (#FFA500)", "#FFA500"))
    print(colored("  ● Pink on black (#FF69B4)", "#FF69B4", "#000000"))
    print(colored("  ● Custom cyan (#00CED1)", "#00CED1", attrs=['bold']))
    
    print("\nMix hex and name:")
    print(colored("  ● Hex text on named bg", "#FF1493", "on_black", ['bold', 'italic']))
    print(colored("  ● Named text on hex bg", "white", "#8B4513"))
    
    print("\nDifferent modes:")
    print(colored("  ● TrueColor (24-bit)", "#FF6347", mode='truecolor'))
    print(colored("  ● 256 Colors", "#FF6347", mode='256'))
    print(colored("  ● 16 Colors", "red", mode='16'))
    
    # Final reset
    print("\x1b[0m")