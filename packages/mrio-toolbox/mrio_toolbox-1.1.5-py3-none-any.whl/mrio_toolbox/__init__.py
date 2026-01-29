"""
The MRIO toolbox module provides several submodules with different functionalities: 

- `mrio_toolbox.mrio`: Contains the MRIO class for handling multi-regional input-output data.
- `mrio_toolbox._parts`: Contains the Part and Axe classes for managing parts of MRIO data.
- `mrio_toolbox.extractors`: Provides functions to extract raw MRIO data.
- 'mrio_toolbox._msm': Contains the multi-scale mapping algorithm for mapping PRIMAP data into an MRIO
- `mrio_toolbox._utils`: Contains utility functions for MRIO loading, saving and converting MRIO data to different formats.

"""

from mrio_toolbox.mrio import MRIO
from mrio_toolbox._parts._Part import Part,load_part
from mrio_toolbox.extractors import extract_MRIO
from mrio_toolbox.extractors import download_MRIO

__all__ = ["MRIO",
           "load_part",
           "Part",
           "extract_MRIO",
           "download_MRIO"]