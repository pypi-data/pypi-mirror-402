"""
Load and convert Figaro MRIO files. 

Supports Figaro inter industry IO, supply and use tables in csv matrix format
https://ec.europa.eu/eurostat/web/esa-supply-use-input-tables/database#Input-output%20tables%20industry%20by%20industry

The extractor loads the IO table and if available the supply and use tables.

@author: wirth
"""

import os
import logging
import pandas as pd

from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__)

def extract_figaro(year, source, format = 'industry by industry', sut = "none", edition=25):
    """
    Extract FIGARO data. 

    Loads FIGARO tables and labels and store them as NetCDF for further use with 
    the mrio_toolbox library. Currently the extractor does not support emission 
    satellite accounts (I couldn't find them on the figaro website).
    
    Put all tables  as well as the 'Description_FIGARO_Tables({edition}ed).xlsx' file 
    in the same source folder. 

    Parameters
    ----------
    year : str
        Data year to load.
    source : path-like
        Path to folder where raw data is stored
    format : str, optional
       Either 'industry by industry' or 'product by product'.
    sut : str, optional
        Supply and use tables to load, by default "none".
        Available options are "none", "supply", "use" or "both".
    edition : int, optional
        Edition of the FIGARO tables, by default 25. The alternative is 24.
    """
    
    if format == 'industry by industry':
        format_abbr = "ind-by-ind"
    elif format == 'product by product':
        format_abbr = "prod-by-prod"
    else:
        raise ValueError("The 'format' parameter must be either 'industry by industry' or 'product by product'.")
        
    log.info(f"Extracting FIGARO IO table for year {year}, load IO table...")
    raw = pd.read_csv(os.path.join(source, f"matrix_eu-ic-io_{format_abbr}_{edition}ed_{year}.csv"), dtype = str)
    log.info("Loaded IO table")

    if sut in ["supply", "both"]:
        log.info(f"Check if supply table is available for year {year}...")
        if os.path.isfile(os.path.join(source, f"matrix_eu-ic-supply_{edition}ed_{year}.csv")):
            log.info("Supply table found, loading...")
            raw_supply = pd.read_csv(os.path.join(source, f"matrix_eu-ic-supply_{edition}ed_{year}.csv"), dtype = str)
            log.info("Loaded supply table")
    
    if sut in ["use", "both"]:    
        log.info(f"Check if use table is available for year {year}...")
        if os.path.isfile(os.path.join(source, f"matrix_eu-ic-use_{edition}ed_{year}.csv")):
            log.info("Use table found, loading...")
            raw_use = pd.read_csv(os.path.join(source, f"matrix_eu-ic-use_{edition}ed_{year}.csv"), dtype = str)
            log.info("Loaded use table")
        
    log.info("Extracting labels...")
    if edition == 24:
        df = pd.read_excel(os.path.join(source, f"Description_FIGARO_Tables({edition}ed).xlsx"), header=5, sheet_name = "Prod, Ind & Accounting items").dropna(axis=1, how='all')
    elif edition == 25:
        df = pd.read_excel(os.path.join(source, f"Description_FIGARO_Tables({edition}ed).xlsx"), header=3, sheet_name = "Prod, Ind & Accounting items").dropna(axis=1, how='all')
    else: 
        ValueError(f"Edition {edition} not yet supported. Please use edition 24 or 25.")
        
    # Countries are not in the correct order in the excel sheet, so get countries from raw data
    column_labs = raw.columns[1:]
    countries = column_labs.str.split("_").str[0]
    countries = list(dict.fromkeys(countries))

    # Get other labels from excel sheet
    sectors = df["Label.1"].tolist()
    cpa_labs = df["Label"].tolist()
    va_labs = df["Label.2"].dropna().tolist()
    y_labs = df["Label.3"].dropna().tolist()

    labels = {
        "countries": countries,
        "sectors": sectors,
        "y_labs": y_labs,
        "va_labs": va_labs 
    }
    c, s, y, va  = len(countries), len(sectors), len(y_labs), len(va_labs)
    if 'raw_supply' in locals() or 'raw_use' in locals():
        labels["cpa_labs"] = cpa_labs
        cpa =  len(cpa_labs)
    log.info("Labels extracted")
    
    log.info("Extracting parts from raw data...")
    raw = raw.iloc[:, 1:].astype(float).to_numpy()

    tables = {}
    tables["t"] = raw[:c*s, :c*s]
    tables["y"] = raw[:c*s, c*s:(c*s+c*y)]
    tables["va"] = raw[c*s:(c*s+c*va), :c*s]
    tables["vay"] = raw[c*s:(c*s+c*va), c*s:(c*s+c*y)]
    log.info("Extracted parts from raw data")

    # Treat supply table if available
    if 'raw_supply' in locals():
        log.info("Extracting supply table...")
        raw_supply = raw_supply.iloc[:, 1:].astype(float).to_numpy()
        tables["sup"] = raw_supply[:c*cpa, :c*s]
        log.info("Extracted supply table")
    else:
        log.info("No supply table found, skipping...")
        
    # Treat use table if available
    if 'raw_use' in locals():
        log.info("Extracting use table...")
        raw_use = raw_use.iloc[:, 1:].astype(float).to_numpy()
        tables["use_t"] = raw_use[:c*cpa, :c*s]
        tables["use_y"] = raw_use[:c*cpa, c*s:c*s + c*y]
        tables["use_va"] = raw_use[c*cpa:c*cpa+c*va, :c*s]
        tables["use_vay"] = raw_use[c*cpa:(c*cpa+c*va), c*s:(c*s+c*y)]
        log.info("Extracted use table")
    else:
        log.info("No use table found, skipping...")

    # Assemble mrio object
    log.info("Building MRIO object...")
    m = MRIO()
    m.add_dimensions(labels)
    log.info("Building MRIO objects from parts containing labels and tables...")
    m.parts["t"] = m.new_part(name="t",
        data= tables["t"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    log.info("t part added")
    m.parts["y"] = m.new_part(name="y",
        data= tables["y"],
        dimensions = [["countries","sectors"],["countries", "y_labs"]])
    log.info("y part added")
    m.parts["va"] = m.new_part(name="va",
        data= tables["va"],
        dimensions = ["va_labs",["countries", "sectors"]])
    log.info("va part added")
    m.parts["vay"] = m.new_part(name="vay",
        data= tables["vay"],
        dimensions = ["va_labs",["countries", "y_labs"]])
    log.info("vay part added")
    if 'sup' in tables:
        m.parts["sup"] = m.new_part(name="sup",
            data= tables["sup"],
            dimensions = [["countries","cpa_labs"],["countries", "sectors"]])
        log.info("sup part added")
    if 'use_t' in tables:
        m.parts["use_t"] = m.new_part(name="use_t",
            data= tables["use_t"],
            dimensions = [["countries","cpa_labs"],["countries", "sectors"]])
        log.info("use_t part added")
        m.parts["use_y"] = m.new_part(name="use_y",
            data= tables["use_y"],
            dimensions = [["countries","cpa_labs"],["countries", "y_labs"]])
        log.info("use_y part added")
        m.parts["use_va"] = m.new_part(name="use_va",
            data= tables["use_va"],
            dimensions = ["va_labs",["countries", "sectors"]])
        log.info("use_va part added")
        m.parts["use_vay"] = m.new_part(name="use_vay",
            data= tables["use_vay"],
            dimensions = ["va_labs",["countries", "y_labs"]])
        log.info("use_vay part added")
    log.info("MRIO object built")
    
    # Add metadata
    log.info("Adding metadata to MRIO object...")
    m.metadata["table"] = "figaro"
    m.metadata["edition"] = edition
    m.metadata["year"] = year
    m.metadata["format"] = format
    m.metadata["sut"] = sut
    m.name = f"figaro_{year}_{format}"
    return m