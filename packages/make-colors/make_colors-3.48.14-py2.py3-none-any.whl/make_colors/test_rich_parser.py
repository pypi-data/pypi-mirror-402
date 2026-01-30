#!/usr/bin/env python3
# File: make_colors/test_rich_parser.py
import re
from richcolorlog import setup_logging
logger = setup_logging()
try:
    from .hex2ansi import hex_to_ansi
except:
    from hex2ansi import hex_to_ansi

def parse_rich_markup(text):
    """Parse Rich markup dengan support escaping \[ dan \]"""
    logger.alert(f"text (original): {text}")
    
    # Pre-process: ganti escaped brackets dengan placeholder
    # \[ → placeholder untuk [
    # \] → placeholder untuk ]
    text_processed = text.replace(r'\[', '\x00ESCAPED_LEFT\x00').replace(r'\]', '\x00ESCAPED_RIGHT\x00')
    
    logger.alert(f"text (processed): {text_processed}")
    
    # Cari semua markup dengan regex
    pattern = r'\[([^\[\]]+?)\](.*?)\[/\]'
    matches = list(re.finditer(pattern, text_processed))
    
    if not matches:
        # Kembalikan escaped brackets
        final_text = text_processed.replace('\x00ESCAPED_LEFT\x00', '[').replace('\x00ESCAPED_RIGHT\x00', ']')
        return [(final_text, None, None, None)]
    
    results = []
    
    for idx, m in enumerate(matches):
        markup = m.group(1).strip().lower()
        content = m.group(2)
        
        # Cek ada text sebelum markup ini?
        if idx == 0:
            # First match - ambil dari awal sampai markup
            before = text_processed[:m.start()]
            if before:
                content = before + content
        
        # Cek ada text setelah [/] sampai markup berikutnya atau akhir
        after_close = m.end()  # posisi setelah [/]
        
        if idx < len(matches) - 1:
            # Ada markup berikutnya
            next_start = matches[idx + 1].start()
            after_text = text_processed[after_close:next_start]
        else:
            # Markup terakhir
            after_text = text_processed[after_close:]
        
        if after_text:
            content = content + after_text
        
        # Kembalikan escaped brackets di content
        content = content.replace('\x00ESCAPED_LEFT\x00', '[').replace('\x00ESCAPED_RIGHT\x00', ']')
        
        logger.debug(f"markup: {markup}")
        logger.debug(f"content: {content}")
        
        # Parse markup
        fg, bg = None, None
        parts = markup.split()
        logger.alert(f"parts: {parts}")
        
        parts_colors = []
        parts_attrs = []
        styles = ['bold', 'italic', 'underline', 'dim', 'blink', 'reverse', 'strikethrough', 'strike']
        
        for part in parts:
            logger.alert(f"part: {part}")
            if part in styles:
                if part == 'strike':
                    part = 'strikethrough'
                parts_attrs.append(part)
            else:
                parts_colors.append(part)
        
        logger.debug(f"parts_colors: {parts_colors}")
        logger.debug(f"parts_attrs: {parts_attrs}")
        
        if 'on' in parts_colors and len(parts_colors) > 2:
            fg = parts_colors[0]
            bg = parts_colors[2]
        else:
            if parts_colors:
                fg = parts_colors[0]
        
        logger.warning(f"fg: {fg}")
        logger.warning(f"bg: {bg}")
        
        if fg and fg.startswith("#"):
            fg = hex_to_ansi(fg, no_prefix=True).get('fg')
        if bg and bg.startswith("#"):
            bg = hex_to_ansi(bg, no_prefix=True).get('bg')
        
        results.append((content, fg, bg, parts_attrs))
    
    logger.debug(f"results: {results}")
    return results

# Test cases
print("Test 1 - Normal:")
text1 = "[[#000000 on #00FFFF]HELLO WORLDS ![/]] [#FFFFFF on #0000FF italic strike blink]JUST ME[/]"
print(parse_rich_markup(text1))
print()

print("Test 2 - Escaped backslash:")
text2 = r"\[[#000000 on #00FFFF][HELLO WORLDS !][/]] [#FFFFFF on #0000FF italic strike blink]JUST ME[/]"
print(parse_rich_markup(text2))
print()

print("Test 3 - Mixed:")
text3 = r"[bold]Text with \[escaped\] brackets[/]"
print(parse_rich_markup(text3))