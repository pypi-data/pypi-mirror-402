"""
Extractor for WIOD 2016 files. 

This script extracts data from WIOD xlsb files and converts them to NetCDF files 
for further use with the MRIO toolbox. 

Supports WIOD 2016 in Excel format
https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release


Created on 08.01, 2024
@author: wirth, based on code of beaufils
"""

import os
import logging
import pandas as pd
from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__) 

def extract_wiod(
    year, 
    source):
    """
    Extract WIOD data. 

    Loads WIOD tables and labels and store them as NetCDF for further use with 
    the mrio_toolbox library. 

    Parameters
    ----------
    year : str
        Data year to load.
    parts : str
        Data blocks to load:
            basic : T, Y
            all : T, Y, VA, QT, QY
    source : path-like
        Path to folder where raw data is stored    
    """

        
    #Check source path
    if not os.path.exists(source):
        log.error(f"{os.path.abspath(source)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(source)} does not exist.")

    # WIOD 2016 comes with: 
    # - 43 countries + ROW 
    # - 56 sectors 
    # - 5 final demand categories
    # - 6 value added category, including 5 tax categories
    c,s,y,va = 44,56,5,6
    
    log.info("Start loading")
    
    tables = {}
    raw = load_raw_WIOD(source, year)
    countries, sectors, y_labs,  va_labs, = [],[],[],[]
    labels = raw.columns
    for i in range(c):
        countries.append(labels[i*s][2].strip())
    for i in range(s):
        sectors.append(labels[i][1].strip())
    for i in range(y):
        y_labs.append(labels[s*c + i][1].strip())
    for i in range(va):   
        va_labs.append(raw.index[s*c + 1 + i][1].strip())


    raw = raw.to_numpy()
    parts = ["t","y","va","vay"]
   
    for part in parts:
        if part == "t":
            tables[part] = raw[:c*s,:c*s]
        elif part == "y":
            tables[part] = raw[:c*s,c*s:-1]
        elif part == "va":
            tables[part] = raw[c*s+1:-1,:c*s]
        elif part == "vay":
            tables[part] = raw[c*s+1:-1,c*s:-1]

    # build an MRIO object from labels and tables        
    m = MRIO()   
    labels = {
        "countries" : countries,
        "sectors" : sectors, 
        "y_labs" : y_labs,
        "va_labs" : va_labs, # including 5 tax categories
        }
    m.add_dimensions(labels)
    
    m.parts["t"] = m.new_part(name="t",
        data= tables["t"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    m.parts["y"] = m.new_part(name="y",
        data= tables["y"],
        dimensions = [["countries","sectors"],["countries", "y_labs"]])
    m.parts["va"] = m.new_part(name="va",
        data= tables["va"],
        dimensions = ["va_labs",["countries", "sectors"]])
    m.parts["vay"] = m.new_part(name="vay",
        data= tables["vay"],
        dimensions = ["va_labs",["countries", "y_labs"]])
    
    m.name = f"wiod16_{year}"
    return m


def load_raw_WIOD(path, year,release=16):
    """
    Load the raw WIOD matrix

    Parameters
    ----------
    year : int-like
    release : int-like, optional
        Version of the WIOD database. The default is 2016.

    Returns
    -------
    Pandas DataFrame
        Full WIOD table as pandas DataFrame.

    """
    #Check source path
    
    path = os.path.join(path, f'WIOT{year}_Nov{release}_ROW.xlsb')
    if not os.path.exists(path):
        log.error(f"{os.path.abspath(path)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(path)} does not exist.")
    
    
    return pd.read_excel(path, header=[2,3,4,5],index_col=[0,1,2,3])

if __name__ == "__main__":
    extract_wiod(year=2014,
                release=16,
                source='/home/florian/job_merkator_institut/MRIO Projects/MRIOs/WIOD 2016 release',
                destination="/home/florian/job_merkator_institut/MRIO Projects/MRIOs/netCDF objects")
