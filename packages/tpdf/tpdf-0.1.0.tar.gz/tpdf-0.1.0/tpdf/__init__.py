"""
TPDF - Text Portable Document Format
AI-friendly PDF generation library
"""

__version__ = "0.1.2"
__author__ = "TheCoolRobot"
__license__ = "MIT"

from .document import TPDF
from .compiler import TPDFCompiler

__all__ = ["TPDF", "TPDFCompiler"]
