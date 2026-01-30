"""
Module for extracting and converting data from various sources.
"""

import logging as log
import os
log = log.getLogger(__name__)

def extract_MRIO(table,year,source,destination=False,
                 preprocessing = False,
                 saving_kwargs = dict(),
                 extraction_kwargs = dict()):
    """
    Extract MRIO data and save it to a NetCDF file.

    Specific extractors are called based on the table name.
    Refer to the individual extractor functions for more details.
    
    Parameters
    ----------
    table : str
        Name of the MRIO table to extract. Currently supported:
        
        - 'eora26': Extracts Eora26 data.
        - 'gloria': Extracts GLORIA data.
        - 'wiod': Extracts WIOD data.
        - 'icio': Extracts ICIO data.
        - 'exiobase3': Extracts EXIOBASE3 data.
        - 'figaro': Extracts FIGARO data.
        - 'emerging': Extracts EMERGING data.
        - 'gtap11': Extracts GTAP 11 data.
    
    year : str
        Year of the data to extract.
    source : path-like
        Path to the source directory containing the raw data files.
    destination : path-like
        Path to the destination directory where the NetCDF file will be saved.
    preprocessing : dict
        Parameters for preprocessing the table
        If left empty, no preprocessing is done
    extraction_kwargs : dict
        Additional keyword arguments specific to the extractor function.
    saving_kwargs : dict
        Additional keyword arguments for saving the MRIO data
    """
    log.info(f"Extracting MRIO data for table '{table}' for year {year} from {source} to {destination}")
    if table == 'eora26':
        from mrio_toolbox.extractors.eora.eora_extractor import extract_eora26
        mrio = extract_eora26(year, source, **extraction_kwargs)
    elif table == 'gloria':
        from mrio_toolbox.extractors.gloria.gloria_extractor import extract_gloria
        mrio =extract_gloria(year, source, **extraction_kwargs)
    elif table == 'wiod16':
        from mrio_toolbox.extractors.wiod.wiod_extractor import extract_wiod
        mrio = extract_wiod(year, source, **extraction_kwargs)
    elif table == 'icio':
        from mrio_toolbox.extractors.icio.icio_extractor import extract_icio
        mrio =extract_icio(year, source, **extraction_kwargs)
    elif table == 'exiobase3':
        from mrio_toolbox.extractors.exiobase.exiobase_extractor import extract_exiobase3
        mrio = extract_exiobase3(year, source, **extraction_kwargs)
    elif table == 'figaro':
        from mrio_toolbox.extractors.figaro.figaro_extractor import extract_figaro
        mrio = extract_figaro(year, source, **extraction_kwargs)
    elif table == 'emerging':
        from mrio_toolbox.extractors.emerging.emerging_extractor import extract_emerging
        mrio = extract_emerging(year, source, **extraction_kwargs)
    elif table == 'gtap11':
        from mrio_toolbox.extractors.gtap11 import extract_gtap11
        mrio = extract_gtap11(year, source, **extraction_kwargs)
    else:
        raise ValueError(f"Unsupported MRIO table: {table}")
    if preprocessing:
        mrio.preprocess(**preprocessing)
    if saving_kwargs or destination:
        if destination:
            mrio.save(destination, **saving_kwargs)
        else:
            mrio.save(destination)
    return mrio