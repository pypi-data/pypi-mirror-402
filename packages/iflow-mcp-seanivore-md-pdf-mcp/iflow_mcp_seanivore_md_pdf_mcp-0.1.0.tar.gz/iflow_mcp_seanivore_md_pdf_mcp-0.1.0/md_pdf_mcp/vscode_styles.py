"""VS Code Markdown Style Implementation for ReportLab PLATYPUS

This module provides an exact implementation of VS Code's markdown styling for ReportLab's
PLATYPUS (Page Layout and Typography Using Scripts) system.
"""

from reportlab.lib import colors
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from pathlib import Path

# Get the directory where this module is located
_MODULE_DIR = Path(__file__).parent.parent
_FONTS_DIR = _MODULE_DIR / "fonts" / "TTF"

# Helper function to get font path
def _get_font_path(font_filename: str) -> str:
    """Get the full path to a font file."""
    font_path = _FONTS_DIR / font_filename
    if font_path.exists():
        return str(font_path)
    # Fallback to relative path
    return f"fonts/TTF/{font_filename}"

# Register fonts in document hierarchy order
# H1 - Title
try:
    pdfmetrics.registerFont(TTFont('BerninaSans-CompressedBold', _get_font_path('Bernina Sans-Compressed Bold.ttf')))
    FONT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load font BerninaSans-CompressedBold: {e}")
    FONT_AVAILABLE = False

# H2 - Role/Bold Text
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninoSans-CondensedBold', _get_font_path('Bernino Sans-Condensed Bold.ttf')))

# H3 - Date/Italics
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninoSans-Light', _get_font_path('Bernino Sans-Light.ttf')))
    pdfmetrics.registerFont(TTFont('BerninoSans-LightItalic', _get_font_path('Bernino Sans-Light Italic.ttf')))

# H4 - Section Headers
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninaSans-CondensedBold', _get_font_path('Bernino Sans-Condensed Bold.ttf')))

# H5 - Subsection Titles
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninaSans-Narrow', _get_font_path('Bernina Sans-Narrow Regular.ttf')))

# Body Text
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninoSans', _get_font_path('Bernino Sans-Regular.ttf')))

