"""
Provides the NetCDF_Loader class for loading MRIO data from netCDF files.
"""
from mrio_toolbox.utils.loaders._loader import Loader
from mrio_toolbox.utils import converters
import xarray as xr

import logging
import pandas as pd

log = logging.getLogger(__name__)

class NetCDF_Loader(Loader):
    """
    Class for loading MRIO data from a netCDF file.

    The `NetCDF_Loader` class extends the base `Loader` class to provide 
    functionality for loading MRIO data stored in netCDF format. It uses the 
    xarray library to load the data and extract metadata, labels, and groupings.

    Instance variables
    ------------------
    data : xarray.Dataset
        The loaded netCDF data stored as an xarray Dataset.
    _available_parts : list
        List of available parts in the MRIO data.
    metadata : dict
        Metadata extracted from the netCDF file.
    labels : dict
        Labels for the axes of the MRIO data.
    groupings : dict
        Groupings for the labels, defining higher-level aggregations.
    file : str or None
        Path to the netCDF file being loaded.
    loader_kwargs : dict
        Additional parameters passed to the xarray loader.

    Methods
    -------
    load_mrio(file=None, **kwargs):
        Load a netCDF file into memory and extract metadata.
    load_part(file=None, **kwargs):
        Load a specific part of the MRIO table.
    get_file(file=None, **kwargs):
        Get the file to load, updating the current file if necessary.
    available_parts(**kwargs):
        Return a list of available parts in the MRIO table.
    """
    
    def __init__(
            self,
            **kwargs
            ):
        """
        Initialize a NetCDF_Loader object.

        Parameters
        ----------
        loader_kwargs : dict, optional
            Parameters passed to the xarray loader.
        file : path-like
            Full path to the netCDF file.
        groupings : dict, optional
            Aggregation on labels
        **kwargs : dict
            Metadata for the MRIO data.
            MRIO metadata are passed to associated parts.

        """
        self.extract_basic_info(**kwargs)
        super().__init__()
        self.update_settings(**kwargs)
        
    def load_mrio(
            self,
            file = None,
            **kwargs
    ):
        """
        Load a netcdf file in the memory.

        This procedure is based on the xarray library.
        The xarray dataset is stored in the data attribute.
        The loader also extracts all metadata from the file.

        Parameters
        ----------
        file : path-like, optional
            Full path to the file.
            If left empty, the file currently initialised is used.

        Raises
        ------
        ValueError
            If the file is not provided.
        """
        
        if file is None:
            file = self.file

        if file is None:
            raise ValueError("No file provided.")
        
        log.info(f"Load MRIO data from {file}")
        self.data = xr.open_dataset(file, **self.loader_kwargs)
        mrio_data,list_of_parts = converters.xarray.make_mrio(self.data)
        self._available_parts = list_of_parts
        self.update_settings(**mrio_data["data"])


    def load_part(
            self,
            file = None,
            **kwargs
    ):
        """
        Load a part of the MRIO table.

        Parameters
        ----------
        name : str
            Name of the variable to load
        file : path, optional
            Full path to the data.
            If left empty, the current xarray Dataset is used.

        Returns
        -------
        dict
            Data required to create a Part object
        """
        self.get_file(file,**kwargs) #Update the file if needed
        return converters.xarray.make_part(
            self.data,**kwargs
            )
    
    def get_file(self, file=None, **kwargs):
        """
        Get the file to load.

        Parameters
        ----------
        file : path-like, optional
            User-defined path to the file, by default None

        Returns
        -------
        path-like
            Path to the file to load from

        Raises
        ------
        ValueError
            If no file is provided nor currently loaded
        
        """
        self.check_instructions(**kwargs)
        #Check if new instructions are provided

        if file is None and self.file is None:
            raise ValueError("No file provided.")
        
        instructions = self.metadata.get("instructions",None)

        if file != self.file and file != instructions:
            #If the file is different from the one currently loaded, the current data is replaced
            self.load_mrio(file)

        return file

    def available_parts(
            self,**kwargs
    ):
        """
        Return a list of available parts in the MRIO table.

        Returns
        -------
        list
            List of available parts
        """
        return self._available_parts

    