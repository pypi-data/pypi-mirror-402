"""Routines for loading from Excel"""

from mrio_toolbox.utils.loaders._np_loader import load_file
from mrio_toolbox.utils.loaders._parameter_loader import Parameter_Loader
from mrio_toolbox.utils import converters
import os
import logging

log = logging.getLogger(__name__)

class Pandas_Loader(Parameter_Loader):
    """
    Class for loading MRIO data through Pandas.

    The `Pandas_Loader` class extends the `Parameter_Loader` class to provide 
    functionality for loading MRIO data from `.xlsx` and `.csv` files. It uses 
    the Pandas library to read the data and extract metadata, labels, and parts.

    Instance variables
    ------------------
    groupings : dict
        Groupings for the labels, defining higher-level aggregations.
    labels : dict
        Explicit dictionary of labels for the MRIO data.
    dimensions : list of int
        List of label names.
    path : str
        Path to the data file.
    labels_path : str
        Path to the labels file.
    parts : dict
        Parts to load, with specific settings.
    loader_kwargs : dict
        Parameters passed to the underlying Pandas loader (e.g., `read_excel`, `read_csv`).

    Methods
    -------
    load_part(**kwargs):
        Load a specific Part from explicit parameters.

    """
    
    def __init__(
            self,
            **kwargs
            ):
        """
        Initialize a Pandas_Loader object.

        Parameters
        ----------
        loader_kwargs : dict, optional
            Parameters passed to the underlying loader.
               - .xlsx: pandas.read_excel
               - .csv: pandas.read_csv
        groupings : dict, optional
            Aggregation on labels
        labels : dict, optional
            Explicit dictionary of labels.
        dimensions : list of int, optional
            List of label names.
        path : str, optional
            Path to the data
            The following paths are recognized:
            - path
            - mrio_path
            - file
            - data_path
            - table/year/version
        labels_path : str, optional
            Path to the labels files
        parts : dict, optional
            Parts to load, with specific settings
        **kwargs : dict
            Metadata for the MRIO data.
            MRIO metadata are passed to associated parts.

        """
        super().__init__(**kwargs)

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

        autodetect_labels = True
        if any(key in loader_kwargs for key in ["index_col", "header"]):
            #If labels are explicitly provided, do not autodetect
            autodetect_labels = False

        
        return converters.pandas.make_part(load_file(file,
                                     **loader_kwargs,
                                     extension=self.extension,
                                     pandas=True),
                                     name=name,
                                     label_detection=autodetect_labels,
                                     **kwargs)