# ============================================
# File: bangla_text_renderer/__init__.py
# ============================================

"""
Bangla Text Renderer
====================
A Python package for rendering Bangla/Bengali text with perfect vowel positioning on images.

This package fixes the common issue where Bangla vowel marks (কার) appear in wrong positions
when using PIL/Pillow, and handles joint letters (যুক্তাক্ষর) correctly.
"""

__version__ = "1.4.1"
__author__ = "Mahfazzalin Shawon Reza"
__email__ = "mahfazzalin1@gmail.com"



from .renderer import BanglaTextRenderer

__all__ = ["BanglaTextRenderer"]
