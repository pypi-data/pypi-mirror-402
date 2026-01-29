"""
Routines for saving to netCDF files.
"""
import os
import yaml
import pandas as pd
from mrio_toolbox.utils.savers._path_checker import check_path
import logging
import xarray as xr

log = logging.getLogger(__name__)

def save_to_nc(obj,path,overwrite=False,write_instructions=False,**kwargs):
    """
    Save an MRIO or Part instance in a .nc file

    Parameters
    ----------
    path : str
        Path to the .nc file to save the MRIO instance into.
    
    **kwargs : dict
        Additional arguments to pass to the saver.
    """
    log.info(f"Saving {obj.__class__.__name__} instance to {path}")
    if os.path.dirname(path) == "":
        path = os.path.join(os.getcwd(), path)
    #Check destination path
    if not os.path.exists(os.path.dirname(path)):
        log.info(f"{os.path.abspath(
        os.path.dirname(path))} does not exist. Creating directory.")
        os.makedirs(os.path.dirname(path))

    ds = obj.to_xarray()

    #Remove dict attrs (not supported for serialization)
    attrs = list(ds.attrs.keys())
    for attr in attrs:
        if isinstance(ds.attrs[attr],dict):
            log.warning(f"Attribute {attr} is a dict. It will not be saved.")
            ds.attrs.pop(attr)

    if isinstance(ds, xr.Dataset):
        for var in ds.data_vars:
            attrs = list(ds[var].attrs.keys())
            for attr in attrs:
                if isinstance(ds[var].attrs[attr],dict):
                    log.warning(f"Attribute {attr} of {var} is a dict. It will not be saved.")
                    ds[var].attrs.pop(attr)

    if not overwrite:
        path = check_path(path)
    ds.to_netcdf(path,**kwargs)
    if write_instructions:
        instructions = {
            "file": path
        }
        base_path, ext = os.path.splitext(path)
        with open(base_path+".yaml","w") as file:
            yaml.dump(instructions,file)