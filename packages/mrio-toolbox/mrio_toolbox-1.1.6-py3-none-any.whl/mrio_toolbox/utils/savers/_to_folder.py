"""
Routines for saving MRIO and Part instances to folders.
"""

import os
from mrio_toolbox.utils.savers._path_checker import check_path
import numpy as np
import yaml
import pandas as pd

import logging

log = logging.getLogger(__name__)

def save_mrio_to_folder(obj,
                        path,
                        name=None,
                        extension=".npy",
                        overwrite=False,
                        **kwargs):
    """
    Save an MRIO instance in a folder

    Parameters
    ----------
    path : str
        Path to the folder to save the MRIO instance into.
    extension : str, optional
        Extension of the files to save the MRIO instance into.
        The default is "npy".
    overwrite : bool, optional
        Whether to overwrite the existing files. The default is False.
        If False, the version name is iterated until a non-existing
        file name is found.
    kwargs : dict
        Additional arguments to pass to the saver.
    """
    if name is None:
        name = os.path.basename(path)+".yaml"
    if not os.path.isdir(path):
        os.mkdir(path)
    elif not overwrite:
        os.mkdir(check_path(path))
    log.info(f"Saving MRIO instance {name} to folder {path}")
    kwargs.pop("write_instructions", None) #Instructions are written anyway
    loading_instructions = dict()
    loading_instructions.update(obj.metadata)
    loading_instructions["path"] = path
    parts_instructions = dict()
    for part in obj.parts:
        save_part_to_folder(
            obj.parts[part],
            path,
            extension=extension,
            overwrite=overwrite,
            include_labels=False,
            write_instructions=False,
            **kwargs
        )
        #Save part metadata
        parts_instructions[part] = dict()
        parts_instructions[part]["dimensions"] = obj.parts[part].get_dimensions()
        parts_instructions[part]["metadata"] = obj.parts[part].metadata
    write_labels(path,obj.labels)
    loading_instructions["parts"] = parts_instructions
    loading_instructions["extension"] = extension
    with open(os.path.join(path+".yaml"),"w") as file:
        yaml.dump(loading_instructions,file)

def write_labels(path,labels):
    """
    Save labels in a folder

    Parameters
    ----------
    path : str
        Path to the folder to save the labels into.
    extension : str, optional
        Extension of the files to save the labels into.
        The default is "txt".
    overwrite : bool, optional
        Whether to overwrite the existing files. The default is False.
        If False, the version name is iterated until a non-existing
        file name is found.
    kwargs : dict
        Additional arguments to pass to the saver.
    """
    with open(os.path.join(path,"labels.yaml"),"w") as file:
        yaml.dump(labels,file)

def save_part_to_folder(obj,
                        path,
                        name=None,
                        extension=".npy",
                        save_labels=True,
                        write_instructions=True,
                        overwrite=False,
                        include_labels=True,
                        **kwargs):
    """
    Save a Part instance in a folder

    Parameters
    ----------
    obj : Part
        Part instance to save
    path : str
        Path to the folder to save the Part instance into.
    extension : str, optional
        Extension of the files to save the Part instance into.
        The default is ".npy".
    save_labels : bool, optional
        Whether to save the labels. The default is True.
    save_instructions : bool, optional
        Whether to save the instructions. The default is True.
    overwrite : bool, optional
        Whether to overwrite the existing files. The default is False.
        If False, the version name is iterated until a non-existing
        file name is found.
    include_labels: bool, optional
        Whether to include the labels in the file. The default is True.
        This is only relevant for .csv and .xlsx files.
        If False, the labels are saved in a separate file.
    kwargs : dict
        Additional arguments to pass to the saver.
    """
    if name is None:
        name = obj.name
    log.info(f"Saving Part instance {name} to folder {path} with extension {extension}")
    if not os.path.isdir(path):
            os.mkdir(path)
    elif not overwrite:
        os.mkdir(check_path(path))
    if save_labels:
        write_labels(path,obj.labels)
    parts_instructions = dict()
    if write_instructions:
        parts_instructions["dimensions"] = obj.get_dimensions()
        parts_instructions["metadata"] = obj.metadata
    if extension == ".npy":
        np.save(os.path.join(path,name+extension),obj.data,**kwargs)
    elif extension == ".csv":
        delimiter = kwargs.pop("delimiter",",")
        if include_labels:
            obj.to_pandas().to_csv(os.path.join(path,name+extension),
                                   **kwargs)
            parts_instructions["index_col"] = [i for i in range(len(obj.axes[0].dims))]
            if len(obj.axes) > 1:
                parts_instructions["header"] = [i for i in range(len(obj.axes[1].dimensions))]
        else:
            np.savetxt(os.path.join(path,name+extension),obj.data,
                    delimiter=delimiter,**kwargs)
    elif extension == ".txt":
        delimiter = kwargs.pop("delimiter","\t")
        np.savetxt(os.path.join(path,name+extension),obj.data,
                   delimiter=delimiter,**kwargs)
    elif extension == ".xlsx":
        obj.to_pandas().to_excel(os.path.join(path,name+extension),
                                 **kwargs)
    else:
        raise NotImplementedError(f"Extension {extension} not supported")
    if write_instructions:
        parts_instructions["file"] = os.path.join(path,name+extension)
        with open(os.path.join(path,name+".yaml"),"w") as file:
            yaml.dump(parts_instructions,file)