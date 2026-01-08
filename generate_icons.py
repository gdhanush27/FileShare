import cairosvg
from pathlib import Path

# Convert SVG to PNG at different sizes
svg_file = Path('static/icons/icon.svg')

# Generate 192x192 icon
cairosvg.svg2png(
    url=str(svg_file),
    write_to='static/icons/icon-192.png',
    output_width=192,
    output_height=192
)

# Generate 512x512 icon
cairosvg.svg2png(
    url=str(svg_file),
    write_to='static/icons/icon-512.png',
    output_width=512,
    output_height=512
)

print("Icons generated successfully!")
print("- static/icons/icon-192.png")
print("- static/icons/icon-512.png")
