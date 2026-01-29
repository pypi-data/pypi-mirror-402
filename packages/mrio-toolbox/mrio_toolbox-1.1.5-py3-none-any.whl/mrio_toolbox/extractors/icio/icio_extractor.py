# -*- coding: utf-8 -*-
"""
Created on Wed May 11 16:15:09 2022
Major modifications on 04.02.2025 by wirth

Load and convert ICIO MRIO files. 
Please put the Readme excel file in the same folder as the data and adjust the filename in the code.

Supports ICIO 2021 in csv format
https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm

@author: beaufils and wirth
"""

import os
import logging
import pandas as pd

from mrio_toolbox import MRIO, Part 
from mrio_toolbox.utils.savers._to_nc import save_to_nc

log = logging.getLogger(__name__) 

def extract_icio(year, source, destination, extended=False):
    """
    Extract and convert ICIO MRIO data to NetCDF format for use with mrio_toolbox.

    This function loads ICIO tables and associated labels from raw OECD files,
    processes them, and stores the result as a NetCDF file. It supports both
    standard and extended ICIO formats (where China and Mexico are split).

    Parameters
    ----------
    year : str
        Year of the ICIO data to load (e.g., "2021").
    source : path-like
        Path to the folder containing the raw ICIO data and ReadMe Excel file.
    extended : bool, optional
        If True, loads the extended version of the ICIO tables (China and Mexico split).
        If False (default), loads the standard version.

    Notes
    -----
    - The ReadMe Excel file must be present in the same source folder as the xlsx data file.
    - Output filenames are automatically generated based on the year and format.
    """
    
    #Check source path
    if not os.path.exists(source):
        log.error(f"{os.path.abspath(source)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(source)} does not exist.")
    
    #Check destination path
    if not os.path.exists(destination):
        log.info(f"{os.path.abspath(
            destination)} does not exist. Creating directory.")
        os.makedirs(destination)
    
    # Adapt the filenames based on the extended parameter
    if extended:
        readme_filename = os.path.join(source, "ReadMe_ICIO_extended.xlsx")
        data_filename = os.path.join(source, f"{year}.csv")
    else:
        readme_filename = os.path.join(source,"ReadMe_ICIO_small.xlsx")
        data_filename = os.path.join(source, f"{year}_SML.csv")
    
    # Load the labels
    countries = pd.read_excel(readme_filename, sheet_name='Area_Activities', header=2)['countries'].dropna().to_list()
    # Filter out everything in parenthesis, such as the additional references (1) and (2) for Israel and Cyprus
    # as well as (People's Republic of China) for China and (People's Democratic Republic) for Lao
    countries = [country.split('(')[0].strip() for country in countries]
    sectors = pd.read_excel(readme_filename, sheet_name='Area_Activities', header=2)['Industry'].dropna().to_list()
    df = pd.read_excel(readme_filename, sheet_name='ColItems',header=3)
    index = df[df["Sector code"] == "Final demand items"].index[0]
    y_labs = df.iloc[index:,4].to_list()
    va_labs = ["Taxes less subsidies on intermediate and final products", "Value added at basic prices"]
    labels = {
        "countries": countries,
        "sectors": sectors,
        "y_labs": y_labs,
        "va_labs": va_labs
    }
    if extended:
        countries_y = countries[:-4] # remove MX1, MX2, CN1, CN2
        labels["countries_y"] = countries_y

    # Extract the raw data
    s,c = len(sectors),len(countries)
    raw = pd.read_csv(data_filename, header=0,index_col=0).to_numpy()
    tables = {} 
    tables["t"] = raw[:c*s,:c*s]
    tables["y"] = raw[:c*s,c*s:-1] # last column is cumulative output
    tables["va"] = raw[c*s:-1,:c*s]
    tables["vay"] = raw[c*s:-1,c*s:-1]

    # Build MRIO object
    m = MRIO()   
    m.add_dimensions(labels)
    m.parts["t"] = m.new_part(name="t", data= tables["t"],
        dimensions = [["countries","sectors"],["countries", "sectors"]])
    m.parts["va"] = m.new_part(name="va", data= tables["va"],
        dimensions = ["va_labs",["countries", "sectors"]])
    if extended:
        m.parts["y"] = m.new_part(name="y", data= tables["y"],
            dimensions = [["countries","sectors"],["countries_y", "y_labs"]])
        m.parts["vay"] = m.new_part(name="vay", data= tables["vay"],
            dimensions = ["va_labs",["countries_y", "y_labs"]])
    else:  
         m.parts["y"] = m.new_part(name="y",data= tables["y"],
            dimensions = [["countries","sectors"],["countries", "y_labs"]])
         m.parts["vay"] = m.new_part(name="vay", data= tables["vay"],
            dimensions = ["va_labs",["countries", "y_labs"]])   
 
    # Save the mrio object to a NetCDF file
    if extended:
        destination = os.path.join(destination, f"icio_year{year}_extended.nc")
    else:
        destination = os.path.join(destination, f"icio_year{year}.nc")
    save_to_nc(m, destination, overwrite=False)


