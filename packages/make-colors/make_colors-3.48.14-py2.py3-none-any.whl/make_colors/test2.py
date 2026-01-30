from hex2ansi import hex_to_ansi

data = hex_to_ansi("#00FFFF")

print(f"{data['fg']}HELLOW WORLD!{data['reset']}")