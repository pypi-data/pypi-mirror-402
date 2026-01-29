"""
eTech Reading - Fast Reading System using RSVP Technology

A PyQt5-based application for rapid serial visual presentation (RSVP) reading.
Increases reading speed while maintaining comprehension through focused letter highlighting.
"""

__title__ = "eTech Reading"
__description__ = "Fast Reading System using RSVP Technology"
__url__ = "https://github.com/yourusername/etech-reading"
__version__ = "1.0.2"
__author__ = "eOS"
__author_email__ = "eos@etech.com"
__license__ = "MIT"
__copyright__ = "Copyright 2026"

from .reader import RSVPReader
from .analyzer import TextAnalyzer

__all__ = ['RSVPReader', 'TextAnalyzer']
