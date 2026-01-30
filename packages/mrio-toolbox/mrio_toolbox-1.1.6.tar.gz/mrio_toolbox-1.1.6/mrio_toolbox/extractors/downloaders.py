"""
Module for extracting and converting data from various sources.
"""

import logging as log
log = log.getLogger(__name__)


def download_MRIO(table,year,destination,**kwargs):
    """
    Downloads the MRIO from the internet and saves it to the specified destination. 
   
    Specific downloaders are called based on the table name.
    Refer to the individual downloader functions for more details.
    
    Parameters
    ----------
    table : str
        Name of the MRIO table to extract. Currently supported:
        
        - 'figaro': Downloading FIGARO data.
    
    year : str
        Year of the data to extract.
    destination : path-like
        Path to the destination directory where the NetCDF file will be saved.
    **kwargs : dict
        Additional keyword arguments specific to the extractor function.
        For example, `extended` for WIOD extraction to specify if extended data should be included.
    """
    log.info(f"Download MRIO data for table '{table}' for year {year} to the folder {destination}")
    if table == 'figaro':
        from mrio_toolbox.extractors.figaro.figaro_downloader import download_figaro
        download_figaro(year, destination, **kwargs)
    else:
        raise ValueError(f"Downloader for table '{table}' is not implemented yet. Currently supported: 'figaro'.")