"""
Extractor for GLORIA data.

This extractor loads GLORIA raw data files and converts them to NetCDF
files.
  
Supports GLORIA version 059
https://ielab.info/labs/ielab-gloria 

Created on Fr Dez 20, 2024
@author: wirth, based on code of beaufils

"""

import os
import logging
import numpy as np
import pandas as pd
from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__)

def extract_gloria(
    year, 
    source,
    markup = 1,
    parts = "all", 
    precision=32):
    """
    Extract GLORIA data. 

    Loads GLORIA tables and labels and store them as NetCDF for further use with 
    the mrio_toolbox library. Currrently, this extractor supports loading T, Y, 
    VA, Q, and QY tables. 
    
    Put all tables (including emission satellite accounts) as well as the 
    'GLORIA_ReadMe_059a.xlsx' file in the same source folder. 
    

    Parameters
    ----------
    year : str
        Data year to load.
    parts : str
        Data blocks to load:
            basic : T, Y
            all : T, Y, VA, Q, QY
    markup : int
        Version of prices to load. Available versions: 
            1 : basic prices
            2 : trade margins
            3 : transport margins
            4 : taxes on products
            5 : subsidies on products
    source : path-like
        Path to folder where raw data is stored
    precision : int
        Floating point precision in bits. Default is 32. 
        This introduces some rounding error for large numbers. 
    """

    #Check source path
    source = source + f"/GLORIA_MRIOs_59_{year}"
    if not os.path.exists(source):
        log.error(f"{os.path.abspath(source)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(source)} does not exist.")

    # Gloria comes with 164 regions (160 countries + rest of americas, 
    # rest of europe, rest of africa, rest of asia-pacific) and 120 sectors. 

    if parts == "all":
        parts = ["T","Y","V","TQ","YQ"]
    elif parts == "basic":
        parts = ["T","Y", "V"]
    
    tables = {}
    
    if precision == 32:
        log.info("Data precision is 32 bits")
        dt = np.float32
    elif precision == 64:
        log.info("Data precision is 64 bits")
        dt = np.float64
    
    log.info("Loading Gloria labels...")
    labels = {} 
    countries = pd.read_excel(
        io = os.path.join(source, "GLORIA_ReadMe_059a.xlsx"),
        sheet_name = "Regions")
    countries = countries["Region_acronyms"].tolist()
    sectors = pd.read_excel(
        io = os.path.join(source, "GLORIA_ReadMe_059a.xlsx"),
        sheet_name = "Sectors")
    sectors = sectors["Sector_names"].tolist()
    va_and_y_labs = pd.read_excel(
        io = os.path.join(source, "GLORIA_ReadMe_059a.xlsx"),
        sheet_name = "Value added and final demand")
    va_labs= va_and_y_labs["Value_added_names"].tolist()
    y_labs = va_and_y_labs["Final_demand_names"].tolist()  
    q_labs = pd.read_excel(
        io = os.path.join(source, "GLORIA_ReadMe_059a.xlsx"),
        sheet_name = "Satellites")
    q_labs["combined"] = q_labs["Sat_head_indicator"] + " - " + q_labs["Sat_indicator"] + " - " + q_labs["Sat_unit"]
    q_labs = q_labs["combined"].tolist()

    labels["countries"] = countries
    labels["sectors"] = sectors
    labels["y_labs"] = y_labs
    labels["q_labs"] = q_labs
    labels["va_labs"] = va_labs
    log.info("Loaded Gloria labels")
    
    log.info("Loading Gloria tables, this can take a while...")
    for part in parts:
        if part == "T" or part == "Y":
            path = os.path.join(source, f'20240111_120secMother_AllCountries_002_{part}-Results_{year}_059_Markup00{markup}(full).csv')
        elif part == "V":
            path = os.path.join(source, f'20240419_120secMother_AllCountries_002_{part}-Results_{year}_059_Markup001(full).csv')
        elif part == "TQ" or part == "YQ":
            path = os.path.join(source, f'20240417_120secMother_AllCountries_002_{part}-Results_{year}_059_Markup00{markup}(full).csv')
        log.info(f"Loading {part} table...")
        tables[part] = load_and_transform_to_IO_structure(path, part, dt)
        log.info(f"Loaded {part} table")
        
    
    # build an MRIO object from labels and tables
    m = MRIO()
    m.add_dimensions(labels)
    
    m.parts["T"] = m.new_part(name="t",
        data= tables["T"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    log.info("Added T table")
    
    m.parts["Y"] = m.new_part(name="y",
        data= tables["Y"],
        dimensions = [["countries","sectors"],["countries", "y_labs"]])
    log.info("Added Y table")
    
    m.parts["VA"] = m.new_part(name="va",
        data= tables["V"],
        dimensions = ["va_labs",["countries","sectors"]])
    log.info("Added VA table")
    
    if parts == "all": 
        m.parts["Q"] = m.new_part(name="q",
            data= tables["TQ"],
            dimensions = ["q_labs",["countries","sectors"]])
        log.info("Added Q table")
        
        m.parts["QY"] = m.new_part(name="qy",
            data= tables["YQ"],
            dimensions = ["q_labs",["countries","y_labs"]])    
        log.info("Added QY table")

    m.name = f"gloria_{year}_markup00{markup}"
    return m

def load_and_transform_to_IO_structure(path, part, dt):
    c = 164 # number of countries
    s = 120 # number of sectors
    
    table = np.loadtxt(path, dtype=dt, delimiter=',')
    
    rows = np.arange(table.shape[0])
    columns = np.arange(table.shape[1])
    
    if part == "T": 
        selected_rows = (rows // s) % 2 == 1 # Starts with 120 off, then 120 on
        selected_columns = (columns // s) % 2 == 0 # starts with 120 on, then 120 off
    elif part == "Y":
        selected_rows = (rows // s) % 2 == 1 
        selected_columns = columns
    elif part == "V": 
        selected_rows = rows
        selected_columns = (columns // s) % 2 == 0
    elif part == "TQ":
        selected_rows = rows
        selected_columns = (columns // s) % 2 == 0
    elif part == "YQ":
        selected_rows = rows
        selected_columns = columns
               
    table = table[selected_rows][:, selected_columns]
    
    if part == "V":
        # Stack the entries to transform the pseudo-diagonalized 984x19680 shape into a 6x19680 shape
        
        block_height = 6
        block_width = 120 
        blocks = []

        for i in range (0, int(table.shape[0]/block_height)):
            block = table[i*block_height:(i+1)*block_height,
                           i*block_width:(i+1)*block_width]
            blocks.append(block)
            
        table = np.hstack(blocks)
       
    return table

