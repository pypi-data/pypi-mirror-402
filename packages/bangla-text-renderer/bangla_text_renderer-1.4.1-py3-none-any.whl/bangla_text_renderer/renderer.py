# ============================================
# File: bangla_text_rendere/renderer.py 
# ============================================

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional, List
import unicodedata
import os


class BanglaTextRenderer:
    CONSONANTS = range(0x0995, 0x09B9 + 1)
    VIRAMA = 0x09CD

    COMBINED_VOWELS = {
        "\u09CB": "\u09C7\u09BE",  # ো
        "\u09CC": "\u09C7\u09D7",  # ৌ
    }

    POPULAR_FONTS = [
        "Kalpurush.ttf",
        "NotoSansBengali-Regular.ttf",
        "SolaimanLipi.ttf",
        "Nikosh.ttf",
        "Vrinda.ttf",
        "Nirmala.ttf",
    ]

    def __init__(
        self,
        font_path: Optional[str] = None,
        font_size: int = 48,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    ):
        self.font_size = font_size
        self.color = color

        if not font_path:
            font_path = self._auto_font()

        self.font_path = font_path
        self.font = ImageFont.truetype(font_path, font_size)

    def _auto_font(self) -> str:
        for f in self.POPULAR_FONTS:
            if os.path.exists(f):
                return f
            p = os.path.join("C:\\Windows\\Fonts", f)
            if os.path.exists(p):
                return p
        raise RuntimeError("No Bangla font found")

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        for k, v in self.COMBINED_VOWELS.items():
            text = text.replace(k, v)
        return text

    # ✅ FINAL: NO VOWEL MOVEMENT
    def fix_bangla_rendering(self, text: str) -> str:
        """
        Do NOT reorder vowels.
        Only normalize and keep joint letters intact.
        """
        return self.normalize(text)

    def wrap_text(self, text: str, max_width: int) -> List[str]:
        words = text.split()
        lines, cur = [], []

        dummy = Image.new("RGBA", (max_width + 50, 100))
        draw = ImageDraw.Draw(dummy)

        for w in words:
            test = " ".join(cur + [w])
            fixed = self.fix_bangla_rendering(test)
            box = draw.textbbox((0, 0), fixed, font=self.font)

            if box[2] <= max_width:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]

        if cur:
            lines.append(" ".join(cur))
        return lines

    def render_text(
        self,
        text: str,
        width: int,
        line_spacing: int = 10,
        align: str = "center",
        background: Optional[Tuple[int, int, int, int]] = None,
    ) -> Image.Image:

        lines = self.wrap_text(text, width)
        height = len(lines) * (self.font_size + line_spacing) + 40

        img = Image.new(
            "RGBA",
            (width, height),
            background if background else (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(img)
        y = 20

        for line in lines:
            fixed = self.fix_bangla_rendering(line)
            box = draw.textbbox((0, 0), fixed, font=self.font)
            tw = box[2] - box[0]

            if align == "center":
                x = (width - tw) // 2
            elif align == "right":
                x = width - tw - 20
            else:
                x = 20

            draw.text((x, y), fixed, font=self.font, fill=self.color)
            y += self.font_size + line_spacing

        return img

    def render_text_with_shadow(
        self,
        text: str,
        width: int,
        shadow_offset: int = 3,
        shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
        **kwargs,
    ) -> Image.Image:

        base = self.render_text(text, width, **kwargs)
        shadow = BanglaTextRenderer(
            self.font_path, self.font_size, shadow_color
        ).render_text(text, width, **kwargs)

        out = Image.new("RGBA", base.size, (0, 0, 0, 0))
        out.paste(shadow, (shadow_offset, shadow_offset), shadow)
        out.paste(base, (0, 0), base)
        return out
