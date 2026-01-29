"""
Routines for converting between xarray DataArrays and Parts objects.

"""
import pandas as pd
import xarray as xr
import numpy as np
import logging

log = logging.getLogger(__name__)

def to_DataArray(part,attrs=dict(),
    check_attrs = True):
    """
    Convert a Part object to an xarray DataArray

    Labels are directly passed to the DataArray as coords.

    Parameters
    ----------
    part : Part
        Part object to convert
    attrs : dict, optional
        Additional attributes to add to the DataArray, by default dict()
    check_attrs : bool, optional
        Whether to check the type of attributes to ensure compatibility with xarray, by default True
        
    Returns
    -------
    xr.DataArray
        Corresponding DataArray
    attrs : dict
        Additional information to save as attributes to the array
    """
    developed = part.develop(squeeze=False) #Force non-squeeze to keep dimensions
    old_dims = part.get_dimensions()
    new_dims = developed.get_dimensions()
    attrs = attrs
    if old_dims != new_dims:
        #We code the original dimensions in the metadata
        #Because netcdf files do not support multi-level attributes
        original_dims = [
            dim for axe in old_dims for dim in axe+["_sep_"]
            ]
        attrs["_original_dimensions"] = original_dims[:-1]
        #The last bit removes the last separator
    coords = list()
    for axe in developed.axes:
        coords.append(
            axe.label(True)
        )
    attrs.update(part.metadata)
    if check_attrs:
        keys = list(attrs.keys())
        #Ensure all attributes are of compatible type
        for key in keys:
            if not isinstance(attrs[key],(str,int,float,np.integer,np.floating,np.ndarray,list)):
                log.info(f"Attribute {key} of part {part.name} is of type {type(attrs[key])}, which is not compatible with xarray.")
                attrs.pop(key)
    return xr.DataArray(
        data = developed.data,
        name = part.name,
        attrs = attrs,
        coords = coords
    )

def to_DataSet(mrio):
    ds = xr.Dataset(
            attrs = mrio.metadata,
            coords = mrio.labels
        )
    for part in mrio.parts:
        ds[part] = mrio.parts[part].to_xarray()
    return ds

def make_part(data,**kwargs):
    """
    Load a Part object from an xarray DataArray

    Parameters
    ----------
    data : DataArray
        Part object to load
    name : str, optional
        Name of the data variable to load, by default None.
        This can be left empty if there's a single variable in the DataArray.

    Returns
    -------
    dict    
        Data required to create the Part object
    """
    part_data = dict()

    if isinstance(data,xr.Dataset):
        #Extract the data from the Dataset
        list_vars = list(data.data_vars)
        if len(list_vars) > 1:
            #In ambiguous cases, the name must be provided
            name = kwargs.get("name",None)
        else:
            name = list_vars[0]
        data = data[name]
    elif isinstance(data,xr.DataArray):
        name = data.name
    
    part_data["data"] = data.to_numpy()

    #Format the labels
    labels = []
    for key in data.dims:
        label = dict()
        index = data.indexes[key]
        label[index.name] = index.values.tolist()
        labels.append(label)
    part_data["name"] = name
    part_data["labels"] = labels
    part_data["metadata"] = kwargs.get("metadata",dict())
    for attr in data.attrs:
        #Add metadata
        part_data["metadata"][attr] = data.attrs[attr]
    part_data["groupings"] = kwargs.get("groupings",dict())
    return part_data

def make_mrio(data,**kwargs):
    """
    Load an MRIO object from an xarray DataSet

    Parameters
    ----------
    data : DataArray
        Part object to load

    Returns
    -------
    dict    
        Data required to create the Part object
    """
    #Extract the data from the xarray
    list_vars = list(data.data_vars)
    to_load = kwargs.get("parts",list_vars)

    mrio_data = dict()

    labels = dict()
    for coord in data.coords:
        labels[coord] = data[coord].values.tolist()
    mrio_data["labels"] = labels
    mrio_data["groupings"] = kwargs.get("groupings",dict())
    mrio_data["groupings"].update(data.attrs.get("groupings",dict()))
    mrio_data["metadata"] = data.attrs
    mrio_data["metadata"].update(kwargs.get("metadata",dict()))
    mrio_data["parts"] = dict()
    return {"data":mrio_data},to_load