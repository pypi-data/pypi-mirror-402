"""
Extractor for Eora26 data.

This extractor loads Eora26 raw data files and converts them to NetCDF
files.
  
Supports Eora26 v199.82
https://worldmrio.com/eora26/

Created on Fr Nov 29, 2024
@author: wirth, based on code of beaufils

"""

import os
import logging
import numpy as np
from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__)

def extract_eora26(
    year, 
    source,
    parts = 'all'):
    """
    Extract EORA26 data. 

    Loads EORA26 tables and labels and store them as NetCDF for further use with 
    the mrio_toolbox library. 

    Parameters
    ----------
    year : str
        Data year to load.
    parts : str
        Data blocks to load:
            basic : T, FD
            all : T, FD, VA, QT, QY
    source : path-like
        Path to folder where raw data is stored
    """

    #Check source path
    if not os.path.exists(source):
        log.error(f"{os.path.abspath(source)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(source)} does not exist.")

    # EORA26 comes with 189 countries and 26 sectors
    c,s = 189,26

    # Usually, we want to extract all tables 
    if parts == "all":
        parts = ["T","FD","VA","Q","QY"]
    else:
        parts = ["T","FD"]
    
    # First, we create a dictionary of part objects
    tables = dict()
    
    
    for part in parts:
        tables[part] = np.loadtxt(
            os.path.join(source,f'Eora26_{year}_bp_{part}.txt'),
            delimiter = '\t')
        
        # Then, we have to exclude statistical discrepancies 
        # (RoW) row and column, so our data aligns with the number
        # of countries and sectors
        if part == "T":
            tables[part] = tables[part][:c*s,:c*s]
        elif part == "FD": 
            tables[part] = tables[part][:c*s,:c*6]
        elif part == "QY": 
            tables[part] = tables[part][:,:c*6]
        else: #Q, VA
            tables[part] = tables[part][:,:c*s]
    
    # Next, we load the labels
    labels = {} 
    # Split country and sector labels for multi-indexing
    labs = np.loadtxt(os.path.join(source, "labels_T.txt"),
                    dtype=str, delimiter ='\t')
    sectors = labs[:s,3].tolist()
    countries = []
    for i in range(c):
        countries.append(labs[i*s,1][:])

    # Omit countries and sectors from y_labs, they are already included
    # in sectors and countries labels. 
    y_labs = np.loadtxt(os.path.join(source, "labels_FD.txt"), 
                    dtype=str, delimiter ='\t')
    y_labs = y_labs[:6, 3].tolist()
    
    # q and y labels need to be reformatted into a single list
    q_labs = np.loadtxt(os.path.join(source, "labels_Q.txt"),
                    dtype=str,delimiter="\t")
    q_labs = [" - ".join(sub_array[:-1]) for sub_array in q_labs]

    va_labs = np.loadtxt(os.path.join(source, "labels_VA.txt"),
                    dtype=str,delimiter="\t")
    va_labs = [" - ".join(sub_array[:-1]) for sub_array in va_labs]     

    labels["countries"] = countries
    labels["sectors"] = sectors
    labels["y_labs"] = y_labs
    labels["q_labs"] = q_labs
    labels["va_labs"] = va_labs

    
    # build an MRIO object from labels and tables
    m = MRIO()
    m.add_dimensions(labels)
    m.parts["t"] = m.new_part(name="t",
        data= tables["T"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    m.parts["y"] = m.new_part(name="y",
        data= tables["FD"],
        dimensions = [["countries","sectors"],["countries", "y_labs"]])
    m.parts["va"] = m.new_part(name="va",
        data= tables["VA"],
        dimensions = ["va_labs",["countries","sectors"]])
    m.parts["q"] = m.new_part(name="q",
        data= tables["Q"],
        dimensions = ["q_labs",["countries","sectors"]])
    m.parts["qy"] = m.new_part(name="qy",
        data= tables["QY"],
        dimensions = ["q_labs",["countries","y_labs"]])

    m.name = f"eora26_{year}"
    return m
