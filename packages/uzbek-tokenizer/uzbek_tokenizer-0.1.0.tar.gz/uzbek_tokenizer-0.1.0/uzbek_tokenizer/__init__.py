"""
Uzbek Tokenizer - Morphological segmentation for Uzbek text
"""

from .segmenter import (
    normalize,
    segment_morphological,
    apply_segmentation,
)

__version__ = "0.1.0"
__author__ = "Ibrat Usmonov"
__description__ = "O'zbek tili uchun morfologik segmentatsiya kutubxonasi"

__all__ = [
    "normalize",
    "segment_morphological", 
    "apply_segmentation",
]