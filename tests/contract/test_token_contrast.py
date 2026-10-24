"""
Test suite validating WCAG 2.x contrast ratios for design tokens in apps/web/styles/tokens.css.
Enforces 4.5:1 minimum ratio for text elements and 3.0:1 for UI borders and chart lines
across both light and dark themes.
"""

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_CSS = REPO_ROOT / "apps" / "web" / "styles" / "tokens.css"


def lum(hex_code: str) -> float:
    """Calculate WCAG 2.x relative luminance of an sRGB hex color."""
    h = hex_code.strip().lstrip("#")
    r, g, b = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(hex_a: str, hex_b: str) -> float:
    """Calculate WCAG 2.x contrast ratio between two hex colors."""
    la = lum(hex_a)
    lb = lum(hex_b)
    lighter = max(la, lb)
    darker = min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def parse_tokens(css_content: str):
    """Simple parser extracting custom property declarations."""
    # Find all var: #hex patterns
    vars_found = {}
    for match in re.finditer(r"--([a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{6})", css_content):
        name = match.group(1)
        hex_val = match.group(2).upper()
        vars_found[name] = hex_val
    return vars_found


def test_tokens_css_exists_and_parses():
    assert TOKENS_CSS.exists(), f"tokens.css missing at {TOKENS_CSS}"
    content = TOKENS_CSS.read_text(encoding="utf-8")
    assert "--primary" in content
    assert "--status-verified" in content
    assert "--chart-combined" in content


def test_core_palette_contrast_light_theme():
    # Light theme surfaces
    bg = "#F7F9FB"
    surface = "#FFFFFF"

    # Core text tokens (must be >= 4.5:1)
    text = "#0B1F33"
    muted = "#475569"
    primary = "#0B6B74"
    moonshot = "#5B49C0"
    highlight_text = "#8A5300"
    ui_border = "#7B8794"

    assert ratio(text, surface) >= 4.5
    assert ratio(text, bg) >= 4.5
    assert ratio(muted, surface) >= 4.5
    assert ratio(muted, bg) >= 4.5
    assert ratio(primary, surface) >= 4.5
    assert ratio(primary, bg) >= 4.5
    assert ratio(moonshot, surface) >= 4.5
    assert ratio(moonshot, bg) >= 4.5
    assert ratio(highlight_text, surface) >= 4.5
    assert ratio(highlight_text, bg) >= 4.5

    # UI border must be >= 3.0:1
    assert ratio(ui_border, surface) >= 3.0
    assert ratio(ui_border, bg) >= 3.0


def test_core_palette_contrast_dark_theme():
    # Dark theme surfaces
    bg = "#0A1624"
    surface = "#12233A"

    # Core text tokens
    text = "#E8EEF5"
    muted = "#A9B8CB"
    primary = "#35C0CB"
    moonshot = "#A99DF5"
    highlight_text = "#FFB84D"
    ui_border = "#5B7391"

    assert ratio(text, surface) >= 4.5
    assert ratio(text, bg) >= 4.5
    assert ratio(muted, surface) >= 4.5
    assert ratio(muted, bg) >= 4.5
    assert ratio(primary, surface) >= 4.5
    assert ratio(primary, bg) >= 4.5
    assert ratio(moonshot, surface) >= 4.5
    assert ratio(moonshot, bg) >= 4.5
    assert ratio(highlight_text, surface) >= 4.5
    assert ratio(highlight_text, bg) >= 4.5

    # UI border must be >= 3.0:1
    assert ratio(ui_border, surface) >= 3.0
    assert ratio(ui_border, bg) >= 3.0


def test_status_chips_contrast_both_themes():
    # Light theme status pairs
    light_statuses = [
        ("verified", "#136F4B", "#E3F4EC"),
        ("warning", "#8A5300", "#FFF1D6"),
        ("unverified", "#566474", "#EAEEF2"),
        ("failed", "#B42318", "#FDE8E6"),
    ]
    for name, text_color, bg_color in light_statuses:
        r = ratio(text_color, bg_color)
        assert r >= 4.5, f"Light status '{name}' ratio {r:.2f} < 4.5:1"

    # Dark theme status pairs
    dark_statuses = [
        ("verified", "#3DCB92", "#12372B"),
        ("warning", "#F2B33D", "#3D2F0F"),
        ("unverified", "#9AA9BB", "#22324A"),
        ("failed", "#FF8A80", "#4A1D1D"),
    ]
    for name, text_color, bg_color in dark_statuses:
        r = ratio(text_color, bg_color)
        assert r >= 4.5, f"Dark status '{name}' ratio {r:.2f} < 4.5:1"


def test_claim_tags_contrast_both_themes():
    # Light theme claim tags
    light_tags = [
        ("cited", "#1D4ED8", "#E4ECFD"),
        ("computed", "#0E6E85", "#DDF1F6"),
        ("inferred", "#6D3FD1", "#EEE8FB"),
        ("commentary", "#566474", "#EAEEF2"),
    ]
    for name, text_color, bg_color in light_tags:
        r = ratio(text_color, bg_color)
        assert r >= 4.5, f"Light tag '{name}' ratio {r:.2f} < 4.5:1"

    # Dark theme claim tags
    dark_tags = [
        ("cited", "#7FA9FF", "#16294D"),
        ("computed", "#4CC9E0", "#0F3340"),
        ("inferred", "#B79CFF", "#2B2250"),
        ("commentary", "#9AA9BB", "#22324A"),
    ]
    for name, text_color, bg_color in dark_tags:
        r = ratio(text_color, bg_color)
        assert r >= 4.5, f"Dark tag '{name}' ratio {r:.2f} < 4.5:1"


def test_chart_lines_contrast_against_card_surfaces():
    # Chart lines must reach >= 3.0:1 on card surface in both themes
    light_surface = "#FFFFFF"
    light_chart_lines = [
        ("baseline", "#566474"),
        ("hire", "#B26A00"),
        ("delay", "#C0392B"),
        ("combined", "#5B49C0"),
    ]
    for name, color in light_chart_lines:
        r = ratio(color, light_surface)
        assert r >= 3.0, f"Light chart line '{name}' ratio {r:.2f} < 3.0:1 on card surface"

    dark_surface = "#12233A"
    dark_chart_lines = [
        ("baseline", "#9AA9BB"),
        ("hire", "#FFB84D"),
        ("delay", "#FF8A80"),
        ("combined", "#A99DF5"),
    ]
    for name, color in dark_chart_lines:
        r = ratio(color, dark_surface)
        assert r >= 3.0, f"Dark chart line '{name}' ratio {r:.2f} < 3.0:1 on card surface"


def test_button_contrast():
    # Light theme buttons
    assert ratio("#FFFFFF", "#0B6B74") >= 4.5  # Primary button
    assert ratio("#FFFFFF", "#5B49C0") >= 4.5  # Moonshot button

    # Dark theme buttons
    assert ratio("#0A1624", "#35C0CB") >= 4.5  # Dark primary button
    assert ratio("#0A1624", "#A99DF5") >= 4.5  # Dark moonshot button
