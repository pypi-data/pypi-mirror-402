"""
Initialize the appropriate loader based on the provided parameters.
"""
import os
import yaml
from mrio_toolbox.utils.loaders._nc_loader import NetCDF_Loader
from mrio_toolbox.utils.loaders._parameter_loader import Parameter_Loader
from mrio_toolbox.utils.loaders._pandas_loader import Pandas_Loader
from mrio_toolbox.utils.loaders._loader import Loader
import logging

log = logging.getLogger(__name__)

def make_loader(**kwargs):
    """
    Initialize the appropriate loader based on the provided parameters.

    If a file or data_file is provided, 
    the function will attempt to determine the appropriate loader based on the file extension.

    Namely:
    - .nc files are loaded using the NetCDF_Loader
    - .yaml files are interpreted as loading instructions
    
    All non-netCDF files are loaded using the Parameter_Loader.
    """
    file = kwargs.get("file",None)
    if file is not None:
        file = os.path.abspath(file) # Avoid issue with UNIX/windows path
    extension = kwargs.get("extension",None)

    if extension is None:
        if file is None:
            log.info("No file or extension provided.")
            log.info("An empty loader will be created.")
            return Loader()
        extension = os.path.splitext(file)[1]
        if extension == "":
            log.error("File extension missing.")
            raise ValueError("File extension missing.")
        
    if extension == "":
        log.error("File extension missing.")
        raise ValueError("File extension missing.")
    if extension == ".nc":
        return NetCDF_Loader(**kwargs)
    if extension in [".yaml",".yml"]:
        return load_from_yaml(**kwargs)
    if extension in [".npy",".txt"]:
        return Parameter_Loader(**kwargs)
    if extension in [".csv"]:
        if "loader_kwargs" in kwargs:
            pandas = kwargs["loader_kwargs"].pop(
                "pandas",False
                )
            if pandas:
                return Pandas_Loader(**kwargs)
        return Parameter_Loader(**kwargs)
    if extension == ".xlsx":
        return Pandas_Loader(**kwargs)
    log.error(f"File extension {extension} not supported.")

def load_from_yaml(**kwargs):	
    """
    Create a loader based on yaml file instructions.

    Parameters
    ----------
    file : path-like
        Full path to the .yaml file
    """
    instructions = kwargs.pop("file")
    log.info("Get loading instructions from: "+instructions)
    with open(instructions) as f: 
        parameters = yaml.safe_load(f)
    for kwarg in kwargs:
        #Override parameters with kwargs
        log.debug(f"Override file parameter {kwarg} with explicit parameter {kwargs[kwarg]}")
        parameters[kwarg] = kwargs[kwarg]

    # Error handling
    if "path" not in parameters.keys(): 
        if "file" not in parameters.keys(): 
            log.info("No path provided, using current working directory instead")
            parameters["path"] = os.getcwd()
    elif not os.path.isdir(parameters["path"]):
        log.error("Provided path is not a directory")
        raise ValueError("Provided path is not a directory")
    

    return make_loader(instructions=instructions,**parameters)


    

    