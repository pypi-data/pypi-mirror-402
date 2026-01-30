"""
Routines for converting between Pandas DataFrames and Parts objects.
"""

import pandas as pd
import numpy as np

def to_pandas(part):
    """Return the current Part object as a Pandas DataFrame
    
    Only applicable to Parts objects with 1 or 2 dimensions.
    """
    if part.ndim==2:
        return pd.DataFrame(part.data,
                            index = part.axes[0].label(True),
                            columns = part.axes[1].label(True))
    if part.ndim==1:
        return pd.DataFrame(part.data,index = part.axes[0].label(True))
    return to_pandas(part.flatten())
                                
    
def make_part(df,name="from_df",
                label_detection=False,
                **kwargs):
    """Load a Part object from a Pandas DataFrame
    
    Parameters
    ----------
    df : DataFrame
        DataFrame to load
    label_detection : bool, optional
        Automatically detect labels, by default False
        If True, the DataFrame is scanned to detect labels (defined as non-numeric data)
    name : str, optional
        Name of the data variable to load, by default None.
        This can be left empty if there's a single variable in the DataFrame.
    
    Returns
    -------
    dict    
        Data required to create the Part object
    """
    part_data = dict()

    if label_detection:
        df = autodecode_labels(df)
    else:
        df = analyse_df(df)

    part_data["data"] = df.to_numpy()
    ndim = df.ndim

    labels = []
    if ndim == 1:
        labels.append(convert_labels(df.index))
    else:
        labels.append(convert_labels(df.index))
        labels.append(convert_labels(df.columns))
    labels = disambiguate_labels(labels)
    part_data["labels"] = labels
    part_data["groupings"] = kwargs.pop("groupings",dict())
    part_data["metadata"] = kwargs.pop("metadata",dict())
    part_data["name"] = name
    for key in kwargs:
        part_data["metadata"][key] = kwargs[key]
    return part_data

def autodecode_labels(df):
    """Automatically detect the labels from a DataFrame
    
    This is done by indentifying the indices and columns
    with non-numeric values.
    """
    def test_selection(df,row,col):
        """Test if a selection is numeric"""
        try:
            for col in df.iloc[row:,col]:
                pd.to_numeric(col)
            return True
        except ValueError:
            return False

    def try_reduce(df,row,col):
        """Try reducing the rectangle to the right or down"""
        if test_selection(df,row+1,col):
            return row+1,col
        elif test_selection(df,row,col+1):
            return row,col+1
        else:
            return row+1,col+1
        
    def try_expand(df,row,col):
        """Try expanding the rectangle to the left or up"""
        if not test_selection(df,row+1,col):
            return row+1,col
        elif not test_selection(df,row,col+1):
            return row,col+1
        else:
            return row, col

    def find_rectangle(df):
        """Find the largest rectangle with only numeric data"""
        row = 0
        col = 0
        while not test_selection(df,row,col):
            row,col = try_reduce(df,row,col)
        while not test_selection(df,row,col):
            #After the first while loop, we found only numeric data
            #We now expand to the top and the left
            #To make sure we didn't crop numerical data
            row,col = try_expand(df,row,col)
        return row,col
    
    #First, we find the largest rectangle with only numeric data
    row,col = find_rectangle(df)

    #And we remove potential nan axes and ensure types are ok
    data = pd.DataFrame(
        data=df.iloc[row:,col:],
        dtype=np.float64)

    #We count Nan axes as they offset label names
    row_offset = data.map(
        np.isnan
    ).all(1).sum()
    col_offset = data.map(
        np.isnan
    ).all(0).sum()

    
    data = data.dropna(axis=0,how="all")
    data = data.dropna(axis=1,how="all")


    #Then, we build the labels
    if col>0:
        col_names = df.iloc[:row,col-1+col_offset].to_list()
        if row > 1:
            labels = []
            sel = df.iloc[:row,col:].transpose()
            for column in sel.columns:
                labels.append(sel[column].dropna().unique())
            columns = pd.MultiIndex.from_product(
                labels,
                names = col_names)
        else:
            columns = pd.Index(
                df.iloc[
                    :row,col:
                    ].values.flatten(),
                name = col_names[0]
            )
        
    else:
        columns = None
    if row > 0:
        index_names = df.iloc[row-1+row_offset,:col].to_list()
        if col > 1:
            labels = []
            sel = df.iloc[row+row_offset:,:col]
            for column in sel.columns:
                labels.append(
                    list(sel[column].dropna().unique())
                )
            index = pd.MultiIndex.from_product(
                labels,
                names = index_names)
        else:
            index = pd.Index(
                list(
                    df.iloc[
                row:,:col
                ].values.flatten()
                ),
                name = index_names[0]
            )
    else:
        index = None

    #We build the formatted DataFrame
    output = pd.DataFrame(
        data = data.values,
        columns=columns,
        index = index
          )
    
    return output

def analyse_df(df):
    """Analyse the DataFrame to ensure the indices and columns are well formatted.

    This function ensures that all categorical columns are treated as indices,
    and that all numeric columns are treated as data.
    """
    numeric_index = False
    if isinstance(df.index,pd.RangeIndex):
        numeric_index = True

    df = df.reset_index()
    if numeric_index:
        #If the index was numeric, we drop it
        #to avoid inserting it in the data
        df = df.drop(columns=["index"])
        

    indices = []
    for col in df.columns:
        try:
            pd.to_numeric(df[col])
        except ValueError:
            indices.append(col)

    df = df.set_index(indices)

    return df

def convert_labels(index):
    """Convert a Pandas Index to a dictionary of labels
    
    Parameters
    ----------
    index : Index
        Pandas Index to convert
    """
    output = []
    if isinstance(index,pd.MultiIndex):
        for i in range(index.nlevels):
            name = index.names[i]
            if name is None:
                name = f"level_{i}"
            output.append(
                {name : list(index.levels[i].values)}
            )
        return output
    if index.name is None:
        return [{str(0):list(index.array)}]
    return [{index.name:list(index.array)}]

def disambiguate_labels(labels):
    """Disambiguate the labels

    This allow solving labels ambiguity if the name was incorrectly loaded.
    
    Parameters
    ----------
    index : dict of str:list of str
        New index to disambiguate
    labels : list of str:list of str
        List of labels to disambiguate
    """
    ordered = []
    cleared = dict()
    flat_labels = [label_dim for label in labels for label_dim in label]
    values = []
    for label in labels:
        ordered.append([])
        for level in range(len(label)):
            name,value = list(
                label[level].keys()
            )[0],list(
                label[level].values()
            )[0]
            if name not in cleared.keys():
                if value in values:
                    #We have a duplicate
                    #We use the first occurrence as reference
                    ref_name = cleared.keys()[list(cleared.values()).index(value)]
                    ordered[-1].append(
                        {ref_name:value}
                    )
                    cleared[name] = value
            ordered[-1].append(label[level])
            cleared[name] = value
            values.append(value)

    return ordered