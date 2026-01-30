"""
Routine for loading MRIO tables from explicit parameters
"""

import os
from mrio_toolbox.utils.loaders._loader import Loader
from mrio_toolbox.utils.loaders._np_loader import load_file
import pathlib
import logging
from pathlib import Path

log = logging.getLogger(__name__)

class Parameter_Loader(Loader):
    """
    Class for loading MRIO data from explicit parameters.

    The `Parameter_Loader` class extends the `Loader` class to provide 
    functionality for loading MRIO data from explicit parameters, such as 
    `.npy`, `.csv`, or `.txt` files. It supports metadata extraction, label 
    formatting, and grouping management.

    Instance variables
    ------------------
    metadata : dict
        Metadata associated with the MRIO data.
    labels : dict
        Explicit dictionary of labels for the MRIO data.
    groupings : dict
        Groupings for the labels, defining higher-level aggregations.
    path : str
        Path to the data file or directory.
    labels_path : str
        Path to the labels file or directory.
    part_settings : dict
        Settings for loading specific parts of the MRIO data.
    extension : str or None
        File extension for the data files (e.g., `.npy`, `.csv`).

    Methods
    -------
    available_parts(extension=None):
        List the available parts in the current path.
    extract_path(update=False, **kwargs):
        Extract the path from the provided parameters.
    format_labels(labels):
        Process and format the label information.
    load_mrio(**kwargs):
        Load MRIO data from explicit parameters.
    get_file(**kwargs):
        Get the file to load based on the provided parameters.
    load_part(**kwargs):
        Load a specific Part from explicit parameters.
    _get_labels(l):
        Find the labels fitting an axis with a given shape.

    Notes
    -----
    This class is designed for loading MRIO data in non-netCDF formats. 
    It provides flexible handling of paths, labels, and groupings, making it 
    suitable for a variety of file formats and data structures.
    """
    def __init__(
            self,
            **kwargs
            ):
        """
        Initialize a Parameter_Loader object.

        Parameters
        ----------
        loader_kwargs : dict, optional
            Parameters passed to the underlying loader.
               - `.npy`: numpy.load
               - `.csv`, `.txt`: numpy.loadtxt
        groupings : dict, optional
            Groupings for the labels, defining higher-level aggregations.
        labels : dict, optional
            Explicit dictionary of labels for the MRIO data.
        dimensions : list of int, optional
            List of label names.
        path : str, optional
            Path to the data file or directory. Recognized paths include:
            - `path`
            - `mrio_path`
            - `file`
            - `data_path`
            - `table/year/version`
        labels_path : str, optional
            Path to the labels file or directory.
        parts : dict, optional
            Settings for loading specific parts of the MRIO data.
        extension : str, optional
            File extension for the data files (e.g., `.npy`, `.csv`).
        **kwargs : dict
            Additional metadata for the MRIO data.

        """
        self.extract_basic_info(**kwargs)
        self.extract_path(update=True,**kwargs)
        self.labels = dict()

        try:
            log.debug("Try bulk labels loading.")
            self.labels = load_file(
                os.path.join(
                   self.metadata["path"],"labels.yaml"
                   )
                    )
        except FileNotFoundError:
            log.debug("No labels found in the path.")
            labels = kwargs.pop("labels",None)
            if labels is None:
                self.metadata["dimensions"] = kwargs.get("dimensions",None)
                labels = self.metadata["dimensions"]
            self.labels = dict()
            self.format_labels(labels)

        try:
            self.groupings = load_file(
                os.path.join(
                    self.metadata["path"],"groupings.yaml"
                    )
                    )
        except FileNotFoundError:
            self.groupings = kwargs.pop("groupings",dict())

        self.extension = kwargs.get("extension",None)
        
        self.part_settings = kwargs.get("parts",dict())
        super().__init__()

    def available_parts(self,extension=None):
        """
        List the available parts in the current path.

        Parameters
        ----------
        extension : str, optional
            Extension of the files to look for.
            If not provided, all files are listed.

        Returns
        -------
        list
            List of available parts
        """
        if extension is None:
            extension = self.extension
            
        if extension is None:
            return os.listdir(self.path)
        files = os.listdir(self.path)
        parts = [
            Path(file).stem for file in files if file.endswith(extension)
            ]
        return parts
    
    def extract_path(self,update=False,**kwargs):
        """
        Extract the path from the kwargs.

        Valid formats are:
        - path
        - mrio_path
        - file
        - data_path
        - table/year/version
        In absence of explicit path, the current directory is used.

        Parameters
        ----------
        update : bool, optional
            Whether to update the path attribute.
            If a path is already set, it is not overridden.
        """
        if "path" in kwargs:
            self.path = kwargs.pop("path")
        elif "mrio_path" in kwargs:
            self.path = kwargs.pop("mrio_path")
        elif "data_path" in kwargs and update:
            self.path = kwargs.pop("data_path")
        elif "file" in kwargs and update:
            self.path = pathlib.Path(kwargs.pop("file")).parent
        elif "path" in self.__dict__.keys() and not update:
            log.debug("No path provided.")
            self.path = "."

        if "table" in kwargs and "year" in kwargs and "version" in kwargs:
            self.path = os.path.join(
                self.path,
                kwargs.pop("table"),
                str(kwargs.pop("year")),
                kwargs.pop("version"))
        
        self.labels_path = kwargs.get("labels_path",
                                      self.__dict__.get("labels_path",self.path)
                                      )

        #Store paths in metadata
        self.metadata["path"] = self.path
        self.metadata["labels_path"] = self.labels_path

    def format_labels(self,labels):
        """
        Treat the label information

        If labels are provided as dict, they are kept as is.
        If labels are provided as string, they are loaded from the labels_path folder.
        The labels are stored as a dict of lists.
        """
        if labels is None:
            log.debug("No labels provided.")
            return
        if isinstance(labels,dict):
            self.labels = labels
        if isinstance(labels,str):
            labels = [labels]
            
        for label in labels:
            if isinstance(label,list):
                for sublabel in label:
                    self.format_labels(sublabel)
            elif label not in self.labels.keys():
                log.debug("Load labels: "+label)
                self.labels[label] = load_file(
                    os.path.join(self.labels_path,label),dtype=str
                )
                
    def load_mrio(
            self,
            **kwargs
    ):
        """
        Load MRIO data from explicit parameters.

        If parameters are provided, they overload the corresponding instance attributes.
        """
        self.update_attributes(**kwargs)
    
    def get_file(self,**kwargs):
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
        
        instructions = self.metadata.get("instructions",None)

        #Find file
        if "file" in kwargs and kwargs.get("file")!=instructions:
            #Ignore the file argument if it is the same as the one in the instructions
            return kwargs.pop("file")
        if "file_name" in kwargs:
            return os.path.join(self.path,kwargs.pop("file_name"))
        if "name" in kwargs:
            return os.path.join(self.path,kwargs.pop("name"))
        if self.file is None:
            log.error("No file provided: please provide a full file or a file name.")
            raise ValueError("No file provided: please provide a full file or a file name.")
        return self.file
        

    def load_part(
            self,
            **kwargs
    ):
        """
        Load a Part from explicit parameters.

        Parameters provided as arguments overload the corresponding instance attributes.

        Returns
        -------
        dict
            Data for creating the Part object

        Raises
        ------
        FileNotFoundError
            If no file nor name argument is provided
        """
        #Initialize Part specific parameters
        part_data = {
            "metadata" : dict()
        }

        #Update loader parameters
        self.update_attributes(**kwargs)

        file = self.get_file(**kwargs)

        
        loader_kwargs = kwargs.pop("loader_kwargs",self.loader_kwargs)

        name = kwargs.pop("name",os.path.splitext(os.path.basename(file))[0])

        log.info(f"Load part {name} from {file}")
        
        if name in self.part_settings:
            #Load preset settings
            part_settings = self.part_settings[name]
            kwargs.update(part_settings)
        
        part_data["data"] = load_file(file,
                                      extension=self.extension,**loader_kwargs)

        labels = []
        dimensions = kwargs.get("dimensions",
                                self.metadata.get("dimensions",
                                part_data["data"].shape)
        )
        if dimensions is None:
            dimensions = part_data["data"].shape
        for dim in dimensions:
            labels.append(self._get_labels(dim))

        part_data["metadata"] = self.metadata
        part_data["name"] = name
        part_data["metadata"]["path"] = self.path
        part_data["metadata"]["loader_kwargs"] = loader_kwargs
        part_data["labels"] = labels
        part_data["groupings"] = kwargs.get("groupings",self.groupings)       
        return part_data
    
    def _get_labels(self,l):
        """Find the labels fitting an axis with a given shape
            
        If no fitting label is found, data are labelled numerically

        Parameters
        ----------
        l : int, list or str
            Length of the data dimension or name of the dimensions.

        Returns
        -------
        dict of str:list of str
            Labels of the axis.

        """
        if isinstance(l,list):
            output = dict()
            try:
                for label in l:
                    output.update(self._get_labels(label))
                return output
            except IndexError:
                return {"0":l}
        if isinstance(l,str):
            if l not in self.labels.keys():
                self.format_labels(l)
            return {l:self.labels[l]}
        if not isinstance(l,int):
            log.error(f"Invalid dimension type {type(l)}")
            raise TypeError(f"Invalid dimension type {type(l)}")
        if l==1:
            return {0:"all"}
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
        return {"0":[i for i in range(l)]}