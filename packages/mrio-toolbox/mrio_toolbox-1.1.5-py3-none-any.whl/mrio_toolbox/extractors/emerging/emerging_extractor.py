"""
Extractor for Emerging MRIO

This extractor loads tables and labels from the Emerging MRIO .mat files files, 
builds an mrio object from the data and saves it as NetCDF for further use with
the mrio_toolbox library.
  
Supports Emerging v.1
https://zenodo.org/records/10956623 

Created on 18.03.2025
@author: wirth
"""

import os
import logging
import numpy as np
import h5py

from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__) 


def extract_emerging(year, source, precision=32):
    """
    Extract EMERGING data. 

    Loads EMERGING tables and labels and store them as NetCDF for further use with 
    the mrio_toolbox library. 

    Parameters
    ----------
    year : str
        Data year to load.
    source : path-like
        Path to folder where raw data is stored
    destination : path-like
        path to folder where NetCDF file will be saved
    precision : int
        Precision of the data in bits. Default is 32.
    """
    
    log.info(f"Opening EMERGING data for year {year}...")
    file_path = os.path.join(source, f"global_mrio_{year}.mat")
    
    #Check source path
    if not os.path.isfile(file_path):
        log.error(f"{os.path.abspath(file_path)} does not exist.")
        raise FileNotFoundError(f"{os.path.abspath(file_path)} does not exist.")
        
    f = h5py.File(file_path, "r")

    log.info("Extracting labels...")
    countries = []
    sectors = []
    y_labs = []
    va_labs = ["Value added"]
    
    for ref in f['country_list']:
        ref_key = ref.item()  # Convert NumPy array to scalar with the item function
        country_data = f['#refs#'][ref_key][:]
        country_name = ''.join(chr(c[0]) for c in country_data) # Convert ASCII codes to string
        countries.append(country_name)
    
    for ref_key in f["sector_list"][0]:
        sector_data = f['#refs#'][ref_key][:]
        sector_data = ''.join(chr(c[0]) for c in sector_data)
        sectors.append(sector_data)

    for ref_key in f['final_list'][0]:
        fd_data = f['#refs#'][ref_key][:]
        fd_data = ''.join(chr(c[0]) for c in fd_data)
        y_labs.append(fd_data)
        
    labels = {
    "countries": countries,
    "sectors": sectors,
    "y_labs": y_labs,
    "va_labs": va_labs
    }
    
    if precision == 32:
        log.info("Data precision is 32 bits")
        dt = np.float32
    elif precision == 64:
        log.info("Data precision is 64 bits")
        dt = np.float64
    
    log.info("Extracting data, this can take a while...")
    tables = {}
    tables["T"] = np.array(f["z"],dtype=dt)
    tables["Y"] = np.array(f["f"], dtype=dt).transpose() # y is provided transposed
    tables["VA"] = np.array(f["va"], dtype=dt) # No vay part provided
    
    # Assemble mrio object
    log.info("Building MRIO object...")
    m = MRIO()
    m.add_dimensions(labels)
    log.info("Building MRIO objects from parts containing labels and tables...")
    m.parts["T"] = m.new_part(name="T",
        data= tables["T"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    log.info("T part added")
    m.parts["Y"] = m.new_part(name="Y",
        data= tables["Y"],
        dimensions = [["countries","sectors"],["countries", "y_labs"]])
    log.info("Y part added")
    m.parts["VA"] = m.new_part(name="VA",
        data= tables["VA"],
        dimensions = ["va_labs",["countries", "sectors"]])
    log.info("VA part added")
    log.info("MRIO object built")

    m.name = f"emerging_{year}_{precision}bits_resolution"
    return m
