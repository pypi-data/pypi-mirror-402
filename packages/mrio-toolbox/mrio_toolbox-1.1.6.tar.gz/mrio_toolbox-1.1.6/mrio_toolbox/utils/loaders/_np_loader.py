"""
Routine for loading MRIO Parts from .npy and .csv files
"""

import os
import numpy as np
import pandas as pd
import logging
import yaml

log = logging.getLogger(__name__)

def load_file(file,extension=None,pandas=False,**kwargs):
    """
    Load data from a .npy, .txt, .xlsx or .csv file.

    Parameters
    ----------
    file : path-like
        Full path to the file
    kwargs : dict
        Additional parameters for the loaders

    Returns
    -------
    data : np.array
        Numerical data
    
    Raises
    ------
    FileNotFoundError
        If the file is not found in the specified path
    ValueError
        If the file extension is not supported
    """
    if extension is None:
        extension = os.path.splitext(file)[1]
    elif os.path.splitext(file)[1] == "":
        file = file+extension
    elif os.path.splitext(file)[1] != extension:
        raise FileNotFoundError(f"File {file} does not match the provided extension {extension}.")
    if extension == "":
        log.info("No extension provided. Trying .npy, .csv and .txt.")
        for loader in [load_npy,load_csv,load_txt,load_xlsx]:
            try:
                return loader(file)
            except FileNotFoundError:
                pass
        log.error(f"File {file} not found with extensions .npy, .csv or .txt.")
        raise FileNotFoundError(f"File {file} not found in the specified path.")
    if extension not in [".npy",".csv",".txt",".xlsx",".yaml"]:
        log.error(f"File extension {extension} not supported.")
        raise ValueError(f"File extension {extension} not supported.\nSupported extensions: .npy, .csv, .txt")
    if extension == ".npy":
        return load_npy(file,**kwargs)
    if extension == ".csv":
        return load_csv(file,pandas=pandas,**kwargs)
    if extension == ".txt":
        return load_txt(file,**kwargs)
    if extension == ".xlsx":
        return load_xlsx(file,**kwargs)
    if extension == ".yaml":
        return load_yaml(file,**kwargs)
    
def load_yaml(file,**kwargs):
    if os.path.splitext(file)[1] == "":
        file = file+".yaml"
    with open(file,"r") as f:
        return yaml.safe_load(f)

def load_npy(file,**kwargs):
    if os.path.splitext(file)[1] == "":
        file = file+".npy"
    return np.load(file,**kwargs)

def load_csv(file,pandas=False,**kwargs):
    """
    Read a .csv file using pandas or numpy.

    If pandas, the file is read using pandas,
    such that labels are automatically extracted.
    Otherwise, the file is read using numpy and labels are loaded from another file.
    """
    if os.path.splitext(file)[1] == "":
        file = file+".csv"
    delimiter = kwargs.get("delimiter",",")
    if pandas:
        #Remove header if not provided
        #This is to avoid issues with the label autodetection
        kwargs["header"] = kwargs.get("header",None)
        return pd.read_csv(file,
                           **kwargs)
    return np.loadtxt(file,delimiter=delimiter,**kwargs)

def load_txt(file,**kwargs):
    if os.path.splitext(file)[1] == "":
        file = file+".txt"
    delimiter = kwargs.get("delimiter","\t")
    try:
        return np.loadtxt(file,delimiter=delimiter,**kwargs)
    except ValueError:
        #If the basic loading fails, it's probably a label file
        return np.loadtxt(file,dtype=str,delimiter=delimiter,**kwargs).tolist()

def load_xlsx(file, **kwargs):
    if os.path.splitext(file)[1] == "":
        file = file+".xlsx"
    #Remove header if not provided
    #This is to avoid issues with the label autodetection
    kwargs["header"] = kwargs.get("header",None)
    return pd.read_excel(file,
                         **kwargs)