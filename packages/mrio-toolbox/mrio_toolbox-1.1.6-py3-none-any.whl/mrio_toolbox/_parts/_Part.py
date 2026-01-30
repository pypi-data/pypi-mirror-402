# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 14:13:17 2023

@author: beaufils
"""

import os
import itertools
import numpy as np
import pandas as pd
import xarray as xr
import copy
from mrio_toolbox._parts._Axe import Axe
import logging
from mrio_toolbox.utils import converters
from mrio_toolbox.utils.loaders import make_loader
from mrio_toolbox.utils.savers import save_part_to_folder,save_to_nc
from mrio_toolbox._parts import part_operations

log = logging.getLogger(__name__)

def load_part(
        **kwargs
        ):
    loader = make_loader(**kwargs)
    return Part(**loader.load_part(**kwargs))

class Part:
    """
    Representation of an MRIO Part object.

    MRIO Parts are the basic building blocks of the MRIO toolbox. A Part is 
    built from a numpy array and a set of Axes, corresponding to the dimensions 
    of the array. The Axes hold the labels of the Part in the different 
    dimensions and are used to perform advanced indexing and operations on the Part.

    Axes support multi-level indexing and groupings.

    Instance variables
    ------------------
    data : numpy.ndarray
        Numerical data of the Part.
    axes : list of Axe instances
        Axes corresponding to the dimensions of the Part.
    groupings : dict
        Groupings of the labels of the Part, for each label defined.
    metadata : dict
        Additional metadata of the Part (e.g., path, name, multiplier, unit).
    name : str
        Name of the Part.
    ndim : int
        Number of dimensions of the Part.
    shape : tuple
        Shape of the Part.

    Methods
    -------
    __init__(data=None, labels=None, axes=None, **kwargs):
        Initialize a Part object.
    alias(**kwargs):
        Create a new Part with modified parameters.
    fix_dims(skip_labels=False, skip_data=False):
        Align the number of axes with the number of dimensions.
    get(*args, aspart=True, squeeze=False):
        Extract data from the Part object.
    setter(value, *args):
        Change the value of a data selection.
    develop(axis=None, on=None, squeeze=True):
        Reshape a Part to avoid double labels.
    reformat(new_dimensions):
        Reshape a Part to match a new dimensions combination.
    combine_axes(start=0, end=None, in_place=False):
        Combine axes of a Part into a single one.
    swap_axes(axis1, axis2):
        Swap two axes of a Part.
    swap_ax_levels(axis, dim1, dim2):
        Swap two levels of an axis.
    flatten(invert=False):
        Flatten a 2D Part into a 1D Part.
    squeeze():
        Remove dimensions of length 1 from the Part.
    expand_dims(axis, copy=None):
        Add dimensions to a Part instance.
    copy():
        Return a copy of the current Part object.
    extraction(dimensions, labels=["all"], on_groupings=True, domestic_only=False, axis="all"):
        Set labels over dimension(s) to 0.
    leontief_inversion():
        Compute the Leontief inverse of a square Part.
    update_groupings(groupings, ax=None):
        Update the groupings of the current Part object.
    aggregate(on="countries", axis=None):
        Aggregate dimensions along one or several axes.
    aggregate_on(on, axis):
        Aggregate a Part along a given axis.
    get_labels(axis=None):
        Returns a list with the labels of the axes as dictionaries.
    list_labels():
        List the labels of the Part.
    get_dimensions(axis=None):
        Return the list of dimensions of the Part.
    rename_labels(old, new):
        Rename some labels of the Part.
    replace_labels(name, labels, axis=None):
        Update a label of the Part.
    set_labels(labels, axis=None):
        Change the labels of the Part.
    add_labels(labels, dimension=None, axes=None, fill_value=0):
        Add indices to one or multiple Part axes.
    expand(axis=None, over="countries"):
        Expand an axis of the Part.
    issquare():
        Check whether the Part is square.
    hasneg():
        Check whether the Part has negative elements.
    hasax(name=None):
        Return the dimensions along which a Part has given labels.
    sum(axis=None, on=None, keepdims=False):
        Sum the Part along one or several axes or on a given dimension.
    save(file=None, name=None, extension=".npy", overwrite=False, include_labels=False, write_instructions=False, **kwargs):
        Save the Part object to a file.
    to_pandas():
        Return the current Part object as a Pandas DataFrame.
    to_xarray():
        Save the Part object to an xarray DataArray.
    mean(axis=None):
        Compute the mean of the Part along a given axis.
    min(axis=None):
        Compute the minimum value of the Part along a given axis.
    max(axis=None):
        Compute the maximum value of the Part along a given axis.
    mul(a, propagate_labels=True):
        Perform matrix multiplication between Parts with label propagation.
    filter(threshold, fill_value=0):
        Set to 0 the values below a given threshold.
    diag():
        Create a diagonal Part from a 1D Part or extract the diagonal of a 2D Part.
    transpose():
        Transpose the Part object.
    """
    
    def __init__(self,data=None,
                 labels=None,
                 axes=None,
                 **kwargs):
        """
        Initialize a Part object.

        Parameters
        ----------
        data : numpy.ndarray, optional
            Numerical data of the Part. If not provided, a Part filled with 
            zeros (or another fill value) is created based on the shape of the axes.
        labels : list of str or dict, optional
            Labels for the axes. If provided, the labels define the structure 
            of the axes. If not provided, axes are created based on the data.
        axes : list of Axe instances, optional
            Custom Axes for the Part. If not provided, axes are created from 
            the labels or inferred from the data.
        kwargs : dict
            Additional metadata for the Part (e.g., path, name, multiplier, unit).

        Raises
        ------
        ValueError
            If the length of the labels does not match the data dimensions.
        TypeError
            If the provided labels are of an unsupported type.

        Notes
        -----
        If both `data` and `axes` are not provided, the method creates an 
        empty Part with default axes and zero-filled data.
        """
        
        if data is not None:
            if isinstance(data,Part):
                data = data.data
            if isinstance(data,(xr.DataArray,xr.Dataset)):
                self.__init__(
                    **converters.xarray.make_part(data)
                    )
                return
            if isinstance(data,pd.DataFrame):
                self.__init__(**converters.pandas.make_part(
                    data)
                    )
                return
            self.data = data
            self.ndim = data.ndim
            self.shape = self.data.shape

        self.name = kwargs.pop("name","new_part")
        log.debug("Create Part instance " + self.name)
        
        self.groupings = kwargs.get("groupings",dict())
        self.metadata = kwargs.get("metadata",dict())
        self.metadata = {**self.metadata,**kwargs}

        if axes is None:
            self.axes = []
            self._create_axis(labels)
        else:
            self.axes = axes

        if data is None:
            log.debug("Create empty Part")
            data = np.zeros([len(ax) for ax in self.axes])
            self.data = data
            self.ndim = data.ndim
            self.shape = self.data.shape

        self.fix_dims()
        for dim in range(self.ndim):
            if len(self.axes[dim]) != self.shape[dim] and self.shape[dim] != 1:
                log.critical(f"Length of label {dim} does not match data: "+\
                                f"{len(self.axes[dim])} and {self.shape[dim]}")
                raise ValueError(f"Length of label {dim} does not match data: "+\
                                 f"{len(self.axes[dim])} and {self.shape[dim]}")

        if "_original_dimensions" in self.metadata.keys():
            #This set of instructions is intended to handle
            #Data loaded from netcdf files
            log.info("Checking if a reformatting is needed.")
            original = self.metadata.pop("_original_dimensions")
            new_dims = [[]]
            for dim in original:
                #Decode the original dimensions
                #Because netcdf files do not support multi-level attributes
                if dim == "_sep_":
                    new_dims.append([])
                else:
                    new_dims[-1].append(dim)

            if new_dims != self.get_dimensions():
                
                log.info("Reformat the Part")
                new_part = self.reformat(new_dims)
                self.data = new_part.data
                self.axes = new_part.axes
                self.ndim = self.data.ndim
                self.shape = self.data.shape
        
        self._store_labels()

    
    def alias(self,**kwargs):
        """Create a new Part in which only prescribed parameters are changed
        
        The current Part is taken as reference: all arguments not explicitely
        set are copied from the current part."""
        data = kwargs.get("data",self.data).copy()
        name = kwargs.get("name",self.name+"_alias")
        groupings = kwargs.get("groupings",self.groupings)
        axes = kwargs.get("axes",self.axes)
        labels = kwargs.get("labels",None)
        metadata = kwargs.get("metadata",self.metadata)
        return Part(
            data=data,
            name=name,
            groupings = groupings,
            labels=labels,
            axes=axes,
            metadata = metadata)
        
    def _create_axis(self,labels):
        """
        Create an Axe object based on a tuple of lists of indices

        Parameters
        ----------
        *args : tuple of lists of str, list of str
            Labels of the axe.
            The first argument is used as the main label.
            The second argument (if any) is used as secondary label.
            If left empty, the axe is labelled by indices only

        Raises
        ------
        TypeError
            Raised if the arguments types differs from the number of dimensions
            or if input labels are incorrect.
        ValueError
            Raised if the label length does not match the data.

        Returns
        -------
        None.

        """
        self.axes = []
        
        if isinstance(labels,(tuple,list)) and len(labels)>0 and\
            isinstance(labels[0],(str,int,float)):
            #If the first item of the labels is not iterable,
            #we assume the label is an axis label
            labels = [labels]
            #We add a dimension to the labels such that enumeration works properly

        if "data" in self.__dict__.keys():
            enum = self.ndim
        else:
            if labels is None:
                raise ValueError("Cannot create axes without data, axes or labels")
            enum = len(labels)
            
        for dim in range(enum):
            if labels is None or dim > len(labels):
                #Fill empty labels with indices
                self.axes.append(
                    Axe([i for i in range(self.shape[dim])],
                        groupings = self.groupings)
                )
            elif isinstance(labels,dict):
                axname = list(labels.keys())[dim]
                self.axes.append(
                    Axe(labels[axname],groupings=self.groupings,name=axname)
                )
            elif isinstance(labels,(list,tuple)):
                self.axes.append(
                    Axe(labels[dim],groupings=self.groupings)
                )
            else:
                log.critical("Unkown label type: "+type(labels))
                raise TypeError("Unknown label type: "+type(labels))
            log.debug(f"Create ax {dim} with len {self.axes[-1]}")
        
    def fix_dims(self,
                 skip_labels=False,
                 skip_data=False):
        """Align the number of axes with the number of dimensions
        
        If one length exceeds the other, axes and/or data are squeezed,
        i.e. dimensions of length 1 are removed."""
        if len(self.axes) == self.ndim:
            return
        log.warning(
            f"The number of axes ({len(self.axes)})"\
                    +f" does not match data dimensions ({self.ndim})"
            )

        if len(self.axes) > self.ndim and not skip_labels:
            log.debug(
                "Try to squeeze axe(s) of len 1"
            )
            counter = [len(ax) != 1 for ax in self.axes]
            self.axes = self.axes[counter]
            return self.fix_dims(
                    skip_labels=True,
                    skip_data=skip_data)
        if self.ndim > len(self.axes) and not skip_data:
            self.data = self.data.squeeze()
            self.shape = self.data.shape
            self.ndim = self.data.ndim
            return self.fix_dims(
                skip_labels=skip_labels,
                skip_data=True)
        
        log.critical("Cannot reconcile data of dims "+ self.ndim+\
                            " with axes of dim " +len(self.axes))
        raise IndexError("Cannot reconcile data of dims "+ self.ndim+\
                        " with axes of dim " +len(self.axes))
        

    def __getitem__(self,args):
        if isinstance(args,str) or isinstance(args,int) or isinstance(args,np.integer) or isinstance(args,dict):
            args = (args,)
        return self.get(*args)
    
    def __setitem__(self,args,value):
        if isinstance(value,Part):
            value = value.data
        if isinstance(args,str) or isinstance(args,int) or isinstance(args,np.integer) or isinstance(args,dict):
            args = (args,)
        self.setter(value,*args)
    
    def setter(self,value,*args):
        """
        Change the value of a data selection

        Parameters
        ----------
        value : float or numpy like
            Value to set.
        *args : list of tuples
            Indices along the respective axes.

        Returns
        -------
        None.
        Modification is applied to the current Part object

        """
        sels = []
        try:
            #First tries to interpret one arg per ax
            for i,arg in enumerate(args):
                sels.append(self.axes[i].get(arg))
        except (IndexError,ValueError):
            #Otherwise, tries to interpret all args on the first ax
            sels = []
            sels = [self.axes[0].get(args)]
        if isinstance(value,(np.ndarray,Part)) and len(sels)!=value.ndim:
            if len(sels) < value.ndim:
                value = value.squeeze() 
            if len(sels) > value.ndim:
                target_shape = [len(sel) for sel in sels]
                value = np.reshape(value,target_shape)   
        self.data[np.ix_(*sels)] = value
    
    def get(self,*args,aspart=True,squeeze=False):
        """
        Extract data from the current Part object

        Parameters
        ----------
        *args : list of tuples
            Selection along the Axes of the Part.
        aspart : bool, optional
            Whether to return the selection as a Part object. 
            If False, the selection is returned as a numpy object.
            The default is True.
        squeeze : bool, optional
            Whether to remove dimensions of length 1.
            The default is False

        Returns
        -------
        New Part object or numpy object
        """
        sels = []
        axes = []

        #Extract the indices for the selection
        try:
            #First tries to interpret one arg per ax
            for i,arg in enumerate(args):
                datasel,labs,groupings = self.axes[i].get(arg,True)
                if not squeeze or len(datasel) > 1:
                    axes.append(Axe(labs,groupings))
                sels.append(datasel)  
        except (ValueError, IndexError):
            sels = []
            axes = []
            #Try interpreting all args on the first ax
            datasel,labs,groupings = self.axes[0].get(args,True)
            if not squeeze or len(datasel) > 1:
                axes.append(Axe(labs,groupings))
            sels.append(datasel)

        #If the selection is not complete, fill with all
        if len(sels)<self.ndim:
            for i in range(len(sels),self.ndim):
                datasel,labs,groupings = self.axes[i].get("all",True)
                if not squeeze or len(datasel) > 1:
                    axes.append(Axe(labs,groupings))
                sels.append(datasel)

        #Execute the selection
        data = self.data[np.ix_(*sels)]

        #Return the selection
        if squeeze:
            data = data.squeeze()
        if aspart:
            return Part(data=data,name=f"sel_{self.name}",
                        groupings=self.groupings,axes = axes)
        return data
        
    def develop(self,axis=None,on=None,squeeze=True):
        """
        Reshape a Part to avoid double labels

        Parameters
        ----------
        axis : int or list of int, optional
            Axis to develop. 
            If left empty, all axes are developed.
            The default is None.
        on : str or list of str, optional
            Dimensions to develop.
            If left empty, all dimensions are developed.
            Note that the develop method does not support the developping of
            non-contiguous dimensions.
            The default is None.
        squeeze : bool, optional
            Whether to remove dimensions of length 1.
            The default is True.
            
        Returns
        -------
        Developped Part :  Part object
            The developed part
        """
        if isinstance(on,str):
            on = [on]
        if isinstance(axis,int):
            axis = [axis]
        axes = []
        for i,ax in enumerate(self.axes):
            if axis is None or i in axis:
                labels = ax.labels.copy()
                for dim in ax.dimensions:
                    if on is None or dim in on:
                        #Add dimension that needs to be developed
                        axes.append(Axe({dim:labels[dim]},groupings=ax.groupings))
                        labels.pop(dim)
                if len(labels) > 0:
                    #Keep remaining dimensions together
                    axes.append(Axe(labels,groupings=ax.groupings))
            else:
                axes.append(ax)

        
        old_dim_order = [dim for ax in self.axes for dim in ax.dimensions]
        new_dim_order = [dim for ax in axes for dim in ax.dimensions]
        if new_dim_order != old_dim_order:
            raise NotImplementedError(
                "Developping the part misaligns the dimensions. "+\
                    "This operation is not yet supported."
                )
        #If the order of the dimensions is unchanged, we can simply reshape

        shape = [len(ax) for ax in axes]
        data = self.data.reshape(shape)
        if squeeze:
            return Part(data=data,
                        name=f"developped_{self.name}",
                        groupings=self.groupings,axes=axes).squeeze()
        return Part(data=data,name=f"developped_{self.name}",
                    groupings=self.groupings,axes=axes)

    def reformat(self, new_dimensions):
        """
        Reshape a Part to match a new dimensions combination.

        Equivalent to a combination of the develop and combine_axes methods.

        This only works for contiguous dimensions in the current Part,
        without overlapping dimensions.

        Parameters
        ----------
        new_dimensions : list of list of str
            Target dimensions to reshape into.

        Returns
        -------
        data : numpy.ndarray
            Reshaped data.
        axes : list of Axe
            Reshaped axes.

        Examples
        --------
        If the Part has dimensions::

            [["countries"], ["sectors"], ["sectors"]]

        The following is allowed::

            [["countries", "sectors"], ["sectors"]]

        The following is not allowed::

            [["countries"], ["sectors", "sectors"]]
            [["sectors"], ["countries", "sectors"]]
            [["sectors", "countries"], ["sectors"]]
        """
        return part_operations.reformat(self,new_dimensions)
    
    def combine_axes(self,start=0,end=None,in_place=False):
        """
        Combine axes of a Part into a single one.

        The order of dimensions is preserved in the new axis.
        Only consecutive axes can be combined.
        The method can be used to revert the develop method.

        Parameters
        ----------
        start : int, optional
            Index of the first axis to combine, by default 0
        end : int, optional
            Index of the final axis to combine, by default None,
            all axis are combined, i.e. the Part is flattened.

        Returns
        -------
        Part instance

        Raises
        ------
        IndexError
            Axes should have no overlapping dimensions.
        """
        axes = []
        covered = []
        labels,groupings = dict(),dict()
        if end is None:
            end = self.ndim - 1
        for i,ax in enumerate(self.axes):
            if i in range(start,end+1):
                for name in ax.dimensions:
                    if name in covered:
                        raise IndexError(
                            "Cannot undevelop axes with overlapping dimensions"
                        )
                    covered.append(name)
                    labels[name] = ax.labels[name]
                    if name in ax.groupings.keys():
                        groupings[name] = ax.groupings[name]
            else:
                axes.append(ax)
            if i == end:
                axes.append(Axe(labels,groupings))
        
        new_shape = [len(ax) for ax in axes]
        data = self.data.reshape(new_shape)
        if in_place:
            return data,axes
        return self.alias(data=data,name=f"combined_{self.name}",
                    axes=axes)
    
    def swap_axes(self,axis1,axis2):
        """Swap two axes of a Part
        
        Parameters
        ----------
        axis1 : int
            First axis to swap.
        axis2 : int
            Second axis to swap.

        Returns
        -------
        Part instance
            Part with swapped axes.

        """
        axes = self.axes.copy()
        axes[axis1],axes[axis2] = axes[axis2],axes[axis1]
        data = self.data.swapaxes(axis1,axis2)
        return Part(data=data,name=f"swapped_{self.name}",axes=axes)
    
    def swap_ax_levels(self,axis,dim1,dim2):
        """Swap two levels of an axis
        
        Parameters
        ----------
        axis : int
            Axis to modify.
        dim1 : str
            First dimension to swap.
        dim2 : str
            Second dimension to swap.

        Returns
        -------
        Part instance
            Part with swapped levels.

        """
        len1,len2 = len(self.axes[axis].labels[dim1]),len(self.axes[axis].labels[dim2])
        if len1 == 1 or len2 == 1:
            axes = self.axes.copy()
            axes[axis].swap_levels(dim1,dim2)
            return Part(data=self.data,name=f"swapped_{self.name}",axes=axes)
        dimensions = self.axes[axis].dimensions
        id1,id2 = dimensions.index(dim1),dimensions.index(dim2)
        offset = sum([len(ax.dimensions) for ax in self.axes[:axis]])
        dev = self.develop(axis)
        dev = dev.swap_axes(id1+offset,id2+offset)
        dev = dev.combine_axes(axis,axis+len(dimensions)-1)
        dev.name = f"swapped_{self.name}"
        return dev
    
    def flatten(self):
        """Flatten a multidimensional Part into a 1D Part
        
        Because Parts do not support repeated dimensions over the same axis,
        Axis dimensions are disambiguated if needed by appending an index to the dimension name.

        """
        def disambiguous_dimension(dim,existing,i=1):
            while f"{dim}_{i}" in existing:
                return disambiguous_dimension(dim,existing,i+1)
            
            return f"{dim}_{i}"
        
        enumerator = range(self.ndim)
        order = "C"
        labels = dict()
        groupings = dict()
        for ax in enumerator:
            for dim in self.axes[ax].dimensions:
                dim_name = dim
                if dim in labels.keys():
                    dim_name = disambiguous_dimension(dim,labels)
                    log.info(f"Disambiguate dimension {dim} on axis {ax} into {dim_name}")
                labels[dim_name] = self.axes[ax].labels[dim]
                if dim in self.groupings.keys():
                    groupings[dim_name] = self.axes[ax].groupings[dim]
        ax = Axe(labels,groupings)
        return self.alias(data=self.data.flatten(order=order),
                            name=f"flattened_{self.name}",
                            axes =[ax])
        
        
    def squeeze(self,drop_ax=True,drop_dims=True):
        axes = []
        for ax in self.axes:
            if drop_dims:
                ax.squeeze()
            if len(ax) > 1 or not drop_ax:
                axes.append(ax)
        return self.alias(data=np.squeeze(self.data),axes=axes,
                          name=f"squeezed_{self.name}")
    
    def expand_dims(self,axis,copy=None):
        """Add dimensions to a Part instance
        
        Parameters
        ----------
        axis : int
            Position of the new axis.
        copy : int, optional
            Axis to copy the labels from.
            If left empty, the axis is created without labels.
        """
        axes = self.axes.copy()
        if copy is not None:
            axes.insert(axis,self.axes[copy])
        else:
            axes.insert(axis,Axe({"expanded":[0]}))
        return self.alias(data = np.expand_dims(self.data,axis),
                          axes=axes,name=f"expanded_{self.name}")
    
    def copy(self):
        """Return a copy of the current Part object"""
        return self.alias()
        
    def extraction(self,
                   dimensions,
                   labels=["all"],
                   on_groupings=True,
                   domestic_only=False,
                   axis="all"):
        """
        Set labels over dimension(s) to 0.

        Parameters
        ----------
        dimensions : str, list of str, dict
            Name of the dimensions on which the extraction is done.
            If dict is passed, the keys are interpreted as the dimensions
            and the values as the labels
        labels : list of (list of) str, optional
            Selection on the dimension to put to 0.
        on_groupings : bool, optional
            Whether to use the groupings to select the labels.
            This matters only when the domestic_only argument is set to True.
        domestic_only : bool, optional
            If yes, only domestic transactions are set to 0 and trade flows 
            are left untouched. The default is False.
        axis : list of ints, optional
            Axis along which the extraction is done. The default is "all".
            In any case, the extraction only applies to axis allowing it, that
            is in axis containing zones or countries labels corresponding to 
            the zone selection.

        Returns
        -------
        Part object
            New Part with selection set to 0.

        """
        if isinstance(dimensions,str):
            dimensions = [dimensions]
        if isinstance(labels,str):
            labels = [labels]
        if isinstance(dimensions,dict):
            to_select = dimensions
            labels = list(to_select.values())
            dimensions = list(dimensions.keys())
        else:
            to_select = dict()
            for dim,label in zip(dimensions,labels):
                to_select[dim] = label
        if len(labels) != len(dimensions):
            if len(dimensions)==1:
                #If only one dimension is passed, we broadcast the labels
                labels = [labels]
            else:
                #Raise an error for ambiguous cases
                log.critical("Number of dimensions and labels do not match for extraction")
                raise ValueError("Number of dimensions and labels do not match for extraction")

        allowed = []
        for i,ax in enumerate(self.axes):
            if all(dimension in ax.dimensions for dimension in dimensions):
                allowed.append(i)
        if len(allowed) == 0:
            if len(dimensions) == 1:
                log.critical("No axis found for extraction on "+str(dimensions))
                raise ValueError("No axis found for extraction on "+str(dimensions))
            log.info(f"No axis found for simultaneous extractions on {dimensions}")
            log.info(f"Try successive extractions on {dimensions}")
            for dim,label in zip(dimensions,labels):
                self.extraction(dim,label,
                                on_groupings=on_groupings,
                                domestic_only=domestic_only,
                                axis=axis)
        if axis == "all":
            log.info(f"Extract {to_select} on axes "+ str(allowed))
            axis = allowed
        if isinstance(axis,int):
            axis = [axis]
        if not all(ax in allowed for ax in axis):
            wrong = [ax for ax in axis if ax not in allowed]
            log.critical(f"Cannot extract {dimensions} on axis {wrong}")
            raise ValueError(f"Cannot extract {dimensions} on axis {wrong}")

        if not domestic_only:
            #If no domestic_only, we can simply set the selection to 0
            sel = ["all"]*self.ndim
            for i,ax in enumerate(self.axes):
                if i in axis:
                    sel[i] = to_select
            output = self.copy()
            output[sel] = 0
            return output
        
        if not on_groupings:
            #If no groupings, develop the selected groupings
            for i,dim in enumerate(dimensions):
                if dim in self.groupings.keys():
                    for label in labels[i]:
                        if label in self.groupings[dim].keys():
                            for j in self.groupings[dim][label]:
                                labels[i].append(j)
                            labels[i].remove(label)
        
        for i,label in enumerate(labels):
            if label == "all":
                if on_groupings and dimensions[i] in self.groupings.keys():
                    labels[i] = list(
                        self.axes[axis[i]].groupings[dimensions[i]].keys()
                        )
                else:
                    labels[i] = self.axes[axis[i]].labels[dimensions[i]]

        output = self.copy()
        for label in itertools.product(*labels):
            #Iteratively set domestic selections to 0
            seldict = dict(zip(dimensions,label))
            sel = ["all"]*self.ndim
            for i in range(self.ndim):
                if i in axis:
                    sel[i] = seldict
            output[sel] = 0
        return output
    
    def leontief_inversion(self):
        if self.ndim == 2 and self.issquare():
            data = np.linalg.inv(np.identity(len(self.axes[0])) - self.data)
            return self.alias(name=f"l_{self.name}",data=data)
        raise ValueError("Can only compute the Leontief inverse on"+\
                         " square parts")
    
    def zone(self):
        """
        Apply a grouping by zone dependent on the shape of the Part.
        
        Final demand Parts are summed over zones.
        Horizontal extensions are expanded by zone.

        Raises
        ------
        AttributeError
            Parts with other shapes are rejected.

        Returns
        -------
        Part object
            Grouped part.

        """
        log.warning("This function is deprecated as it returns different "+\
                    "results depending on the shape of the Part. "+\
                        "Use group or expand instead.")
        if self.ndim == 2 and not self.issquare():
            if "countries" in self.axes[1].dimensions:
                #Expand normal parts
                return self.group(1,"countries")
        if self.ndim == 1:
            #Expand horizontal parts
            return self.expand("countries")
        raise AttributeError(f"Part {self.name} has no predefined grouping.")
    
    def update_groupings(self,groupings,ax=None):
        """Update the groupings of the current Part object
        
        groupings : dict
            Description of the groupings
        ax: int, list of int
            Axes to update. If left empty, all axes are updated.
        """
        self.groupings = groupings
        if ax is None:
            ax = range(self.ndim)
        for axe in list(ax):
            self.axes[axe].update_groupings(groupings)
    
    def aggregate(self,on=None,axis=None):
        """Aggregate dimensions along one or several axis.

        If groupings are defined, these are taken into account.
        If you want to sum over the dimension of an axis, use the sum method.

        If no axis is specified, the operation is applied to all axes.
        If no dimension is specified, the operation is applied to all possible dimensions.

        Parameters
        ----------
        axis : str or list of str, optional
            List of axis along which countries are grouped.
            If left emtpy, countries are grouped along all possible axis.
        on : str or dict, optional
            Indicate wether the grouping should be done by zones ("zones")
            or by sector ("sectors"), or both ("both").
            The default is "zones".
            If both, the operation is equivalent to summing over an axis

        Raises
        ------
        ValueError
            Raised if a selected Axe cannot be grouped.

        Returns
        -------
        Part object
            Part grouped by zone.

        """
        log.debug(f"Aggregate Part {self.name} along axis {axis} on {on}")

        if on is None:
            on = list(self.groupings.keys())
        
        
        if isinstance(on,list):
            for item in on:
                self = self.aggregate(on = item, axis=axis)
            return self
        if on not in self.groupings.keys():
            raise ValueError(f"No groupings defined for dimensions {on}")
        
        if axis is None:
            axis = self.hasax(
                on
            )
        if isinstance(axis,int):
            axis = [axis]
            
        output = self.alias()

        for ax in axis:
            output = output.aggregate_on(on,ax)

        output.name = f"{on}_grouped_{self.name}"
        return output
    
    def aggregate_on(self,on,axis):
        """Aggregate a Part along a given axis
        
        Parameters
        ----------
        on : str
            Dimension to aggregate on
        axis : int
            Axis to aggregate
        
        Returns
        -------
        Part instance
            Aggregated Part
        """
        if on not in self.axes[axis].dimensions:
            raise ValueError(f"Dimension {on} not found in axis {axis}")
        
        new_labels = self.axes[axis].labels.copy()
        new_labels[on] = list(self.axes[axis].groupings[on].keys())
        new_groupings = self.groupings.copy()
        new_groupings[on] = {
            item : [item] for item in self.groupings[on]
        }

        new_axis = self.axes.copy()
        new_axis[axis] = Axe(new_labels,new_groupings)
        new_shape = [len(ax) for ax in new_axis]

        output = Part(axes=new_axis)
        idsum = new_axis[axis].dimensions.index(on) #Index of the dimension to sum on
        ref_dev = self.develop(axis, squeeze=False)
        new_dev = output.develop(axis,squeeze=False)
        selector = ["all"]*ref_dev.ndim
        for label in new_labels[on]:
            selector[axis+idsum] = label
            new_dev[selector] = ref_dev[selector].sum(
                axis=axis+idsum,
                keepdims=True
            )
        output = new_dev.data.reshape(new_shape)
        return self.alias(data=output,name=f"{on}_grouped_{self.name}",
                                axes=new_axis)

 
    def get_labels(self,axis=None):
        """
        Returns a list with the labels of each axis 
        of the part in a the dictionary.
        
        Parameters
        ----------
        axis : int or list of int, optional
            Axis to investigate, by default None,
            All axes are investigated.
        
        Returns
        -------
        list
            Labels used in the part.
        """
        labels = []
        if axis is None:
            axis = range(self.ndim)
        if isinstance(axis,int):
            axis = [axis]
            #Make sure the axis is iterable
        for ax in axis:
            labels.append(self.axes[ax].labels)
        return labels
    
    def list_labels(self):
        """List the labels of the Part"""
        labels = dict()
        ax_labels = self.get_labels()
        for ax in ax_labels:
            for label in ax.keys():
                if label not in labels.keys():
                    labels[label] = ax[label]
        return labels
    
    def get_dimensions(self,axis=None):
        """
        Returns the list dimensions of the Part

        Parameters
        ----------
        axis : int or list of int, optional
            Axis to investigate, by default None,
            All axes are investigated.
        
        Returns
        -------
        list
            Dimensions of the axes.
        """
        dimensions = []
        if axis is None:
            axis = range(self.ndim)
        if isinstance(axis,int):
            axis = [axis]
            #Make sure the axis is iterable
        for ax in axis:
            dimensions.append(self.axes[ax].dimensions)
        return dimensions
    
    def rename_labels(self,old,new):
        """
        Rename some labels of the Part

        Parameters
        ----------
        old : str
            Name of the label to change.
        new : str
            New label name.
        """
        for ax in self.axes:
            if old in ax.dimensions:
                ax.rename_labels(old,new)
        self._store_labels()

    def replace_labels(self,name,labels,axis=None):
        """
        Update a label of the part

        Parameters
        ----------
        name : str
            Name of the label to update, by default None
        labels : dict or list
            New labels for the corresponding ax.
            If a list is passed, the former label name is used.
        axis : int, list of int, optional
            List of axis on which the label is changed.
            By default None, all possible axes are updated.
        """
        if axis is None:
            axis = range(self.ndim)
        if isinstance(axis,int):
            axis = [axis]
        if isinstance(labels,list):
            labels = {name:labels}
        for ax in axis:
            if name in self.axes[ax].dimensions:
                self.axes[ax].replace_labels(name,labels)
        self._store_labels()
    
    def set_labels(self,labels,axis=None):
        """
        Change the labels of the Part

        Parameters
        ----------
        labels : dict or nested list
            New labels of the axes.
            If a nested list is passed, the first level corresponds to the axes
        axis : str, optional
            Axis on which the labels are changes, by default None,
            all axes are updated.
        """
        if axis is None:
            axis = range(self.ndim)
        if isinstance(axis,int):
            axis = [axis]
        if isinstance(labels,list) and len(labels) == self.ndim:
            labels = {i:labels[i] for i in range(self.ndim)}
        for ax in axis:
            self.axes[ax].set_labels(labels[ax])
        self._store_labels()
    
    def _store_labels(self):
        """Store the labels of the Part"""
        self.labels = self.list_labels()

    def add_labels(self,labels,dimension=None,axes=None,
                    fill_value=0):
        """
        Add indices to one or multiple Part axes.

        Parameters
        ----------
        new_labels : list of str or dict
            List of indices to add
        dimension : str, optional
            Labels the new indices should be appended to,
            in case new_labels is not a dict.
            If new_labels is a dict, dimension is ignored.
        axes : int or set of ints, optional
            Axes or list of axes to modify.
            In case it is not specified, the axes are detected
            by looking for the dimension (or new_labels keys) in each ax.
        fill_value : float, optional
            Value used to initialize the new Part

        Returns
        -------
        Part instance
            Part instance with the additional ax indices.

        Raise
        -----
        ValueError
            A Value Error is raised if neither the axes nor the 
            ref_set arguments are set.
        """
        if isinstance(labels,list):
            labels = {dimension:labels}
        dimension = list(labels.keys())[0]
        if axes is None:
            #Identify the axes with the ref_set in labels
            axes = self.hasax(dimension)
        elif isinstance(axes,int):
            axes = [axes]

        new_axes = self.axes.copy()
        sel = ["all"]*self.ndim
        for ax in axes:
            log.debug("Add labels to axis "+str(ax))
            sel[ax] = dict()
            old_labels = self.axes[ax].labels
            new_labels = self.axes[ax].labels.copy()
            new_labels[dimension] = old_labels[dimension] + labels[dimension]
            new_axes[ax] = Axe(new_labels,self.groupings)
            sel[ax] = old_labels

        new_shape = [len(ax) for ax in new_axes]
        output = self.alias(data=np.full(new_shape,fill_value,dtype="float64"),
                            axes=new_axes)
        
        #Put original data back in place
        output[sel] = self.data
        return output
    
    def reorder_data(self,new_labels):
        """
        Reorder the data of the Part according to new labels.

        Parameters
        ----------
        new_labels : dict
            New labels for the axes.
            The keys are the dimensions, the values are the labels.

        Raises
        ------
        ValueError
            If the new labels do not match the current axes.
        """
        
        if not isinstance(new_labels,dict):
            raise ValueError("New labels should be a dictionary")
        
        
        
        sels = []
        for axis in self.axes:
            old_labels = axis.labels
            if not set(new_labels.keys()).issubset(set(old_labels.keys())):
                sels.append(axis.get("all"))
                continue
            for key in new_labels.keys():
                set_old = set(old_labels[key])
                set_new = set(new_labels[key])
                if not set_old.issubset(set_new):
                    raise ValueError(f"The new labels provided for dimension '{key}' is not a superset of the old labels. " +
                                    f"Old labels: {old_labels[key]}, new labels: {new_labels[key]}. "
                                    "If you want to rename the labels of this dimensions, use the method 'replace_labels() before reordering the data")


            ax_label_dict = {}
            for key in old_labels.keys():
                if key in new_labels.keys():
                    ax_label_dict[key] = new_labels[key]
                    for lab in new_labels[key]: 
                        if lab not in old_labels[key]:
                            # If the label is not in the list, remove it
                            ax_label_dict[key].remove(lab)
                else:
                    ax_label_dict[key] = old_labels[key]
 
            sels.append(axis.get(ax_label_dict))
        
        if len(sels) == 0:
            raise ValueError(f"None of the dimensions provided in the new labels dict {new_labels.keys()} are present "+
                             f"in the labels of part '{self.name}', which only contains the dimensions {self.get_dimensions()}")
        
        #Execute the selection
        self.data = self.data[np.ix_(*sels)]
        
        # Update the axes with the new labels
        for dim in new_labels.keys():
            self.replace_labels(name = dim, labels = new_labels[dim])
     
    
    def expand(self,axis=None,over="countries"):
        """
        Expand an axis of the Part
        
        Create a new Axes with a unique dimension.
        Note that this operation significantly expands the size of the Part.
        It is recommended to use this method with Extension parts only.

        Parameters
        ----------
        axis : int, optional
            Axe to extend. 
            If left empty, the first suitable axe is expanded.
        over : str, optional
            Axe dimension to expand the Part by.
            The default is "countries".

        Returns
        -------
        Part object
            New Part object with an additional dimension.

        """
        if axis is None:
            axis = self.hasax(over)
        if isinstance(axis,int):
            axis = [axis]

        output = self.copy()
        
        for ax in axis[::-1]:
            output = output._expand_on(ax,over)
        return output

    def _expand_on(self,ax,over):
        """Expand over a single axis"""
        ref_ax = self.axes[ax]
        new_ax = Axe({over: ref_ax.labels[over]}, groupings=self.groupings)
        axes = self.axes.copy()
        axes.insert(ax,new_ax)
        new_shape = list(self.shape)
        new_shape.insert(ax,len(new_ax))
        output = np.zeros(new_shape)
        selector = [slice(None)]*self.ndim
        ordering = ref_ax.dimensions.index(over)
        for item in ref_ax.labels[over]:
            newsel,refsel = selector.copy(),selector.copy()
            newsel.insert(ax,new_ax.get(item))
            ax_selector = ["all" for i in range(ordering)]
            ax_selector.append(item)
            newsel[ax+1] = ref_ax.get(ax_selector)
            refsel[ax]= ref_ax.get(ax_selector)
            output[tuple(newsel)] = self.data[tuple(refsel)]
        return self.alias(data=output,name=f"expanded_{self.name}",axes=axes)

    
    def issquare(self):
        """Assert wether the Part is square"""
        return self.ndim == 2 and len(self.axes[0])==len(self.axes[1])
    
    def hasneg(self):
        """Test whether Part has negative elements"""
        if np.any(self.data<0):
            return True
        return False

    def hasax(self,name=None):
        """Returns the dimensions along which a Part has given labels
        
        If no axis can be found, an empty list is returned empty.
        This method can be used to assert the existence of a given dimension
        in the part.

        Parameters
        ----------
        name : int, optional
            Name of the label to look for.
            If no name is given, all axes are returned.

        Returns
        -------
        axes : list of ints
            Dimensions along which the labels are found.

        """
        if name == "any" or name is None:
            return [i for i in range(self.ndim)]
        axes = []
        for i,ax in enumerate(self.axes):
            if name in ax.dimensions:
                axes.append(i)
        return axes
    
    def __str__(self):
        return f"{self.name} Part object with {self.ndim} dimensions"
    
    def sum(self,axis=None,on=None,keepdims=False):
        """
        Sum the Part along one or several axis, and/or on a given dimension.

        Parameters
        ----------
        axis : int or list of int, optional
            Axe along which the sum is evaluated.
            By default None, the sum of all coefficients of the Part is returned
        on : str, optional
            name of the dimension to be summed on.
            If no axis is defined, the Part is summed over all axis having 
            the corresponding dimension.
            By default None, the full ax is summed
        keepdims : bool, optional
            Whether to keep the number of dimensions of the original.
            By default False, the dimensions of lenght 1 are removed.

        Returns
        -------
        Part instance or float
            Result of the sum.
        """
        if axis is None:
            if on is None:
                return self.data.sum()
            if not keepdims:
                self = self.squeeze()
            axis = self.hasax(on)
        if isinstance(axis,int):
            if on is not None:
                return self._sum_on(axis,on,keepdims)
            ax = self.axes.copy()
            if not keepdims:
                del ax[axis]
            else:
                ax[axis] = Axe(["all"])
            return self.alias(
                data=self.data.sum(axis,keepdims=keepdims),
                name=f"{self.name}_sum_{axis}",
                axes = ax
            )
        axis = sorted(axis)
        for ax in axis[::-1]:
            self = self.sum(ax,on,keepdims)
        return self

    def _sum_on(self,axis,on,keepdims=False):
        """
        Sum a Part along an axis on a given dimension
        """
        ax = self.axes[axis]
        if on not in ax.dimensions:
            raise ValueError(f"Cannot sum on {on} as it is not a dimension of axis {axis}")
        if ax.levels == 1:
            #If the axis has a single level, this is a simple sum
            axes = self.axes.copy()
            if not keepdims:
                del axes[axis]
            return self.alias(
                data = self.data.sum(axis,keepdims=keepdims),
                name=f"{self.name}_sum_{axis}",
                axes = axes
            )
        #Otherwise, sum on the relevant levels
        idsum = ax.dimensions.index(on) #Index of the dimension to sum on
        dev = self.develop(axis,squeeze=False)
        dev = dev.sum(axis+idsum,keepdims=keepdims)
        if keepdims:
            dev = dev.combine_axes(axis,axis+idsum)
        dev.name = f"{self.name}_sum_on_{on}_{axis}"
        return dev
        
    def save(self,
             file=None,
             name=None,
             extension=".npy",
             overwrite=False,
             include_labels=False,
             write_instructions=False,
             **kwargs):
        """
        Save the Part object to a file

        Parameters
        ----------
        name : str, optional
            Name under which the Part is saved.
            By default, the current part is used.
        path : Path-like, optional
            Directory in which the Path should be saved, 
            by default None, the dir from which the part was loaded.
        extension : str, optional
            Format under which the part is saved. The default ".npy"
            If ".csv" is chosen, the part is saved as a csv file with labels
        file : path-like, optional
            Full path to the file to save the Part to.
            This overrides the path, name and extension arguments.
        overwrite : boolm optional
            Whether to overwrite an existing file. 
            If set False, the file is saved with a new name.
            The default is False.
        write_instructions : bool, optional
            Whether to write the loading instructions to a yaml file.
            The default is False.
        include_labels : bool, optional
            Whether to include the labels in the saved file.
            Only applicable to .csv and .xlsx files.
        **kwargs : dict
            Additional arguments to pass to the saving function

        Raises
        ------
        FileNotFoundError
            _description_
        """
        path = kwargs.get("path",None)
        if file is not None:
            path,name = os.path.split(file)
            name,possible_extension = os.path.splitext(name)
            if possible_extension != "":
                extension = possible_extension
        if name is None:
            name = self.name
        if path is None:
            raise FileNotFoundError("No path specified for saving the Part")
        if extension == ".nc":
            path = os.path.join(path,name+extension)
            save_to_nc(self,path,overwrite,
                       write_instructions=write_instructions,
                       **kwargs)
        else:
            save_part_to_folder(
                self,
                path = path,
                name = name,
                extension = extension,
                overwrite = overwrite,
                include_labels=include_labels,
                write_instructions = write_instructions,
                **kwargs
            )

    def to_pandas(self):
        """Return the current Part object as a Pandas DataFrame
        
        Only applicable to Parts objects with 1 or 2 dimensions.
        """
        return converters.pandas.to_pandas(self)
    
    def to_xarray(self,attrs=dict()):
        """
        Save the Part object to an xarray DataArray

        Labels are directly passed to the DataArray as coords.
        Note that data will be flattened.
        The dimension order will be saved as an attribute.
        If you're loading the data back,
        the Part will be automatically reshaped to its original dimensions.

        Parameters
        ----------
        attrs : dict
            Additional arguments to store as attributes

        Returns
        -------
        xr.DataArray
            Corresponding DataArray
        """
        return converters.xarray.to_DataArray(self, attrs=attrs)

    def mean(self,axis=None):
        return self.data.mean(axis)
    
    def min(self,axis=None):
        return self.data.min(axis)

    def max(self,axis=None):
        return self.data.max(axis)
        
    def mul(self,a,propagate_labels=True):
        """
        Matrix multiplication between parts with labels propagation

        Parameters
        ----------
        a : Part or numpy array
            Right-hand multiplicator.
        propagate_labels : bool, optional
            Whether to try propagating the labels from the right hand multiplicator
            By default True.
            If right-hand multiplicator is not a Part object, becomes False.

        Returns
        -------
        Part instance
            result of the multiplication
        """
        if not isinstance(a,Part):
            propagate_labels = False
            name="array"
        else:
            name = a.name
        data = np.matmul(self.data,a.data)
        axes = [self.axes[i] for i in range(self.ndim-1)]
        for ax in range(a.ndim-1):
            if propagate_labels:
                axes.append(a.axes[ax+1])
            else:
                axes.append(Axe([i for i in range(a.shape[ax+1])]))
        return self.alias(data=data,name=f"{self.name}.{name}",axes=axes)
    
    def filter(self,threshold,fill_value=0):
        """
        Set to 0 the values below a given threshold

        Parameters
        ----------
        threshold : float
            Threshold value.
        fill_value : float, optional
            Value to replace the filtered values with.
            The default is 0.

        Returns
        -------
        Part instance
            Filtered Part.

        """
        data = self.data.copy()
        data[data<threshold] = fill_value
        return self.alias(data=data,name=f"filtered_{self.name}_{threshold}")
    
    def diag(self):
        if self.ndim == 1:
            log.info("Diagonalize a 1D part")
            return self.alias(data=np.diag(self.data),
                              name=f"diag_{self.name}",
                              axes = self.axes*2)
        try:
            log.info("The part has too many dimensions: try to diagonalize the squeezed part")
            return self.squeeze().diag()
        except:
            raise ValueError("Cannot diagonalize a part with more than 2 dimensions")

    def __add__(self,a):
        if isinstance(a,Part):
            name = a.name
            a = a.data
        else:
            name=""
        if isinstance(a,np.ndarray) and self.ndim != a.ndim:
            a = a.squeeze()
            self = self.squeeze()
        return self.alias(data=a+self.data,name=f"{self.name}+{name}")
    
    def __radd__(self,a):
        return self.__add__(a)
    
    def __rmul__(self,a):
        return self.__mul__(a)
    
    def __mul__(self,a):
        if isinstance(a,Part):
            name = "{a.name}*{self.name}"
            a = a.data 
        else:
            if isinstance(a,int):
                name = f"{a}*{self.name}"
            else:
                name = f"array*{self.name}"
        data = self.data*a
        if data.ndim!=self.ndim:
            data = data.squeeze()
        #Trust numpy to broadcast the multiplication
        #Squeeze to get rid of unused dimensions
        return self.alias(data=data,
                          name=name)
    
    def __neg__(self):
        return self.alias(data=-self.data,name=f"-{self.name}")
    
    def __lt__(self,other):
        if isinstance(other,Part):
            return self.data < other.data
        return self.data < other 
    
    def __le__(self,other):
        if isinstance(other,Part):
            return self.data <= other.data
        return self.data <= other
    
    def __gt__(self,other):
        if isinstance(other,Part):
            return self.data > other.data
        return self.data > other
    
    def __ge__(self,other):
        if isinstance(other,Part):
            return self.data >= other.data
        return self.data >= other
    
    def __sub__(self,a):
        if isinstance(a,Part):
            name = a.name
            a = a.data
        else:
            name=""
        return self.alias(data=self.data-a,name=f"{self.name}-{name}")
    
    def __rsub__(self,a):
        if isinstance(a,Part):
            name = a.name
            a = a.data
        else:
            name=""
        return self.alias(data=a-self.data,name=f"{name}-{self.name}")
    
    def power(self,a):
        if isinstance(a,Part):
            a = a.data
            name = f"{self.name}**{a.name}"
        elif isinstance(a,int) or isinstance(a,float):
            name = f"{self.name}**{a}"
        else:
            name = f"{self.name}**array"
        return self.alias(data=np.power(self,a),name=name)

    def __pow__(self,a):
        return self.power(a)

    def __eq__(self,a):
        if isinstance(a,Part):
            return np.all(self.data==a.data)
        return False
    
    def __rtruediv__(self,a):
        if isinstance(a,Part):
            name = f"{self.name}/{a.name}"
            a = a.data
        else:
            if isinstance(a,int):
                name = f"{a}/{self.name}"
            else:
                name= f"array/{self.name}"
        if np.sum(self.data==0)!=0:
            log.warning("Division by zero in "+name)
        return self.alias(data=a/self.data,
                          name=name)
    
    def __truediv__(self,a):
        if isinstance(a,Part):
            name = f"{a.name}/{self.name}"
            a = a.data
        else:
            if isinstance(a,int):
                name = f"{self.name}/{a}"
            else:
                name= f"{self.name}/array"
        if np.sum(a==0)!=0:
            log.warning("Division by zero in "+name)
        return self.alias(data=self.data/a,
                          name=name)
    
    def __getattr__(self,name):
        name = name.casefold()
        try:
            return self.metadata[name]
        except:
            pass
        raise AttributeError(f"Attribute {name} not found")
    
    def transpose(self):
        return self.alias(data=self.data.transpose(),
                          name=f"transposed_{self.name}",
                          axes=self.axes[::-1])
        
        