# -*- coding: utf-8 -*-
"""
Definition of Part Axes
"""

import logging
import itertools
import pandas as pd
import numpy as np
from copy import deepcopy

log = logging.getLogger(__name__)
class Axe:
    """
    Representation of an Axe object.

    An Axe holds the labels and dimensions for an MRIO Part. Axes are used 
    to slice MRIO Parts based on labels or indices and support multi-level 
    indexing and groupings.

    Instance variables
    ------------------
    labels : dict
        Dictionary of labels for each level of the Axe.
    levels : int
        Number of levels in the Axe.
    dims : list of int
        Number of labels for each level.
    dimensions : list of str
        Keys of the labels dictionary, representing the dimensions of the Axe.
    groupings : dict
        Groupings of the labels for each level of the Axe.
    mappings : dict
        Mappings used to convert grouping labels into indices.
    multipliers : dict
        Multipliers used to convert labels into indices.
    name : str
        Name of the Axe.

    Methods
    -------
    set_labels(labels):
        Set the labels of the Axe.
    update_multipliers():
        Update the multipliers used to convert labels into indices.
    squeeze():
        Remove levels with only one label.
    swap_levels(level1, level2):
        Swap the positions of two levels in the Axe.
    label(as_index=False):
        Generate the labels for the full axis.
    isin(arg, level):
        Check whether an element is in the labels of a given level.
    derive_mappings(groupings=None):
        Update the mappings of the Axe based on the groupings.
    update_groupings(groupings=None):
        Update the groupings of the Axe.
    get(args, labels=False):
        Get the indices corresponding to a selection on the Axe.
    rename_labels(old, new):
        Rename labels in the Axe.
    replace_labels(name, labels):
        Replace a given label in the Axe.
    has_dim(dim):
        Check whether a given dimension is in the Axe.
    __getitem__(*args):
        Indexing is passed to the `get` method.
    __eq__(other):
        Check equality between two Axe objects.
    __len__():
        Get the full label length of the Axe.
    """    
    
    def __init__(self,labels,groupings=None,
                 name=None):
        """
        Initialize an Axe object.

        Parameters
        ----------
        labels : dict or list of list of str
            Dictionary of labels for each level of the Axe. If a list of lists 
            is passed, levels are set to 0, 1, 2, etc.
        groupings : dict, optional
            Dictionary of groupings for each level of the Axe. Groupings define 
            how labels are grouped into larger categories (e.g., countries into zones).
            If not provided, groupings are set to the identity.
        name : str, optional
            Name of the Axe. If not provided, a name is generated automatically 
            based on the dimensions.

        Raises
        ------
        TypeError
            If the provided labels are not a dictionary or a list of lists.

        Notes
        -----
        The `labels` parameter defines the structure of the Axe, while the 
        `groupings` parameter allows grouping labels into higher-level categories.
        """
        if isinstance(labels,dict):
            self.labels = labels
        elif isinstance(labels,list):
            if isinstance(labels[0],dict):
                self.labels = dict()
                for label in labels:
                    self.labels.update(label)
            elif not isinstance(labels[0],list):
                self.labels = {str(0):labels}
            else:
                self.labels = {str(i):labels[i] for i in range(len(labels))}
        else:
            raise TypeError("Labels must be a list or a dict. Input is of type "+str(type(labels)))
        self.levels = len(self.labels)
        self.dims = [len(dim) for dim in self.labels.values()]
        self.dimensions = [
            str(dim) for dim in self.labels.keys()
        ] #Dimensions of the Axe
        #Dimensions also save the order of the levels
        self.ndim = len(self.dims)
        self.update_multipliers()
        if groupings is None:
            self.groupings = {i:{} for i in self.dimensions}
        else:
            self.groupings = groupings
        self.mappings = dict()
        self.derive_mappings(groupings)
        if name is None:
            if len(self.dimensions)>1:
                self.name = "_".join(self.dimensions)
            self.name = self.dimensions[0]
        else:
            self.name = name

    def set_labels(self,labels):
        """Set the labels of the Axe
        
        Parameters
        ----------
        labels : dict or list of list of str
            Dict of labels for each level of the Axe.
            The levels are interpreted in the order of the keys.
            If a list of list of str is passed, levels are set to 0,1,2...
        """
        if isinstance(labels,dict):
            self.labels = labels
        elif isinstance(labels,list):
            if not isinstance(labels[0],list):
                self.labels = {str(0):labels}
            else:
                self.labels = {str(i):labels[i] for i in range(len(labels))}
        else:
            raise TypeError("Labels must be a list or a dict. Input is of type "+str(type(labels)))
        self.levels = len(self.labels)
        self.dims = [len(dim) for dim in self.labels.values()]
        self.dimensions = list(self.labels.keys())
        self.ndim = len(self.dims)

    def update_multipliers(self):
        """
        Update the multipliers used to convert labels into indices
        """
        multipliers = []
        for i in range(len(self.dims)):
            multipliers.append(self.dims[i]*multipliers[i-1] if i > 0 else 1)
        self.multipliers = { #Dictionnary of multipliers for each level
            i:multiplier for i,multiplier in zip(self.dimensions,multipliers[::-1])
            }

    def squeeze(self):
        """Remove levels with only one label"""
        for key in self.dimensions:
            if len(self.labels[key]) == 1:
                self.labels.pop(key)
                self.multipliers.pop(key)
                if key in self.mappings.keys():
                    self.mappings.pop(key)
        self.levels = len(self.labels)
        self.dims = [len(dim) for dim in self.labels.values()]
        self.dimensions = list(self.labels.keys())
        self.ndim = len(self.dims)
        

    def swap_levels(self,level1,level2):
        """Swap the positions of two levels in the Axe
        
        Parameters
        ----------
        level1 : int
            Level to swap
        level2 : int
            Level to swap
        """
        if level1 not in self.labels.keys() or level2 not in self.labels.keys():
            raise IndexError("Levels must be in the Axe")
        dims = self.dimensions
        dims[level1],dims[level2] = dims[level2],dims[level1]
        self.dimensions = dims
        self.dims = [len(dim) for dim in self.labels.values()]

    def __str__(self):
        return f"Axe object of len {len(self)}, with {self.levels} levels: {self.dimensions}"
            
    def label(self,as_index=False):
        """ Generate the labels for the full axis

        Parameters
        ----------
        as_index : bool, optional
            Whether to return a Pandas MultiIndex. 
            The default is False, in which case a list of labels is returned.

        
        Returns
        -------
        list of str
            Labels along the Axe
        """
        if as_index:
            if self.levels == 1:
                return pd.Index(self.labels[self.dimensions[0]],name=self.dimensions[0])
            return pd.MultiIndex.from_product(
                [self.labels[key] for key in self.dimensions],
                names = self.dimensions
                )
        return list(itertools.product(*[self.labels[key] for key in self.dimensions]))

    
    def isin(self,arg,level):
        """
        Assert whether an element is in the labels of a given level

        Parameters
        ----------
        arg : str, int or list of int,str
            Element to look for.
        level : str
            Key of the level to look into.

        Returns
        -------
        bool
            Whether the element is in the labels.

        """
        if "all" in arg:
            return True
        if isinstance(arg,(int,np.integer)) and arg < len(self.labels[level]):
            return True
        if isinstance(arg,str):
            return arg in self.labels[level] \
                or arg in self.mappings[level].keys()\
                    or arg=="all"
        if isinstance(arg,list):
            for a in arg:
                if not self.isin(a,level):
                    return False
            return True
        raise TypeError(
            "Arg must be a string, an int or a list of strings or ints."+\
                " Input is of type "+str(type(arg))
            )

    def derive_mappings(self,groupings=None):
        """Update the mappings of the Axe
        
        Mappings are defined at Axe level and derive from the current groupings
        Mappings are used to convert grouping labels into indices

        Parameters
        ----------
        groupings : dict of dict
            Dict of groupings for each level of the Axe.
            Grouping of labels into larger categories (e.g countries into zones).
            If groupings contain references not in the labels, these are removed.
            By default, groupings are set to the identity.
        """
        
        if groupings is None:
            for key in self.dimensions:
                self.mappings[key] = {
                    label:[i] for i,label in enumerate(self.labels[key])
                }
            return
        to_sort = deepcopy(groupings)
        for key in self.dimensions:
            self.mappings[key] = dict()
            covered = []

            if to_sort is not None and key in to_sort.keys():
                for group in to_sort[key].keys():
                    idlist = []
                    for label in to_sort[key][group]:
                        if label not in self.labels[key]\
                            and label != "all":
                            log.debug(
                                f"Label {label} in group {group} is not in the labels of the Axe"
                                )
                            to_sort[key][group].remove(label)
                        elif label in covered:
                            log.warning(
                                f"Label {label} is in multiple groups and will be ignored from group {group}"
                                )
                        elif label == "all":
                            idlist = [i for i in len(self.labels[key])]
                            covered = self.labels[key] + "all"
                        else:
                            idlist.append(self.labels[key].index(label))
                            covered.append(label)
                    to_sort[key][group] = idlist.copy()
                self.mappings[key] = to_sort[key].copy()
            else:
                self.mappings[key] = dict()

    def update_groupings(self,groupings=None):
        self.groupings = groupings
        self.derive_mappings(groupings)
    
    def get_on(self,arg,level,multiplier):
        """
        Recursively get the index of an arg on a given level

        Parameters
        ----------
        arg : str, int, list of str, int
            Element to look for.
        level : str
            Key of the level to look into.
        """
        if isinstance(arg,str):
            if arg == "all":
                return [i*multiplier for i in range(len(self.labels[level]))]
            if arg in self.mappings[level].keys():
                return [
                    i*multiplier for i in self.mappings[level][arg]
                ]
            return [self.labels[level].index(arg)*multiplier]
        if isinstance(arg,(int,np.integer)):
            return [arg*multiplier]
        sel = []
        for a in arg:
            sel += self.get_on(a,level,multiplier)
        return sel
    
    def get_single_ax(self,args):
        """Make selection for single level Axes"""
        sel = []
        level = self.dimensions[0]
        sel.append(self.get_on(args,level,self.multipliers[level]))
        for level in range(1,self.levels):
            #Fill the rest of the selection with all elements
            sel.append([i*self.multipliers[level] for i in range(len(self.labels[level]))])
        return [sum(arg) for arg in itertools.product(*sel)]
    
    def get_labels(self):
        """Get the labels of the Axe as a dict"""
        return {key:self.labels[key] for key in self.dimensions}
    
    def get_groupings(self):
        """Get the groupings of the Axe"""
        return self.groupings
    
    def get_labs(self,args):
        """Extract the labels corresponding to a given selection of multiple levels
        
        Parameters
        ----------
        args : list of ints
            Cleaned selection of indices
        
        Returns
        -------
        dict
            Dict of labels for each level
        """
        labels = dict()
        for i,key in enumerate(self.dimensions):
            if isinstance(args[i],(str)):
                labels[key] = [args[i]]
            
            else:
                labels[key] = [
                    self.labels[key][j//self.multipliers[key]] for j in args[i]
                ]
        return labels

    def get(self,args,labels=False):
        """
        Get the indices corresponding to a selection on the Axe

        Parameters
        ----------
        args : str, int, dict, list of str, int
            Arguments to select on the Axe.
            If a dict is passed, it is assumed that the keys are the dimensions of the Axe.
            If a list is passed, it is assumed that the first element is the selection on the first level,
            the second on the second level, etc. 
            If the selection on multipler levels fails, the selection is assumed to be on the first level only.
        labels : bool, optional
            Whether to return the labels of the selection, by default False

        Returns
        -------
        list of int or (list of ints, dict, dict)
            If labels is False, returns the indices of the selection.
            If labels is True, returns the indices of the selection, 
            the labels of the selection and the groupings of the Axe.
        """
        if isinstance(args,(int,str,np.integer)):
            if args == "all":
                #Shortcut for all elements
                sel = [i for i in range(len(self))]
                if labels:
                    return sel,self.labels.copy(),self.groupings
                return sel
            args = [args]
        if all(isinstance(arg,(int,np.integer)) for arg in args):
            #Shortcut for int based selection
            if labels:
                labels = self.label().copy()
                labs = [labels[arg] for arg in args]
                return args,labs,self.groupings
            return args
        if self.levels == 1:
            if isinstance(args,dict):
                args = list(args.values())
            sel = self.get_on(args,self.dimensions[0],1)
            if labels:
                labs = {
                    self.dimensions[0] : [self.labels[self.dimensions[0]][i] for i in sel]
                }
                return sel,labs,self.groupings
            return sel
        sel = []

        #Preformat the args input
        if isinstance(args,dict):
            #Convert into a list
            filled = []
            for key in self.dimensions:
                if key not in args.keys():
                    filled.append(["all"])
                else:
                    if isinstance(args[key],list):
                        filled.append(args[key])
                    else:
                        filled.append([args[key]])
            if not all([key in self.dimensions for key in args.keys()]):
                raise IndexError(f"Keys {args.keys()} are invalid in Axe with dimensions {self.dimensions}")
            args = filled

        if len(args) > self.levels:
            #If the args length exceeds the number of levels,
            #it is assumed that the selection is on the first level only
            return self.get_single_ax(args)
        #Otherwise, try to select on each level
        try:
            for level,arg in enumerate(args):
                lname = self.dimensions[level]
                sel.append(self.get_on(
                    arg,lname,self.multipliers[lname]
                    ))
            for other_dim in range(level+1,self.levels):
                lname = self.dimensions[other_dim]
                sel.append(
                    self.get_on(
                        "all",lname,self.multipliers[lname])
                    )
            composed = [sum(arg) for arg in itertools.product(*sel)]
            if labels:
                labs = self.get_labs(sel)
                return composed,labs,self.groupings
            return composed
        except IndexError:
            #If it fails, try again on a single ax
            return self.get_single_ax(args)
    
    def rename_labels(self,old,new):
        """
        Rename labels in the Axes

        Parameters
        ----------
        old : str
            Former label name
        new : str
            New name
        """
        if old not in self.labels.keys():
            raise IndexError(f"Label {old} not in the Axe")
        self.labels = { (new if key == old else key): val 
                       for key, val in self.labels.items()}
        self.mappints = { (new if key == old else key): val 
                       for key, val in self.mappings.items()}
        self.dimensions = list(self.labels.keys())
        self.update_multipliers()
        
    def replace_labels(self,name,labels):
        """
        Replace a given label

        Parameters
        ----------
        name : str
            Name of the level to replace
        labels : dict
            New labels
        """
        self.labels.update(labels)
        if name != list(labels.keys())[0]:
            self.labels.pop(name)
            self.dimensions = list(self.labels.keys())
            self.mappings[labels.keys()[0]] = self.mappings.pop(name)
            self.update_multipliers()
    
    def __getitem__(self,*a):
        """
        Indexing are passed to the get method
        """
        return self.get(*a)
    
    def __eq__(self,other):
        if isinstance(other,Axe):
            if self.labels == other.labels:
                return True
        return False
    
    
    def has_dim(self,dim):
        """Check whether a given dimension is in the Axe"""
        return dim in self.dimensions
    
    def __len__(self):
        """Get the full label length of the Axe"""
        length = 1
        for dim in self.labels.values():
            length *= len(dim)
        return length