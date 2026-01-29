"""
Created on Wed Mar 29 10:43:49 2023

Load and convert Exiobase Industries MRIO files.

Supports Exiobase 3.9.5 in csv https://zenodo.org/records/14869924 

This is the supporting information excel sheet:
https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1111%2Fjiec.12715&file=jiec12715-sup-0009-SuppMat-9.xlsx

@author: wirth
"""

import os
import pandas as pd
import logging
from mrio_toolbox import MRIO
from mrio_toolbox.utils.savers._to_nc import save_to_nc

s,c = 163,49
log = logging.getLogger(__name__)

def extract_exiobase3(
    year, 
    source,
    mode="ixi",
    satellites = 'basic'):
    
    """
    Load and preformat an EXIOBASE 3 table.

    Parameters
    ----------
    year : str
        Data year to load.
    source : path-like
        Path to folder where raw data is stored
    satellites : str
        Satellite accounts to load:
            basic : air emissions
            all : air_emissions, employment, energy, land, material, nutrients, water
    path : path-like
        Path to raw data.

    Returns
    -------
    tables : dict of {str : 2D numpy array}
        Keys correspond to matrix parts.
        Values are the numerical tables stored as numpy arrays.
    labels : dict of {str : list of str}
        Dictionnary of countries and sectors labels.

    """
    source = os.path.join(source, f"IOT_{year}_{mode}")
    #Check source path
    if not os.path.exists(source):
        log.error(f"{os.path.abspath(source)} does not exist.")
        raise NotADirectoryError(f"{os.path.abspath(source)} does not exist.")
        
    # EXIOBASE 3 comes with: 
    # - 43 countries + 5 ROW regions 
    # - 163 industries
    # - 9 final demand categories
    # - 9 value added categories including taxes
    # - various satellite accounts
     #c,s,y,va = 48,163, 5, 9,

    parts = ["t", "y", "va", "vay", "q_air", "qy_air"]
    
    # Load labels
    log.info("Loading labels...")
    countries = pd.read_csv(os.path.join(source,"unit.txt"), delimiter="\t")
    countries = countries["region"].tolist()
    seen = set()  # Remove duplicates while preserving order
    countries = [x for x in countries if not (x in seen or seen.add(x))]
    sectors = pd.read_csv(os.path.join(source,"unit.txt"), delimiter="\t")
    sectors = sectors[sectors["region"] == "AT"]["sector"].tolist()
    y_labs = pd.read_csv(os.path.join(source,"Y.txt"), header=1, dtype= "str", delimiter="\t")
    y_labs = y_labs.columns[2:9]
    va_labs = pd.read_csv(os.path.join(source, "factor_inputs", "unit.txt"), dtype= "str", delimiter="\t")
    va_labs = va_labs.iloc[:,0].tolist()
    q_labs_air_emissions = pd.read_csv(os.path.join(source, "air_emissions", "unit.txt"), dtype= "str", delimiter="\t")
    q_labs_air_emissions = q_labs_air_emissions.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
    
    labels = {
            "countries" : countries,
            "sectors" : sectors, 
            "y_labs" : y_labs,
            "va_labs" : va_labs,
            "q_labs_air_emissions" : q_labs_air_emissions,
            }
    
    if satellites == 'all':
        
        parts.extend(["q_employment", "qy_employment", "q_energy", "qy_energy", "q_land", "qy_land", "q_material", "qy_material", "q_nutrients", "qy_nutrients", "q_water", "qy_water"])
        
        q_labs_employment  = pd.read_csv(os.path.join(source, "employment", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_employment"] = q_labs_employment.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
        q_labs_energy  = pd.read_csv(os.path.join(source, "energy", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_energy"] = q_labs_energy.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
        q_labs_land  = pd.read_csv(os.path.join(source, "land", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_land"] = q_labs_land.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
        q_labs_material  = pd.read_csv(os.path.join(source, "material", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_material"] = q_labs_material.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
        q_labs_nutrient  = pd.read_csv(os.path.join(source, "nutrients", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_nutrient"] = q_labs_nutrient.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
        q_labs_water  = pd.read_csv(os.path.join(source, "water", "unit.txt"), dtype= "str", delimiter="\t")
        labels["q_labs_water"] = q_labs_water.apply(lambda row: f"{row.iloc[0]} - {row.iloc[1]}", axis=1).tolist()
    
    log.info("Labels loaded")
        
    # Load tables

    tables = {}
    log.info("Loading IO tables, this can take a while...")
    for part in parts: 
        
        
        if part == "t": 
             tables[part] = pd.read_csv(os.path.join(source, "Z.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 2:].to_numpy().astype(float)
             log.info(f"Loaded {part}")
        elif part == "y":
            tables[part] = pd.read_csv(os.path.join(source, "Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 2:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "va":
            tables[part] = pd.read_csv(os.path.join(source, "factor_inputs", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "vay":
            tables[part] = pd.read_csv(os.path.join(source, "factor_inputs", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_air":
            tables[part] = pd.read_csv(os.path.join(source, "air_emissions", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_air":
            tables[part] = pd.read_csv(os.path.join(source, "air_emissions", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_employment":
            tables[part] = pd.read_csv(os.path.join(source, "employment", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_employment":
            tables[part] = pd.read_csv(os.path.join(source, "employment", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_energy":
            tables[part] = pd.read_csv(os.path.join(source, "energy", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_energy":
            tables[part] = pd.read_csv(os.path.join(source, "energy", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_land":
            tables[part] = pd.read_csv(os.path.join(source, "land", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_land":
            tables[part] = pd.read_csv(os.path.join(source, "land", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_material":
            tables[part] = pd.read_csv(os.path.join(source, "material", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_material":
            tables[part] = pd.read_csv(os.path.join(source, "material", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_nutrients":
            tables[part] = pd.read_csv(os.path.join(source, "nutrients", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_nutrients":
            tables[part] = pd.read_csv(os.path.join(source, "nutrients", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "q_water":
            tables[part] = pd.read_csv(os.path.join(source, "water", "F.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        elif part == "qy_water":
            tables[part] = pd.read_csv(os.path.join(source, "water", "F_Y.txt"), delimiter = "\t", dtype = "str", header = None).iloc[3:, 1:].to_numpy().astype(float)
            log.info(f"Loaded {part}")
        else:
            tables[part] = None
            log.info(f"Didn't load {part}")
        
    log.info("Tables loaded")
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
        dimensions = ["va_labs",["countries","sectors"]])
    log.info("va part added")
    m.parts["vay"] = m.new_part(name="vay",
        data= tables["vay"],
        dimensions = ["va_labs",["countries","y_labs"]])
    log.info("vay part added")
    m.parts["q_air"] = m.new_part(name="q_air",
        data = tables["q_air"],
        dimensions = ["q_labs_air_emissions",["countries","sectors"]])
    log.info("q_air part added")
    m.parts["qy_air"] = m.new_part(name="qy_air",
        data = tables["qy_air"],
        dimensions = ["q_labs_air_emissions",["countries","y_labs"]])
    log.info("qy_air part added")
    
    if(satellites == 'all'): 
        m.parts["q_employment"] = m.new_part(name="q_employment",
        data = tables["q_employment"],
        dimensions = ["q_labs_employment",["countries","sectors"]])
        log.info("q_employment part added")
        
        m.parts["qy_employment"] = m.new_part(name="qy_employment",
            data = tables["qy_employment"],
            dimensions = ["q_labs_employment",["countries","y_labs"]])
        log.info("qy_employment part added")
        
        m.parts["q_energy"] = m.new_part(name="q_energy",
        data = tables["q_energy"],
        dimensions = ["q_labs_energy",["countries","sectors"]])
        log.info("q_energy part added")
        
        m.parts["qy_energy"] = m.new_part(name="qy_energy",
            data = tables["qy_energy"],
            dimensions = ["q_labs_energy",["countries","y_labs"]])
        log.info("qy_energy part added")
        
        m.parts["q_land"] = m.new_part(name="q_land",
        data = tables["q_land"],
        dimensions = ["q_labs_land",["countries","sectors"]])
        log.info("q_land part added")
        
        m.parts["qy_land"] = m.new_part(name="qy_land",
            data = tables["qy_land"],
            dimensions = ["q_labs_land",["countries","y_labs"]])
        log.info("qy_land part added")
        
        m.parts["q_material"] = m.new_part(name="q_material",
        data = tables["q_material"],
        dimensions = ["q_labs_material",["countries","sectors"]])
        log.info("q_material part added")
        
        m.parts["qy_material"] = m.new_part(name="qy_material",
            data = tables["qy_material"],
            dimensions = ["q_labs_material",["countries","y_labs"]])
        log.info("qy_material part added")
        
        m.parts["q_nutrients"] = m.new_part(name="q_nutrients",
        data = tables["q_nutrients"],
        dimensions = ["q_labs_nutrient",["countries","sectors"]])
        log.info("q_nutrients part added")
        
        m.parts["qy_nutrients"] = m.new_part(name="qy_nutrients",
            data = tables["qy_nutrients"],
            dimensions = ["q_labs_nutrient",["countries","y_labs"]])
        log.info("qy_nutrients part added")
        
        m.parts["q_water"] = m.new_part(name="q_water",
        data = tables["q_water"],
        dimensions = ["q_labs_water",["countries","sectors"]])
        log.info("q_water part added")
        
        m.parts["qy_water"] = m.new_part(name="qy_water",
            data = tables["qy_water"],
            dimensions = ["q_labs_water",["countries","y_labs"]])
        log.info("qy_water part added")

    m.name = f"exiobase3_{year}_{mode}_{satellites}_satellites"
    return m

