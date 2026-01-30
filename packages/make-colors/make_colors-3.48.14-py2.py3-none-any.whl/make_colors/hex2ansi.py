#!/usr/bin/env python3

# File: hex2ansi.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-04
# Description: Hex to ANSI Color Converter, Converts various hex color formats to ANSI escape codes
# License: MIT

"""
Hex to ANSI Color Converter
Converts various hex color formats to ANSI escape codes
"""

def hex_to_rgb(hex_color):
    """Konversi hex color ke RGB tuple"""
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

def hex_to_color_name(hex_color):
    """
    Convert hex colors to human-readable color names
    
    Args:
        hex_color (str): Hex color
    
    Returns:
        str: The closest color name
    """
    r, g, b = hex_to_rgb(hex_color)
    
    color_database, _ = get_color_database()
    
    # Find the closest color using euclidean distance
    min_distance = float('inf')
    closest_name = "unknown"
    
    for (cr, cg, cb), name in color_database.items():
        distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    
    # Add modifiers based on brightness
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
    Convert color names to hex colors
    
    Args:
        color_name (str): Color Name (case-insensitive)
    
    Returns:
        str: Hex color with format #RRGGBB
    
    Raises:
        ValueError: If color name not found
    """
    _, name_to_rgb = get_color_database()
    
    # Normalize color names (lowercase, remove extra spaces)
    normalized_name = color_name.lower().strip().replace(" ", "")
    
    if normalized_name in name_to_rgb:
        r, g, b = name_to_rgb[normalized_name]
        return f"#{r:02X}{g:02X}{b:02X}"
    else:
        # Try looking for a partial match
        for name, rgb in name_to_rgb.items():
            if normalized_name in name or name in normalized_name:
                r, g, b = rgb
                return f"#{r:02X}{g:02X}{b:02X}"
        
        raise ValueError(f"Nama warna '{color_name}' tidak ditemukan")

def color_name_to_ansi(color_name, mode='truecolor'):
    """
    Convert color names to ANSI escape codes
    
    Args:
        color_name (str): Color Name (case-insensitive)
        mode (str): 'truecolor' (24-bit), '256' (256 colors), or '16' (16 colors)
    
    Returns:
        dict: Dictionary with foreground and background ANSI codes
    
    Raises:
        ValueError: If the color name is not found
    """
    hex_color = color_name_to_hex(color_name)
    return hex_to_ansi(hex_color, mode)

def to_ansi(color_input, mode='truecolor'):
    """
    Convert color input (hex or name) to ANSI escape codes
    
    Args:
        color_input (str): Hex color or color name
        mode (str): 'truecolor' (24-bit), '256' (256 colors), or '16' (16 colors)
    
    Returns:
        dict: Dictionary with foreground and background ANSI codes
    """
    try:
        return hex_to_ansi(color_input, mode)
    except ValueError:
        return color_name_to_ansi(color_input, mode)

def hex_to_ansi(hex_color, mode='truecolor', no_prefix=False):
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
        fg = f"[38;2;{r};{g};{b}m" if no_prefix else f"[38;2;{r};{g};{b}m"
        bg = f"[48;2;{r};{g};{b}m" if no_prefix else f"[48;2;{r};{g};{b}m"
    elif mode == '256':
        color_code = rgb_to_ansi_256(r, g, b)
        fg = f"[38;5;{color_code}m" if no_prefix else f"[38;5;{color_code}m"
        bg = f"[48;5;{color_code}m" if no_prefix else f"[48;5;{color_code}m"
    elif mode == '16':
        color_code = rgb_to_ansi_16(r, g, b)
        fg = f"[{color_code}m" if no_prefix else f"[{color_code}m"
        bg = f"[{color_code + 10}m" if no_prefix else f"[{color_code + 10}m"
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    return {
        'fg': fg,
        'bg': bg,
        'reset': '[0m',
        'rgb': (r, g, b)
    }

def convert(hex_color, mode='truecolor'):
    """Convert hex color to ANSI codes and return as dictionary"""
    return hex_to_ansi(hex_color, mode)
    
def print_color_demo(hex_color, mode='truecolor'):
    """Color print demo with various modes"""
    result = hex_to_ansi(hex_color, mode)
    reset = result['reset']
    
    # Escape ANSI codes to display as text
    fg_display = repr(result['fg'])[1:-1]  # Remove quotes
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

# Examples of usage
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
        "F0F",      # Format 3-digit
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
    
    # Example of batch conversion
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
    
    # Color name demo
    print("\n--- COLOR NAMES ---")
    demo_colors = ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF", "#4B0082", "#EE82EE", 
                   "#FFC0CB", "#A52A2A", "#808080", "#FFD700", "#FF6347", "#40E0D0"]
    for color in demo_colors:
        name = hex_to_color_name(color)
        result = hex_to_ansi(color, 'truecolor')
        print(f"{result['fg']}●{result['reset']} {color:8} -> {name}")
    
    # Demo of conversion from color names to hex
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
    
    # Demo of conversion from color names to ANSI
    print("\n--- NAME TO ANSI ---")
    test_names = ["red", "skyblue", "forestgreen"]
    for name in test_names:
        try:
            result = color_name_to_ansi(name, 'truecolor')
            fg_display = repr(result['fg'])[1:-1]
            print(f"{result['fg']}●{result['reset']} {name:15} -> {fg_display}")
        except ValueError as e:
            print(f"  {name:15} -> Error: {e}")
    
    print(to_ansi("#FF5733", mode='256'))
    print(to_ansi("cyan", mode='256'))

    # Reset final
    print("\033[0m")