# Core font variations we need
if FONT_AVAILABLE:
    pdfmetrics.registerFont(TTFont('BerninoSans-Bold', _get_font_path('Bernino Sans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('BerninoSans-NarrowExtrabold', _get_font_path('Bernino Sans-Narrow Extrabold.ttf')))

def px_to_pt(px: float) -> float:
    """Convert pixels to points (1px = 0.75pt)"""
    return px * 0.75

def em_to_pt(em: float, base_size: float = 14) -> float:
    """Convert em to points based on base font size"""
    return em * base_size

# VS Code's exact colors
THEME_COLORS = {
    'light': {
        'text': colors.black,
        'background': colors.white,
        'link': HexColor('#0090f1'),
        'pre_background': Color(30/255, 30/255, 30/255, alpha=0.95),
        'pre_text': Color(220/255, 220/255, 220/255),
        'comment': Color(87/255, 166/255, 74/255),
        'widget_border': Color(0, 0, 0, alpha=0.14),  # Needed for code blocks
    },
    'high-contrast': {
        'text': colors.black,
        'background': colors.white,
        'link': HexColor('#0090f1'),
        'pre_background': colors.black,
        'pre_text': colors.white,
        'comment': Color(87/255, 166/255, 74/255),
        'widget_border': colors.black,  # Needed for code blocks
    }
}

def get_vscode_stylesheet(theme: str = 'light') -> StyleSheet1:
    """Generate a ReportLab StyleSheet matching VS Code's markdown styling."""
    styles = StyleSheet1()
    colors = THEME_COLORS[theme]

    # Base style for normal document flow
    styles.add(ParagraphStyle(
        name='Body',
        fontName='BerninoSans' if FONT_AVAILABLE else 'Helvetica',
        fontSize=px_to_pt(11),
        leading=em_to_pt(1.2),
        textColor=colors['text'],
        backColor=colors['background'],
        alignment=TA_LEFT,
        spaceAfter=em_to_pt(1.0),
        firstLineIndent=0,
        leftIndent=0,
        rightIndent=0,
        bulletIndent=em_to_pt(0.5),
    ))

    # Regular heading styles - all left aligned
    styles.add(ParagraphStyle(
        name='Heading1',
        parent=styles['Body'],
        fontName='BerninaSans-CompressedBold' if FONT_AVAILABLE else 'Helvetica-Bold',
        fontSize=px_to_pt(48),
        leading=em_to_pt(3.0),
        spaceBefore=em_to_pt(0.2),
        spaceAfter=0,
    ))

    # H2 - Role/Bold Text
    styles.add(ParagraphStyle(
        name='Heading2',
        parent=styles['Body'],
        fontName='BerninoSans-CondensedBold' if FONT_AVAILABLE else 'Helvetica-Bold',
        fontSize=px_to_pt(16),
        leading=em_to_pt(1.15),
        spaceBefore=em_to_pt(0.2),
        spaceAfter=em_to_pt(2.0),
    ))

    # H3 - Date/Italics
    styles.add(ParagraphStyle(
        name='Heading3',
        parent=styles['Body'],
        fontName='BerninoSans-LightItalic' if FONT_AVAILABLE else 'Helvetica-Oblique',
        fontSize=px_to_pt(14),
        leading=em_to_pt(1.2),
        spaceBefore=0,
        spaceAfter=em_to_pt(3.0),
    ))

    # H4 - Section Headers
    styles.add(ParagraphStyle(
        name='Heading4',
        parent=styles['Body'],
        fontName='BerninaSans-CondensedBold' if FONT_AVAILABLE else 'Helvetica-Bold',
        fontSize=px_to_pt(18),
        leading=em_to_pt(1.2),
        spaceBefore=em_to_pt(1.5),
        spaceAfter=em_to_pt(1.0),
    ))

    # H5 - Now a regular heading
    styles.add(ParagraphStyle(
        name='Heading5',
        parent=styles['Body'],
        fontName='BerninaSans-Narrow' if FONT_AVAILABLE else 'Helvetica',
        fontSize=px_to_pt(14),  # Smaller than H4
        leading=em_to_pt(1.2),
        spaceBefore=em_to_pt(1.0),
        spaceAfter=em_to_pt(0.5),
    ))

    # List items
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['Body'],
        fontName='BerninoSans-NarrowExtrabold' if FONT_AVAILABLE else 'Helvetica-Bold',
        fontSize=px_to_pt(11),
        leftIndent=em_to_pt(1.2),
        bulletIndent=em_to_pt(0.8),
        spaceBefore=em_to_pt(0.2),
        spaceAfter=em_to_pt(0.2),
        leading=13,
        wordSpacing=2,
        tracking=110,
        textTransform='uppercase',
    ))

    # Emphasized text (italics)
    styles.add(ParagraphStyle(
        name='Emphasis',
        parent=styles['Body'],
        fontName='BerninoSans-LightItalic' if FONT_AVAILABLE else 'Helvetica-Oblique',
        textColor=colors['text'],
    ))

    # Strong text (bold)
    styles.add(ParagraphStyle(
        name='Strong',
        parent=styles['Body'],
        fontName='BerninoSans-Bold' if FONT_AVAILABLE else 'Helvetica-Bold',
        textColor=colors['text'],
    ))

    # Code blocks
    styles.add(ParagraphStyle(
        name='Code',
        parent=styles['Body'],
        fontName='Courier',
        fontSize=px_to_pt(11),
        leading=em_to_pt(1.2),
        textColor=colors['pre_text'],
    ))

    styles.add(ParagraphStyle(
        name='CodeComment',
        parent=styles['Code'],
        textColor=colors['comment'],
    ))

    styles.add(ParagraphStyle(
        name='Pre',
        parent=styles['Code'],
        backColor=colors['pre_background'],
        borderPadding=px_to_pt(12),
        leftIndent=px_to_pt(12),
        rightIndent=px_to_pt(12),
        spaceBefore=px_to_pt(6),
        spaceAfter=px_to_pt(6),
        borderWidth=1,
        borderColor=colors['widget_border'],  # Used for code block border
        borderRadius=3,
        textColor=colors['pre_text'],
    ))

    # Links
    styles.add(ParagraphStyle(
        name='Link',
        parent=styles['Body'],
        textColor=colors['link'],
        underline=1,
    ))

    # Signature style - preserve line breaks
    styles.add(ParagraphStyle(
        name='Signature',
        parent=styles['Body'],
        spaceBefore=em_to_pt(1.0),
        spaceAfter=em_to_pt(0.5),
        keepWithNext=True,
    ))

    return styles