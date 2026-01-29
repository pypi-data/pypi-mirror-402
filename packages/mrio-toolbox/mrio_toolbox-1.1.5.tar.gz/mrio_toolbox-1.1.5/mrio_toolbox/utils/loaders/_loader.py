"""
Central loading module for the mrio_toolbox package.

This module contains the central loading function for the mrio_toolbox package.
Depending on the loading mode, the function will call the appropriate loader.
"""

import os
import logging
import yaml

log = logging.Logger(__name__)

class Loader:
    """
    Parent class for loaders in the MRIO toolbox.

    The `Loader` class provides a base implementation for loading MRIO data. 
    It includes methods for extracting metadata, updating settings, and managing 
    groupings and labels. Specific loaders can inherit from this class to implement 
    format-specific loading functionality.

    Instance variables
    ------------------
    metadata : dict
        Metadata associated with the loader.
    labels : dict
        Labels for the axes of the MRIO data.
    groupings : dict
        Groupings for the labels, defining higher-level aggregations.
    file : str or None
        Path to the file being loaded.
    loader_kwargs : dict
        Additional parameters for the loader.

    Methods
    -------
    extract_basic_info(**kwargs):
        Extract basic information such as path, labels, and groupings.
    update_settings(**settings):
        Update the loader settings with new parameters.
    load_mrio():
        Create an MRIO container based on the current parameters.
    load_part(**kwargs):
        Load an MRIO Part based on new or existing parameters.
    set_groupings(groupings):
        Update the groupings attribute of the loader.
    update_attributes(**kwargs):
        Update the current attributes of the loader.
    load_groupings(file, dimension=None, path=None):
        Load groupings from a file.
    set_labels(labels):
        Update the labels attribute of the loader.
    available_parts(**kwargs):
        Return the available parts in the MRIO data.
    check_instructions(**kwargs):
        Interpret the file argument for loading a part and check for instruction consistency.

    Notes
    -----
    This class is intended to be used as a base class for specific loaders. 
    It provides general functionality for managing metadata, labels, and groupings, 
    but does not implement actual data loading.
    """
    def __init__(
            self
            ):
        """
        Initialize a Loader object.
        
        Notes
        -----
        Loaders are created with format-specific parameters. They hold metadata and methods to load MRIO data.
        A loader is created using the base class if no specific loader is required,
        i.e., if the data is directly loaded from dict, pandas or xarray.
        In that case, the loader will fail when used,
        triggering the creation of a specific loader.
        """
        self.load_mrio()

    def extract_basic_info(self,**kwargs):
        """
        Extract basic information from the loader.

        The function will extract the path, labels and groupings from the loader.
        """
        self.loader_kwargs = kwargs.pop("loader_kwargs",dict())
        self.file = kwargs.get("file",None)
        self.groupings = kwargs.get("groupings",dict())
        self.labels = kwargs.get("labels",dict())
        #Remaining kwargs are metadata
        self.metadata = kwargs
        if isinstance(self.groupings,str):
            self.groupings = self.load_groupings(self.groupings)

    def update_settings(self,**settings):
        """
        Update the loader settings with new parameters
        """
        self.loader_kwargs.update(
            settings.pop("loader_kwargs",dict())
        )
        self.groupings.update(
            settings.pop("groupings",dict())
        )
        self.labels.update(
            settings.pop("labels",dict())
        )
        self.metadata.update(
            settings.pop("metadata",dict())
        )
        self.metadata.update(settings)


    def load_mrio(
            self
    ):
        """
        Create an MRIO container based on the new parameters

        Returns
        -------
        dict
            Dictionary of MRIO metadata
        """
        self.metadata = dict()
        self.labels = dict()
        self.groupings = dict()
        self.file = None
        pass

    def load_part(
            self,
            **kwargs
    ):
        """
        Load an MRIO Part based on new or existing parameters

        Returns
        -------
        dict
            Dictionary containing the Part data
        """
        raise FileNotFoundError("No proper loader was initialised.\n"+\
        "The loader needs to be reloaded with new instructions.")

    def set_groupings(self,groupings):
        """
        Update the groupings attribute of the loader

        Parameters
        ----------
        groupings : dict of dict of str
            Aggregation on labels
        """
        self.groupings = groupings
    
    def update_attributes(self,**kwargs):
        """
        Update the current attributes of the loader.

        The function will update the groupings, paths, labels and metadata attributes.
        """
        if "groupings" in kwargs:
            log.debug("Update groupings")
            self.groupings = kwargs.pop("groupings",self.groupings)
            
        self.extract_path(update=True,**kwargs)

        if "labels" in kwargs:
            log.debug("Update labels")
            self.format_labels(kwargs.pop("labels"))

        for kwarg in kwargs:
            log.debug(f"Override parameter {kwarg} with explicit parameter {kwargs[kwarg]}")
            self.metadata[kwarg] = kwargs[kwarg]
            
    def load_groupings(self,
                       file,
                       dimension=None,
                       path=None):
        """Load groupings from a file
        
        Parameters
        ---------- 
        file : str
            Name of the file to load
        dimension : str, optional
            Name of the dimension to load groupings for.
            By default (None), the file is interpreted as a preset
            of groupings on different dimension.
        path : path-like, optional
            Path where the file is stored. 
            By default, the groupings are from the settings dir
            in the working dir.
        """
        def _check_groupings(groupings,dimension):
            """Check whether the groupings are consistent with the labels"""
            for key in groupings.keys():
                for item in groupings[key]:
                    if item not in self.labels[dimension]:
                        log.warning(
                            f"Item {item} not found in {dimension} labels"
                            )
                        groupings[key].remove(item)
                if len(groupings[key])==0:
                    log.warning(f"Group {key} is empty")
                    groupings.pop(key)
            return groupings
    
        def load_grouping(file,level,path):
            """Load a single grouping file"""
            path = os.path.join(path,level)
            with open(os.path.join(path,file+'.txt')) as f:
                group = f.read().splitlines()
            return {file:group}
        
        if path is None:
            path = os.path.join("parameters","groupings")

        #If no dimension is specified, interpret as a preset
        output = dict()
        if isinstance(file,str):
            log.info("Load groupings set from "+path+file)
            with open(os.path.join(path,file)) as f:
                groupings = yaml.safe_load(f)
        elif isinstance(file,dict):
            groupings = file
        output = self.groupings
        
        if dimension is None:
            dimensions = list(groupings.keys())
            output = dict()
        for level in dimensions:
            if isinstance(groupings[level],dict):
                #Case the preset explicitly defines a grouping
                groupings[level] = _check_groupings(
                    groupings[level],level
                    )
                output[level] = groupings[level]
                continue
            if isinstance(groupings[level],str):
                groupings[level] = [groupings[level]]
            if isinstance(groupings[level],list):
                #Otherwise, interpret as a list of groupings
                output[level] = dict()
                covered = []
                for item in groupings[level]:
                    #Load all groupings
                    groups= load_grouping(
                        item,level,path
                    )
                    if any([group in covered for group in groups]):
                        duplicate = [
                            group for group in groups if group in covered
                            ]
                        log.warning("The following items are covered in "+\
                                    "multiple groupings: "+duplicate)
                    covered += groups
                    output[level][item] = groups
        return output
    
    def set_labels(self,labels):
        """
        Update the labels attribute of the loader

        Parameters
        ----------
        labels : dict of str:list of str
            Labels of the axes
        """
        self.labels = labels

    def available_parts(self,**kwargs):
        """
        Return the available parts in the MRIO data
        """
        if self.file is None:
            raise FileNotFoundError("No file was provided.")

    def check_instructions(self,**kwargs):
        """
        Interpret the file argument for loading a part.

        This method solves the ambiguity between data files and optional
        .yaml instructions.
        If the file argument refers to an instruction file, it is compared
        to the current instructions.
        If the data file or instruction file differ from the ones currently loaded,
        an exception is raised to force a reload.

        Parameters
        ----------
        file : path-like
            User-provided file path
        kwargs : additional arguments

        Raises
        ------
        FileNotFoundError
            If the loader needs to be reloaded with new instructions.
        
        """
        #The 'instructions' attribute is used to check if the loader needs to be reloaded
        #It contains the reference to the potential yaml file used to load the data
        new_instructions = kwargs.get("instructions",None)
        ref_instructions = self.metadata.get("instructions",None)
        if new_instructions is not None and ref_instructions != new_instructions:
            #If the instructions differ from the current ones,
            #trigger a reload of the loader
            log.error("The loader needs to be reloaded with new instructions.")
            raise FileNotFoundError("The loader needs to be reloaded with new instructions.")