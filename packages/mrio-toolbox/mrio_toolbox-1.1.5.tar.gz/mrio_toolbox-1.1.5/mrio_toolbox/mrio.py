# -*- coding: utf-8 -*-
"""
This module provides the MRIO class.

Created on Thu Mar 30 10:42:23 2023
@author: beaufils
"""

import os
import numpy as np
import logging
import xarray as xr
import pandas as pd
from mrio_toolbox._parts import Part
from mrio_toolbox.utils import converters
from mrio_toolbox.utils.loaders import make_loader
from mrio_toolbox.utils.savers import save_mrio_to_folder,save_to_nc
from mrio_toolbox.utils.formatting import formatter

log = logging.getLogger(__name__)

class MRIO:
    """
    Representation of an MRIO table

    An MRIO table holds a collection of Parts, each representing a different aspect 
    of the table (e.g., inter-industry matrix, final demand, satellite accounts, etc).
    The MRIO instance allows performing basic operations on the table, such as
    loading parts, setting groupings, filtering, aggregating, and saving data.

    Instance variables
    ------------------
    metadata : dict
        Dictionary storing the metadata of the MRIO table.
    labels : dict
        Labels of the table parts, including:
            - List of countries
            - List of sectors
    groupings : dict
        Groupings of the MRIO table. Groupings are used to group labels into 
        larger categories (e.g., countries into zones, sectors into aggregate 
        sectors). These groupings are primarily used for visualization or 
        aggregation purposes.
    c : int
        Number of countries in the table.
    s : int
        Number of sectors in the table.
    parts : dict of Part objects
        Dictionary containing the different parts of the MRIO table.

    Methods
    -------
    __init__(**kwargs):
        Initialize an MRIO instance from a file or explicit parameters.
    load_part(update_part=True, standalone=False, **kwargs):
        Load a Part object into the MRIO table.
    set_groupings(groupings=None):
        Set the groupings of the MRIO table.
    filter(threshold, fill_value=0):
        Filter the MRIO table by removing values below a specified threshold.
    add_part(part, name=None, update_part=True):
        Add a Part object to the MRIO table.
    new_part(data=None, name="part", dimensions=None, fill_value=0.0, **kwargs):
        Create a new Part object from data or dimensions.
    add_dimensions(dimensions):
        Add new dimensions to the MRIO table.
    add_labels(new_indices, dimension, fill_value=0.0):
        Add items to a label of the MRIO instance.
    replace_labels(name, new_labels):
        Replace labels for one or more dimensions in all MRIO parts.
    rename_dimensions(old_names, new_names):
        Rename the names of the dimensions in the MRIO table.
    aggregate(on="sectors"):
        Aggregate the MRIO table on a given dimension.
    has_neg(parts=None):
        Check whether some parts of the MRIO table have negative values.
    copy():
        Create a copy of the MRIO object.
    save(file, name=None, extension="npy", overwrite=False, **kwargs):
        Save the current MRIO instance to a file or folder.
    to_xarray():
        Convert the MRIO instance to an xarray Dataset.

    Notes
    -----
    This class provides a comprehensive interface for working with MRIO tables,
    including loading, modifying, and saving data, as well as performing 
    operations like filtering and aggregation.
    """
    
    def __init__(self,**kwargs):
        """
        Initialize an MRIO instance.

        There are multiple ways to initialize an MRIO instance:
            - From a `.nc` file: Provide the "file" parameter with the path to the file.
            - From explicit parameters: Provide the data, labels, and metadata explicitly.
            - From a `.yaml` file: Provide the "file" parameter with the path to a `.yaml` file 
              containing loading instructions.

        If no arguments are provided, an empty MRIO instance is created.

        Parameters
        ----------
        file : str, optional
            Path to the file to load the MRIO table from. If a `.yaml` file is provided, 
            it is interpreted as loading instructions.
        data : dict, xarray.DataArray, xarray.Dataset, or pandas.DataFrame, optional
            Data to initialize the MRIO instance. If provided, the instance is created 
            from this data.
        kwargs : dict
            Additional parameters for initializing the MRIO instance.

        Raises
        ------
        ValueError
            If the provided data type is not supported for initializing the MRIO instance.
            
        Notes
        -----
        The "data" parameter is reserved for setting an MRIO instance from a dictionary.
        It is intended for internal use only.
        """
        
        if not kwargs:
            #Create an empty MRIO instance
            kwargs = {
                "data" : dict()
            }
        if "data" in kwargs:
            data = kwargs.pop("data")
            if isinstance(data,dict):
                log.info("Create MRIO from dict")
                self.parts,self.labels,self.metadata,self.groupings = dict(),dict(),dict(),dict()
                self.__dict__.update(data)
                
                for part in self.parts:
                    self._update_labels(
                        self.parts[part],
                        update_part=False
                        )
                self.metadata.update(kwargs)
                self.loader = make_loader()
                return
            if isinstance(data,(xr.DataArray,xr.Dataset)):
                if isinstance(data,xr.DataArray):
                    data = data.to_dataset()
                mrio_data,to_load = converters.xarray.make_mrio(data,**kwargs)
                self.__init__(data=mrio_data)
                for part in to_load:
                    self.add_part(data[part])
                return
            if isinstance(data,pd.DataFrame):
                self.__init__(data=kwargs)
                self.add_part(data)
                return
            raise ValueError(f"Cannot create an MRIO instance from type: {type(data)}")
            
        
        file = kwargs.pop("file",None)
        #Initialize the loader
        self.loader = make_loader(file=file,**kwargs)

        #Load basic MRIO data
        self.metadata = self.loader.metadata
        self.labels = self.loader.labels
        self.groupings = self.loader.groupings

        #Initialize the parts
        self.parts = dict()
        available_parts = self.loader.available_parts(
                extension = kwargs.get("extension",None)
            )
        
        to_load = {part:part for part in available_parts}
        if "part_settings" in self.loader.__dict__ and bool(self.loader.part_settings):
            to_load = dict()
            for part in self.loader.part_settings.keys():
                to_load[part] = self.loader.part_settings[part].get("file_name",part)

        for part in to_load.keys():
            if to_load[part] not in available_parts:
                log.warning(f"Part {part} not found in available parts")
                continue
            kwargs["name"] = part
            kwargs["file_name"] = to_load[part]
            self.load_part(**kwargs)
        
        if "countries" in self.labels:
            self.c = len(self.labels["countries"])
        if "sectors" in self.labels:
            self.s = len(self.labels["sectors"])

    def load_part(self,
                  update_part = True,
                  standalone=False,
                  **kwargs):
        """
        Load a Part object into the MRIO table

        By default, the Part is loaded using the current loader.

        Parameters
        ----------
        update_part : bool, optional
            The groupings and labels of the Part are updated based on the MRIO attributes.
        standalone : bool, optional
            Whether to load the Part as a standalone object.
            The default is False.
        kwargs : dict
            Additional arguments to pass to the Part loader.
        """
        name = kwargs.get("name","new_part")
        try:
            log.debug(f"Try loading part {name} from the current loader")
            part = self.loader.load_part(**kwargs)
        except FileNotFoundError:
            log.info(f"Part {name} not found with the current loader")
            log.debug(f"Try resetting the loader")
            loader = make_loader(**kwargs)
            part = loader.load_part()
        part = Part(**part)
        if standalone:
            return part
        log.info(f"Add part {part.name} to MRIO table")
        self.add_part(part,update_part=update_part)
        
    def _update_labels(self,part,update_part=True):
        """
        Update the labels of the MRIO table with the labels of a Part object

        If all the labels of the Part are already in the MRIO labels,
        the method does nothing.
        This method is run after adding a new Part to the MRIO table.

        Parameters
        ----------
        part : Part object
            Part object to use for the update.
        update_part : bool, optional
            If True and the Part labels are not properly set,
            tries to update the Part labels based on the MRIO labels.
        """
        part_labels = part.get_labels()
        log.debug(f"Update labels of MRIO table with {part.name}")  
        for labels in part_labels:
            for label in labels.keys():
                if isinstance(label,int):
                    log.debug(f"Skip numerical label in {part.name}")
                    if update_part:
                        log.debug(f"Try to update labels of {part.name}")
                        labels[label] = self._get_labels(
                            len(labels[label])
                            )
                    continue #Skip unkwnown labels
                if label not in self.labels.keys():
                    self.labels[label] = labels[label]
                    log.info(f"Add label {label} to MRIO table")
        if update_part:
            part.set_labels(part_labels)

    def _get_labels(self,l):
        """
        Find the labels fitting an axis with a given shape
        
        Available labels:
        
            - countries and sectors
            - countries
            - zones and sectors
            - zones
            - sectors
            
        If no fitting label is found, data are labelled numerically

        Parameters
        ----------
        l : int
            Length of the data dimension.

        Returns
        -------
        dict of str:list of str
            Labels of the axis.

        """
        if l==1:
            return (["all"])
        log.debug("Try to infer label from axis of length "+str(l))
        for label in self.labels:
            #Look whether a basic label fits the axis
            if l == len(self.labels[label]):
                log.debug(f"Label {label} fits axis of length {l}")
                return {label:self.labels[label]}
        for grouping in self.groupings:
            #Look whether a grouped label fits the axis
            if l == len(self.groupings[grouping]):
                log.debug(f"Label {label} fits axis of length {l}")
                return {grouping:list(self.groupings[grouping]).keys()}
        log.warning("No label found for axis of length "+str(l))
        return {0:[i for i in range(l)]}

    
    def set_groupings(self,groupings=None):
        """Set the groupings of the MRIO table
        
        Groupings are used to group labels into larger categories 
        (e.g countries into zones, sectors in aggregate sectors).
        Groupings have in principle no impact on the resolution of the table
        but can be used for visualization or aggregation purposes.

        Groupings should be disjoint, but this is not enforced.
        Nested groupings are not supported.

        Unspecified groupings are set to the identity.
        Calling the method without arguments resets the groupings to the identity.

        Parameters
        ----------
        groupings : dict of dict, optional
            Groupings of the MRIO table.
            The default is None.
            If None, the groupings are set to the identity.
            Groupings should be provided as a dict of dict::
            
                {dimension : {group : [items]}}
                
            where dimension is the name of the label to group,
            group is the name of the group,
            and items is a list of items to group.
        """
        if groupings is None:
            groupings = {label:dict() for label in self.labels.keys()}
            self.set_groupings(groupings)
        for key in groupings.keys():
            labels = self.labels[key]
            covered = []
            for group in list(groupings[key]):
                for item in list(groupings[key][group]):
                    if item not in labels:
                        log.warning(
                            f"Item {item} not found in {key} labels"
                            )
                        groupings[key][group].remove(item)
                    else:
                        covered.append(item)
                if len(groupings[key][group]) == 0:
                    log.warning(f"Group {group} is empty")
                    groupings[key].pop(group)
            for item in labels:
                if item not in covered:
                    groupings[key][item] = [item]
            self.groupings[key] = groupings[key]
        self._update_groupings()
        self.loader.set_groupings(self.groupings)
    
    def _update_groupings(self):
        """
        Update the groupings of all Parts of the MRIO instance
        """
        for part in self.parts.keys():
            self.parts[part].update_groupings(self.groupings)
        self.groups = {
            groups : list(self.groupings[groups].keys()) for groups in self.groupings
            } #Save name of groups for each dimension
    
    def filter(self,threshold,fill_value=0):
        """
        Filter the MRIO table by removing values below a threshold
        
        Parameters
        ----------
        threshold : float
            Value below which the values are set to 0.
        fill_value : float, optional
            Value to use to fill the table if only dimensions are given.
        
        Returns
        -------
        None.
        """
        for part in self.parts.keys():
            self.parts[part] = self.parts[part].filter(threshold,fill_value)
    
    def add_part(self,
                 part,
                 name=None,
                 update_part=True):
        """
        Add a Part object to the MRIO table
        
        Parameters
        ----------
        part : Part object
            Part object to add to the MRIO table.
        update_part : bool, optional
            Whether to update the labels of the Part object.
            The default is True.
        """
        if not isinstance(part,Part):
            #Cast the data into a Part object
            part=Part(part)
        if name is None:
            name = part.name
        log.info(f"Add part {name} to MRIO table")
        self._update_labels(part,update_part)
        if update_part:
            part.update_groupings(self.groupings)
            for metadata in self.metadata:
                if metadata not in part.metadata:
                    part.metadata[metadata] = self.metadata[metadata]
        self.parts[name] = part
                
    def new_part(self,
                 data=None,
                 name="part",
                 dimensions=None,
                 fill_value=0.0,
                 **kwargs):
        """Cast part data into the corresponding Part Object
        
        Parameters
        ----------
        data : np.ndarray, optional
            Data to load in the Part. The default is None.
            If None, the dimensions argument is used to create an empty Part.
        name : str, optional
            Name of the Part. The default is "part".
        dimensions or labels : list of str, list of ints, str, list of dicts, optional
            Labels of the Part. 
            Either of these formats are accepted:
            
                - Dictionary of explicit labels for each axis
                - List of explicit labels for each axis
                - List of existing dimension names
                
            If None, the labels are inferred from the data shape.
        multiplier : str, optional
            multiplier of the data. The default is None.
        unit : float, optional
            Unit of the data. The default is 1.
        fill_value : float, optional
            Value to use to fill the table if only dimensions are given.

        Returns
        -------
        Part instance
        """
        def unpack_dimensions(self,dimensions):
            """Unpack the dimensions argument"""
            if isinstance(dimensions,dict):
                return dimensions
            if isinstance(dimensions,str):
                #Try to get the dimensions from the current labels or groupings
                if dimensions in self.labels.keys():
                    return {dimensions:self.labels[dimensions]}
                if dimensions in self.groupings.keys():
                    return {dimensions:list(self.groupings[dimensions])}
                log.warning(f"Dimension {dimensions} not found in labels or groupings\n"+\
                            " Available dimensions are "+str(self.labels.keys()))
                raise ValueError(f"Invalid dimension {dimensions}")
            if isinstance(dimensions,int):
                #Try to infer the dimension from the length of the data
                return self._get_labels(dimensions)
            if isinstance(dimensions,(list,tuple)):
                try:
                    #Try to unpack nested dimensions
                    output = dict()
                    for dim in dimensions:
                        output.update(unpack_dimensions(self,dim))
                    return output
                except ValueError:
                    #Otherwise assume the labels were given as a list
                    return {0:dimensions}
            raise TypeError(f"Invalid type for dimensions {type(dimensions)}")
        
        dimensions = kwargs.get("dimensions",dimensions)
        if dimensions is None:
            dimensions = kwargs.get("labels",None)
        if data is None:
            #Create a Part from the dimensions only
            if dimensions is None:
                raise ValueError("No data nor dimensions provided")
            
            if isinstance(dimensions,(int,str)):
                #Ensure dimensions are iterable
                dimensions = [dimensions]
            labels = []
            for dim in dimensions:
                labels.append(unpack_dimensions(self,dim))
            dims = len(labels)
            shape = []
            for dim in range(dims):
                #Recursively compute the shape of the table
                length = 1
                for label in labels[dim]:
                    length *= len(labels[dim][label])
                shape.append(length)
            data = np.full(shape,fill_value=fill_value)

        elif dimensions is None:
            #Infer the dimensions from the data shape
            labels = []
            for dimension in range(data.ndim):
                labels.append(
                    self._get_labels(data.shape[dimension])
                    )

        else:
            #Reformat the dimensions
            labels = []
            if isinstance(dimensions,(int,str)):
                #Ensure dimensions are iterable
                dimensions = [dimensions]
            for dim in dimensions:
                labels.append(unpack_dimensions(self,dim))

        return Part(data=data,
                    name=name,
                    groupings = self.groupings,
                    labels = labels,
                    **kwargs)

    def add_dimensions(self,dimensions):
        """
        Add dimensions to the MRIO table

        Parameters
        ----------
        dimensions : dict
            Description of the dimension to add.
        """
        for dimension in dimensions.keys():
            log.info("Add dimension "+dimension+" to MRIO table")
            # check whether the dimension is already in the labels
            if dimension in self.labels.keys():
                log.info(f"Dimension {dimension} already exists in MRIO labels")
                if dimensions[dimension] != self.labels[dimension]:
                    log.warning(f"There already exist different or differently ordered labels for dimension '{dimension}' in the MRIO labels. "+ 
                                "You are now overwriting them which leads to inconsistent labels in the parts of your MRIO table!")
            
            if isinstance(dimensions[dimension],str):
                #For single item dimensions, convert to list
                dimensions[dimension] = [dimensions[dimension]]
            self.labels[dimension] = dimensions[dimension]

    def check_label_consistency(self):
        """
        Check whether the labels of of all parts of the MRIO table are consistent.
        """
        
        for part in self.parts.keys():
            for key, labels in self.parts[part].labels.items():
                if key in self.labels.keys():
                    if labels != self.labels[key]: 
                        log.warning(f"Labels for dimension'{key}' in part '{part}' are inconsistent with MRIO labels")
                        return False
                else: 
                    log.warning(f"Label {key} not found in MRIO labels")
                    return False
        return True
    
    def add_labels(self,new_indices,dimension,
                   fill_value=0.0):
        """
        Add items to a label of the MRIO instance

        All Parts are updated automatically with the given fill_value

        Parameters
        ----------
        new_indices : list of str
            items to add to the label
        dimension : str
            name of the labels to which the new indices should be added
        fill_value : float, optional
            Value to use to fill the newly created label fields in the tables.
        """
        log.info(f"Add labels {str(new_indices)} to dimension "+dimension)
        for part in self.parts.keys():
            self.parts[part] = self.parts[part].add_labels(
                new_indices,dimension=dimension,
                fill_value=fill_value
            )
        self.labels[dimension] += new_indices
        if dimension == "countries":
            self.c = len(self.labels[dimension])
        if dimension == "sectors":
            self.s = len(self.labels[dimension])
        if "x" in self.parts.keys():
            x = self.x.data
            x[x==0] = 1
        self.loader.set_labels(self.labels)

    def replace_labels(self,name,new_labels):
        """
        Replace labels for one or more dimensions in all MRIO parts. 

        Parameters
        ----------
        name : str or list of str
            Name of the dimension for which the labels should be replaced 
        new_labels : list of str or dict of list of str
            New labels for given dimension in the labels dictionary.
        """
        log.info(f"Replace labels for {name}")
        if isinstance(name,str):
            self._replace_individual_labels(name = name, new_labels = new_labels)
        elif isinstance(name,list):
            for dimension in name:
                if isinstance(new_labels,list):
                    raise ValueError("You provided multiple dimensions but only one set of new labels.")
                elif isinstance(new_labels,dict):
                    new_labels = new_labels[dimension]
                else: 
                    raise TypeError(f"Invalid type for new labels: {type(new_labels)}")
                self._replace_individual_labels(dimension,new_labels)
         
    def _replace_individual_labels(self,name, new_labels): # check for usages and update them
        """
        Replace labels for one dimension in all MRIO parts. 

        Parameters
        ----------
        name : str
            Name of the labels to replace. Usually this is 'countries', 'sectors', 'va_labs' or 'y_labs'
        new_labels : list of str
            New labels for given name in the label dictionary.
        """
        log.info(f"Replace labels for {name}")
        if name not in self.labels.keys():
            log.warning(f"Label {name} is not in MRIO labels and cannot be replaced.")
            return
        for part in self.parts.keys():
            self.parts[part].replace_labels(name, new_labels)
        self.loader.set_labels(self.labels)
        self.labels[name] = new_labels
        
        if name in self.groupings.keys():
            log.warning("Groupings for all dimensions are reset to identity, because the labels have changed.\n \
                        Please update the groupings manually if needed.")
            self.set_groupings(groupings=None)

    def rename_dimensions(self,old_names,new_names):
        """
        Rename the names of the dimensions.
        
        The keys of the label dicts for the MRIO instance are renamed.
        The content of the labels and the groupings is conserved. 

        Parameters
        ----------
        old_names : str or list of str
            Labels to rename.
        new_names : str or list of str
            New names for the labels.
        """
        if isinstance(old_names,str):
            old_names = [old_names]
        if isinstance(new_names,str):
            new_names = [new_names]
        for old,new in zip(old_names,new_names):
            log.info(f"Rename label {old} to {new}")
            
            if old in self.labels.keys():
                self.labels = {new if key == old else key : value for key, value in self.labels.items()}
            else:
                log.warning(f"Label {old} is not in MRIO labels and cannot be renamed.")
                continue
            if old in self.groupings.keys():
                self.groupings = {new if key == old else key : value for key, value in self.groupings.items()}
            for part in self.parts.keys():
                self.parts[part].rename_labels(old,new)
                
    def reorder_data(self, new_labels):
        """
        Reorder the data of the MRIO instance based on new labels.

        This method is used to reorder the data of the MRIO instance based on the new labels.
        The new labels should be a dictionary with the same keys and items as the old mrio labels
        but the keys and items can be in a different order. The data of the part is then reordered
        to fit the new labels.

        Parameters
        ----------
        new_labels : dict
            New labels to use for reordering.
        """
        log.info("Reorder MRIO data with new labels")
        old_labels = self.labels
        if not isinstance(new_labels,dict):
            raise TypeError(f"Invalid type for new labels: {type(new_labels)}. Expected a dict.")
        if not set(new_labels.keys()).issubset(set(old_labels.keys())):
            raise ValueError("You are trying to reorder data for dimensions that are not present in your MRIO instance")
        
        for part in self.parts.keys():
            new_part_labels = {}
            for key, labels in new_labels.items():
                if key in self.parts[part].labels.keys():
                    new_part_labels[key] = labels
            self.parts[part].reorder_data(new_part_labels)
                    
        for key in new_labels.keys():
            self.replace_labels(key, new_labels[key])



    def aggregate(self,on="sectors"):
        """Aggregate the MRIO table on a given dimension
        
        The aggregation is performed by summing the values of the table
        for the items that are grouped together.

        Parameters
        ----------
        on : str, optional
            Name of the dimension to aggregate on. 
            The default is "sectors".

        Returns
        -------
        None.

        """
        if on == "all":
            on = list(self.groupings.keys())
        if isinstance(on,list):
            for item in on:
                self.aggregate(item)
            return
        log.info(f"Aggregate MRIO on {on}")
        if on not in self.labels.keys():
            raise ValueError(f"Invalid dimension {on}")
        if on not in self.groupings.keys():
            raise ValueError(f"No groupings defined for dimensions {on}")
        
        new_groupings = {
            item : [item] for item in self.groupings[on]
        }
        new_labels = [item for item in self.groupings[on]]

        for part in self.parts.keys():
            self.parts[part] = self.parts[part].aggregate(on)

        self.groupings[on] = new_groupings
        self.labels[on] = new_labels
        
        if on == "countries":
            self.c = len(self.labels[on])
        if on == "sectors":
            self.s = len(self.labels[on])

        self.loader.set_groupings(self.groupings)
        self.loader.set_labels(self.labels)
    
    def __getattr__(self,name):
        selset = [
            self.parts,
            self.labels,
            self.metadata
            ]
        for sel in selset:
            try:
                return sel[name]
            except:
                pass
        raise AttributeError(f"Attribute {name} not found")
    
    def __setattr__(self,name,value):
        if isinstance(value,Part):
            self.add_part(value,name=name)
        elif isinstance(value,np.ndarray):
            self.add_part(self.new_part(value,name))
        else:
            super().__setattr__(name,value)
    
    def __str__(self):
        s = ["MRIO object: "+ ' '.join(self.metadata.values())]
        s.append("")
        s.append("Parts currently loaded:")
        s.append("   " + ", ".join(self.parts.keys()))
        return "\n".join(s)
    
    def has_neg(self,parts=None):
        """Check whether some Parts have negative values

        Parameters
        ----------
        parts : str, list of str or None, optional
            List of parts to inspect. 
            If left empty, all parts are inspected.

        Returns
        -------
        bool
        """
        if isinstance(parts,str):
            parts = [parts]
        elif parts is None:
            parts = self.parts.keys()
        for part in parts:
            if self.parts[part].hasneg():
                return True
        return False
    
    def copy(self):
        """Create a copy of the MRIO object"""
        return MRIO(data=self.__dict__)
    
    def save(self,
             file=None,
             name=None,
             extension = ".nc",
             overwrite=False,
             **kwargs):
        """
        Save the current MRIO instance

        If the path points to a folder, the MRIO parts can be saved as:
            - .npy
            - .csv
            - .txt
            - .xlsx
            
        Labels are saved as .txt files and metadata as a .yaml file.

        Otherwise the MRIO instance is saved as a .nc file.

        Parameters
        ----------
        file : str
            Full path to the file or folder to save the MRIO instance into.
            If a file is provided, the extension is used to determine the format.
        extension : str, optional
            Extension of the file to save the MRIO instance into.
            This is only used if the file is a folder.
        overwrite : bool, optional
            Whether to overwrite the existing file. The default is False.
            If False, the version name is iterated until a non-existing
            file name is found.
        kwargs : dict
            Additional arguments to pass to the saver.
        """
        if file is None:
            if file is None:
                name = self.metadata.get("name","mrio")
            file = name
        file_extension = os.path.splitext(file)[1]
        if file_extension == "" and extension == ".nc":
            file = os.path.join(file+".nc")
            file_extension = ".nc"
        if file_extension == "":
            #If the file is a folder, save in folder
            save_mrio_to_folder(
                self,
                file,
                name=name,
                extension=extension,
                overwrite=overwrite,
                **kwargs
                )
        elif file_extension == ".nc":
            #If the file is a .nc, save the tables
            save_to_nc(self,file,overwrite,**kwargs)
        else:
            raise NotImplementedError(f"Cannot save MRIO in {file_extension} format")
    
    def to_xarray(self):
        """
        Convert the MRIO instance to an xarray Dataset
        """
        return converters.xarray.to_DataSet(self)
    
    def reallocate_negatives(self,**kwargs):
        formatter.reallocate_negatives(self,**kwargs)

    def adjust_intermediates(self,**kwargs):
        formatter.adjust_intermediates(self,**kwargs)

    def fill_empty_rows(self,**kwargs):
        formatter.fill_empty_rows(self,**kwargs)

    def balance_va(self,**kwargs):
        formatter.balance_va(self,**kwargs)

    def compute_technical_coefficients(self,**kwargs):
        formatter.compute_technical_coefficients(self,**kwargs)

    def compute_leontief(self,**kwargs):
        formatter.compute_leontief(self,**kwargs)

    def preprocess(self,**kwargs):
        formatter.preprocess(self,**kwargs)

    def rename_part(self,old_name,new_name):
        formatter.rename_part(self,old_name,new_name)

    def rename_parts(self,renaming_dict):
        formatter.rename_parts(self,renaming_dict)