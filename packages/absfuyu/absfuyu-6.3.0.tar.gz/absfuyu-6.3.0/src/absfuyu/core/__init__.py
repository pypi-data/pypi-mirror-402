"""
Absfuyu: Core
-------------
Bases for other features

Version: 6.3.0
Date updated: 17/01/2026 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    # color
    "CLITextColor",
    # path
    # "CORE_PATH",
    # class
    "GetClassMembersMixin",
    "BaseClass",
    # wrapper
    "tqdm",
    "unidecode",
    # decorator
    "deprecated",
    "versionadded",
    "versionchanged",
]

__package_feature__ = [
    "full",  # All package
    "docs",  # For (package) hatch's env use only
    "extra",  # Extra features
    "beautiful",  # BeautifulOutput
    "dadf",  # DataFrame
    "pdf",  # PDF
    "pic",  # picture related
    "xml",  # XML
    "ggapi",  # Google
]


# Library
# ---------------------------------------------------------------------------
# from importlib.resources import files

from enum import StrEnum

# Most used features are imported to core
from absfuyu.core.baseclass import BaseClass, CLITextColor, GetClassMembersMixin
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.core.dummy_func import tqdm, unidecode

# Path
# ---------------------------------------------------------------------------
# CORE_PATH = files("absfuyu")


# Color
# ---------------------------------------------------------------------------
class HexColor(StrEnum):
    # Base
    WHITE = "FFFFFF"
    BLACK = "000000"

    # Grayscale
    LIGHT_GRAY = "F2F2F2"
    GRAY = "BFBFBF"
    DARK_GRAY = "7F7F7F"
    CHARCOAL = "595959"
    SOFT_BLACK = "262626"

    # Blue family
    LIGHT_BLUE = "D9E1F2"
    PALE_BLUE = "DEEAF6"
    SKY_BLUE = "BDD7EE"
    BLUE = "5B9BD5"
    DARK_BLUE = "2F5597"

    # Green family
    LIGHT_GREEN = "E2EFDA"
    PALE_GREEN = "EAF1DD"
    MINT_GREEN = "C6EFCE"
    GREEN = "70AD47"
    DARK_GREEN = "375623"

    # Orange / Yellow family
    LIGHT_ORANGE = "FCE4D6"
    PALE_ORANGE = "FBE5D6"
    AMBER = "FFD966"
    GOLD = "FFC000"
    DARK_ORANGE = "ED7D31"

    # Red / Pink family
    LIGHT_RED = "F4CCCC"
    PALE_RED = "F8CBAD"
    ROSE = "F4B084"
    RED = "C00000"
    DARK_RED = "7F0000"

    # Purple family
    LAVENDER = "E4DFEC"
    LIGHT_PURPLE = "D9D2E9"
    PURPLE = "7030A0"
    DARK_PURPLE = "4B3869"

    # Teal / Cyan family
    LIGHT_TEAL = "D0E3E7"
    TEAL = "4BACC6"
    DARK_TEAL = "31859B"

    # Brown family
    BEIGE = "FFF2CC"
    TAN = "E6B8AF"
    BROWN = "8B5A2B"
