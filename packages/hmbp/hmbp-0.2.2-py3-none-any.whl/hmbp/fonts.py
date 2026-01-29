"""Font installation utilities for hmbp."""

import logging
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm

# Suppress matplotlib font warnings globally
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)


# TeX Gyre Heros is a free, open-source Helvetica clone
TEX_GYRE_HEROS_URL = "https://www.gust.org.pl/projects/e-foundry/tex-gyre/heros/qhv2.004otf.zip"
FONT_NAME = "TeX Gyre Heros"


def _get_mpl_font_dir() -> Path:
    """Get matplotlib's TTF font directory."""
    return Path(matplotlib.get_data_path()) / "fonts" / "ttf"


def _is_font_available(font_name: str) -> bool:
    """Check if a font is available to matplotlib."""
    available_fonts = {f.name for f in fm.fontManager.ttflist}
    return font_name in available_fonts


def _install_tex_gyre_heros() -> bool:
    """Download and install TeX Gyre Heros font. Returns True on success."""
    font_dir = _get_mpl_font_dir()

    # Check if already installed
    if any(font_dir.glob("texgyreheros*.otf")):
        return True

    try:
        # Download zip
        with urllib.request.urlopen(TEX_GYRE_HEROS_URL, timeout=30) as response:
            zip_data = BytesIO(response.read())

        # Extract OTF files to matplotlib font dir
        installed_fonts = []
        with zipfile.ZipFile(zip_data) as zf:
            for name in zf.namelist():
                if name.endswith(".otf"):
                    # Extract to font dir with flat name
                    font_path = font_dir / Path(name).name
                    with zf.open(name) as src, open(font_path, "wb") as dst:
                        dst.write(src.read())
                    installed_fonts.append(font_path)

        # Add fonts to font manager
        for font_path in installed_fonts:
            fm.fontManager.addfont(str(font_path))

        return True

    except Exception as e:
        print(f"Warning: Could not install {FONT_NAME}: {e}")
        return False


def ensure_helvetica_available() -> str:
    """
    Ensure a Helvetica-compatible font is available.

    Returns the font name to use (Helvetica if available,
    TeX Gyre Heros as fallback).
    """
    # Check for Helvetica first
    if _is_font_available("Helvetica"):
        return "Helvetica"

    # Check for TeX Gyre Heros
    if _is_font_available(FONT_NAME):
        return FONT_NAME

    # Try to install TeX Gyre Heros
    if _install_tex_gyre_heros():
        return FONT_NAME

    # Fall back to DejaVu Sans (always available)
    return "DejaVu Sans"
