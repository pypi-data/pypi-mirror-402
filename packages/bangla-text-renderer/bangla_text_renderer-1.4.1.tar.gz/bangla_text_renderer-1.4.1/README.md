
# Bangla Text Renderer

Perfect Bangla/Bengali text rendering on images with correct vowel positioning and joint letter handling.

## Problem

When using PIL/Pillow to render Bangla text on images, vowel marks (কার) like ি, ে, ৈ often appear in the wrong position - one letter behind where they should be. This package fixes that issue.

## Installation

```bash
pip install bangla-text-renderer
```

## Quick Start

```python
from bangla_text_renderer import BanglaTextRenderer
from PIL import Image

# Create renderer with your Bangla font
renderer = BanglaTextRenderer(
    font_path='NotoSansBengali-Bold.ttf', # give your font name here /// download your font .ttf file and put on windows\fonts directory
    font_size=48,
    color=(255, 255, 255, 255)  # White
)

# Render text
text = "বাংলা লেখা সঠিকভাবে"
img = renderer.render_text(text, width=800)

# Save image
img.save('output.png')
```

## Features

- ✅ **Perfect vowel positioning** - Fixes misplaced vowel marks (ি, ী, ে, ৈ, etc.)
- ✅ **Joint letter support** - Handles যুক্তাক্ষর correctly
- ✅ **Text wrapping** - Automatic word wrapping
- ✅ **Multiple alignments** - Left, center, right
- ✅ **Shadow effects** - Built-in text shadow
- ✅ **Unicode normalization** - Proper NFC normalization

## Advanced Usage

### Text with Shadow

```python
img = renderer.render_text_with_shadow(
    text="বাংলা টেক্সট",
    width=800,
    shadow_offset=3,
    shadow_color=(0, 0, 0, 180)
)
```

### Custom Alignment and Line Spacing

```python
img = renderer.render_text(
    text="বাংলা লেখা",
    width=800,
    max_lines=3,
    line_spacing=15,
    align='center',  # 'left', 'center', or 'right'
    background=(255, 255, 255, 255)  # White background
)
```

### Integration with Existing Images

```python
from PIL import Image

# Load base image
base_img = Image.open('background.jpg').convert('RGBA')

# Render Bangla text
text_img = renderer.render_text("বাংলা", width=500)

# Paste text on base image
base_img.paste(text_img, (100, 100), text_img)
base_img.save('result.png')
```

## How It Works

The package implements proper Bangla text shaping by:

1. **Normalizing** text to Unicode NFC form
2. **Splitting** combined vowel signs (ো, ৌ)
3. **Reordering** pre-base vowels to appear before consonants
4. **Processing** joint letters (যুক্তাক্ষর) with virama (্)

This ensures text renders exactly as it should appear visually.

## Supported Fonts

Works with any Unicode Bangla font:
- Noto Sans Bengali
- Noto Serif Bengali
- Kalpurush
- SolaimanLipi
- Vrinda
- And more...

## Requirements

- Python 3.7+
- Pillow 8.0.0+

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues, please open an issue on GitHub.



