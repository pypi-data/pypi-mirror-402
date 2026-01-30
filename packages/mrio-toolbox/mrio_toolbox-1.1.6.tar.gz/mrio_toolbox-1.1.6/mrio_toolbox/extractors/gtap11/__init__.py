"""
This module contains the extractor for raw GTAP 11 data and the IO builder to transform it into an MRIO object.
"""
from .extraction.extractor import extract_gtap11
from .gtap_mrio import build_io

__all__ = ["extract_gtap11","build_io"]