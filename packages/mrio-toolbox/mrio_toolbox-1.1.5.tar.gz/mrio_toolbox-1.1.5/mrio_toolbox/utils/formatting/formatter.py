"""
Format MRIO tables to meet specific requirements
"""


import os
import sys
import yaml
import numpy as np
import logging as log

#from mrio_toolbox import MRIO

log = log.getLogger(__name__)

def reallocate_negatives(mrio,
               final_demand="y",
               value_added="va",
               category_fd=None,
               category_va=None,
               destination_fd = -1,
               destination_va = -1,
               from_fd=True,
               from_va=True,
               validate_intermediates=False):
    """Reallocate negative values between final demand and value added parts
    
    Negative values might interfere with some MRIO operation.
    This function reallocates negative values from final demand to value added parts and vice versa.

    Parameters
    ----------
    mrio : MRIO instance
        Instance on which the operation applies
    final_demand : str, optional
        Name of the final demand part. The default is "y"
    value_added : str, optional
        Name of the value added part. The default is "va"
    origin_fd : list of str, optional
        List of final demand labels that are transferable. The default is None.
        If no label is given, all negative values are transferred.
    origin_va : list of str, optional
        List of value added labels that are transferable. The default is None.
        If no label is given, all negative values are transferred.
    destination_fd : str, optional
        Final demand categories to which negative values are transferred. 
        The default is -1, i.e. the last final demand category.
    destination_va : str, optional
        Value added category to which negative values are transferred. 
        The default is -1, i.e. the last value added category.
    from_fd : bool, optional
        Whether to reallocate from final demand to value added. The default is True.
    from_va : bool, optional
        Whether to reallocate from value added to final demand. The default is True.
    validate_intermediates : bool, optional
        Whether to double check the validity of intermediate use,
        i.e., that intermediate inputs demand do not exceed the total output.
        See the corresponding function's documentation

    """
    if final_demand not in mrio.parts.keys():
        log.error(f"Part {final_demand} not found in MRIO. Cannot reallocate final demand.")
        raise ValueError(f"Part {final_demand} not found in MRIO. Cannot reallocate final demand.")
    if value_added not in mrio.parts.keys():
        log.error(f"Part {value_added} not found in MRIO. Cannot reallocate final demand.")
        raise ValueError(f"Part {value_added} not found in MRIO. Cannot reallocate final demand.")

    log.info(f"Reallocate final values between {final_demand} and {value_added}")

    fd = mrio.parts[final_demand]
    va = mrio.parts[value_added]

    ###Extract the negative value added and replace them by
    if from_fd:
        log.info("Remove negatives from the final demand")
        selectable_fd = fd
        #Select transferrable data
        if category_fd is not None and fd.axes[1].ndim==2:
            selectable_fd = fd["all",["all",category_fd]]
        
        loc_negs_fd = np.where(selectable_fd.data<0)
        neg_fd = selectable_fd.data[loc_negs_fd]
        #Sum over importing countries and final demand categories
        selectable_fd.data[loc_negs_fd] = 0
        if category_fd is not None and fd.axes[1].ndim==2:
            fd["all",["all",category_fd]] = selectable_fd

        
    if from_va:
        log.info("Remove negatives from the value added")
        selectable_va = va
        #Select transferrable data
        if category_va is not None:
            if selectable_va.ndim==1:
                log.warning("The value added part is aggregated. The argument 'category_va' will be ignored.")
            else:
                selectable_va = va[category_va]

        loc_negs_va = np.where(selectable_va.data<0)
        neg_va = selectable_va.data[loc_negs_va].copy()
        selectable_va.data[loc_negs_va] = 0
        if neg_va.ndim>1:
            #Sum over va categories if needed
            neg_va = neg_va.sum(axis=0)

        if category_va is not None and selectable_va.ndim>1:
            va[category_va] = selectable_va
    
    ###Add the negative values to the other part

    if from_fd:
        log.info("Add final demand negatives to the value added")
        for value,position in zip(neg_fd,loc_negs_fd[0]):
            if va.ndim==2:
                va[[destination_va],[position]] += -value
            else:
                va[[position]] += -value

    if from_va:
        log.info("Add value added negatives to the final demand")

        #Negative value added are only added to the domestic final demand
        for value,position in zip(neg_va,loc_negs_va[-1]):
            country = position // fd.axes[0].multipliers[fd.axes[0].dimensions[0]]
            if fd.axes[1].ndim==1:
                fd[[[position],[country]]] += -value
            else:
                fd[position,[[country],[destination_fd]]] += -value
    
    if validate_intermediates:
        mrio.validate_intermediates()

def adjust_intermediates(mrio,
                           final_demand = "y",
                           inter_industry = "t",
                           destination = -1,
                           save_gross_output=True):
    """
    Ensures that intermediate use is always less than gross output

    This is required to avoid negative value added as residual.
    The domestic final demand is adjusted to make sure gross output is larger than intermediate use.

    Parameters
    ----------
    mrio : MRIO instance
        Instance on which the operation applies
    final_demand : str, optional
        Name of the final demand part. The default is "y"
    inter_industry : str, optional
        Name of the inter-industry part. The default is "t"
    destination : str, optional
        Final demand categories to which negative values are transferred. 
        The default is -1, i.e. the last final demand category.
    """
    if final_demand not in mrio.parts.keys():
        log.error(f"Part {final_demand} not found in MRIO. Cannot readjust intermediates.")
        raise ValueError(f"Part {final_demand} not found in MRIO. Cannot readjust intermediates.")
    if inter_industry not in mrio.parts.keys():
        log.error(f"Part {inter_industry} not found in MRIO. Cannot readjust intermediates.")
        raise ValueError(f"Part {inter_industry} not found in MRIO. Cannot readjust intermediates.")
    
    log.info(f"Adjust intermediates in parts {inter_industry} and {final_demand}")
    fd = mrio.parts[final_demand]
    t = mrio.parts[inter_industry]
    original_x = t.sum(1) + fd.sum(1)
    residual = original_x - t.sum(0)
    
    loc_negs = np.where(residual.data<0)
    negs = residual.data[loc_negs]

    for value,position in zip(negs,loc_negs[-1]):
        country = position // fd.axes[0].multipliers[fd.axes[0].dimensions[0]]
        if fd.axes[1].ndim==1:
            fd[[[position],[country]]] += -value
        else:
            fd[position,[[country],[destination]]] += -value

    if save_gross_output:
        if not isinstance(save_gross_output,str):
            save_gross_output = "x"
        mrio.parts[save_gross_output] = t.sum(1) + fd.sum(1)

def fill_empty_rows(
        mrio,
        final_demand = "y",
        inter_industry = "t",
        target = -1,
        fill_value=0.5,
        save_gross_output = True
):
    """
    Insert fill values in empty rows

    This avoids any issue with missing data (e.g. for the Leontief inversion)
    The fill value is inserted on the diagonal of empty rows in the inter-industry matrix
    and as domestic consumption for final demand, 
    such that it does not interfere with the rest of the table.
    The fill_value 1 must be avoided, as it conflicts with the Leontief inversion.
    Note that the fill value slightly changes the aggregate.
    """
    if inter_industry not in mrio.parts.keys():
        log.error(f"Part {inter_industry} not found in MRIO. Cannot fill the empty rows.")
        raise ValueError(f"Part {inter_industry} not found in MRIO. Cannot fill the empty rows.")
    if final_demand not in mrio.parts.keys():
        log.error(f"Part {final_demand} not found in MRIO. Cannot fill the empty rows.")
        raise ValueError(f"Part {final_demand} not found in MRIO. Cannot fill the empty rows.")
    
    log.info(f"Fill empty rows in parts {inter_industry} and {final_demand}")
    t = mrio.parts[inter_industry]
    y = mrio.parts[final_demand]

    x = t.sum(1) + y.sum(1)
    zeros = np.where(x.data==0)
    sectors = t.axes[0].labels[t.axes[0].dimensions[1]]
    for zero in zeros[0]:
        
        t[[zero],[zero]] = fill_value
        country = zero // y.axes[0].multipliers[y.axes[0].dimensions[0]]
        sector = sectors[zero % y.axes[0].multipliers[y.axes[0].dimensions[0]]]
        log.info(f"Fill empty row {zero}: {mrio.countries[country]}, {sector}")
        if y.axes[1].ndim==1:
            y[[zero],[country]] = fill_value
        else:
            y[[zero],[[country],[target]]] = fill_value

    if save_gross_output:
        if not isinstance(save_gross_output,str):
            save_gross_output = "x"
        mrio.parts[save_gross_output] = t.sum(1) + y.sum(1)

def balance_va(
        mrio,
        final_demand="y",
        value_added="va",
        inter_industry="t",
        save_as_category=False,
        category="residual"
):
    """Fill residuals in the value added part.
    
    This makes sure the balance is respected.
    If save_as_category is False, the value_added part is overwritten
    in order to balance the table.
    Otherwise, the residuals are stored in the given category.
    If a non-existing category is provided, it is added to the existing va labels.

    Parameters
    ----------
    mrio : MRIO instance
        The MRIO instance to format.
    final_demand : str
        The name of the final demand part.
    inter_industry : str
        The name of the inter-industry part.
    value_added : str
        The name of the value added part.
    save_as_category : bool
        Whether to save the residuals in a category.
        Otherwise, the value added is defined as the full residual
    category : str
        Name of the category under which the residual is stored.
        If the category does not exist, it is created.
        If the value added was flat, a va_labs dimension is added.
    """
    if inter_industry not in mrio.parts.keys():
        log.error(f"Part {inter_industry} not found in MRIO. Cannot fill the empty rows.")
        raise ValueError(f"Part {inter_industry} not found in MRIO. Cannot fill the empty rows.")
    if final_demand not in mrio.parts.keys():
        log.error(f"Part {final_demand} not found in MRIO. Cannot fill the empty rows.")
        raise ValueError(f"Part {final_demand} not found in MRIO. Cannot fill the empty rows.")
    
    log.info(f"Balance value added in part {value_added}")
    t,y = mrio.parts[inter_industry], mrio.parts[final_demand]

    x = t.sum(1) + y.sum(1)

    if not save_as_category:
        log.info(f"Write balanced value added in part {value_added}")
        mrio.parts[value_added] = x - t.sum(0)
        return
    
    log.info(f"Save residuals in category '{category}' of part {value_added}")
    if value_added not in mrio.parts.keys():
        log.error(f"Part {value_added} not found in MRIO. Cannot fill the empty rows.")
        raise ValueError(f"Part {value_added} not found in MRIO. Cannot fill the empty rows.")
    va = mrio.parts[value_added]
    residual = x - t.sum(0) - va.sum(0)

    #Adjust va dimensions
    if va.ndim == 1:
        mrio.add_dimensions({
            "va_labs" : ["original_va", category]
        })
        new_va = mrio.new_part(
            name="balanced_va",
            data = np.zeros((2,va.shape[0])),
            dims = ["va_labs", va.axes[0].dimensions]
        )
        new_va["original_va"] = va
    
    if category not in va.axes[0].labels[va.axes[0].dimensions[0]]:
        va_labs = va.axes[0].dimensions[0]
        mrio.add_labels([category], va_labs)
        va = mrio.parts[value_added] #Reload va with new labels
    
    va[category] += residual

def compute_technical_coefficients(mrio,
                                   name="a",
                                   inter_industry="t",
                                   final_demand = "y"
                                   ):
    """
    Compute the technical coefficients matrix.

    This is the inter-industry matrix normalized by the gross output.

    Parameters
    ----------
    mrio : MRIO
        The MRIO instance to format.
    name : str
        The name under which the technical coefficients matrix will be stored.
        The default is "a".
        If no name is provided, the technical coefficients matrix is not stored and directly returned.
    inter_industry : str
        The name of the inter-industry matrix stored.
        The default is "t".
    final_demand : str
        The name of the final demand matrix stored.
        The default is "y".
    """
    if inter_industry not in mrio.parts.keys():
        log.error(f"Part {inter_industry} not found in MRIO. Cannot compute the technical coefficients matrix.")
        raise ValueError(f"Part {inter_industry} not found in MRIO. Cannot compute the technical coefficients matrix.")
    t = mrio.parts[inter_industry]

    if final_demand not in mrio.parts.keys():
        log.error(f"Part {final_demand} not found in MRIO. Cannot compute the technical coefficients matrix.")
        raise ValueError(f"Part {final_demand} not found in MRIO. Cannot compute the technical coefficients matrix.")
    y = mrio.parts[final_demand]
    x = t.sum(1) + y.sum(1)
    x.data[x.data==0] = 1 #Avoid division by zero

    if not name:
        return t.mul((1/x).diag())
    
    mrio.parts[name] = t.mul((1/x).diag())

def compute_leontief(mrio,
                     name="l",
                     technical_coefficients_matrix="a",
                     **kwargs):
    """
    Compute the Leontief inverse matrix.

    If the technical coefficients matrix is not provided, it will be computed.
    
    Parameters
    ----------
    mrio : MRIO
        The MRIO instance to format.
    name : str
        The name under which the Leontief inverse matrix will be stored.
    technical_coefficients_matrix : str
        The name of the technical coefficients matrix to use.
        If the matrix does not exist, it is computed and saved under the corresponding name.
        If False, the technical coefficients matrix is computed but not stored.
    kwargs : dict
        Additional keyword arguments for the technical coefficients matrix computation.
    """
    if not technical_coefficients_matrix:
        a = compute_technical_coefficients(mrio,
                                            name=technical_coefficients_matrix,**kwargs)
    else:
        compute_technical_coefficients(mrio, name= technical_coefficients_matrix,
                                            **kwargs)
        a = mrio.parts[technical_coefficients_matrix]
    mrio.parts[name] = a.leontief_inversion()


def preprocess(
        mrio, 
        reallocate_negatives = False,
        adjust_intermediates = False,
        fill_empty_rows = False,
        balance_va = False,
        group_parts = False, 
        final_demand="y",
        inter_industry="t",
        value_added="va",
        compute_technical_coefficients = False,
        compute_leontief = False,
        save = False
):
    """
    Preprocess MRIO data.

    The following operations are available:
        - reallocate_negatives:
            Allocate negative final demand and value added
            to the opposite member
        - adjust_intermediates:
            Adjust intermediate consumption values to avoid negative value added.
        - fill_empty_rows:
            Add empty rows in the MRIO tables, to avoid computational errors.
        - balance_va:
            Balance the table by adding residuals to the value added.
        - group_parts:
            Group parts in the MRIO tables.
        - compute_technical_coefficients:
            Compute the technical coefficients matrix.
        - compute_leontief:
            Compute the Leontief inverse matrix.

    Parameters
    ----------
    mrio : MRIO instance
        MRIO instance to preprocess.
    reallocate_negatives : dict
        Parameters for reallocating negative values.
    adjust_intermediates : dict
        Parameters for adjusting intermediate values.
    fill_empty_rows : dict
        Parameters for filling empty rows.
    balance_va : dict
        Parameters for balancing value added.
    group_parts : dict
        Parameters for grouping parts.
        Must be set as a dictionary:
            part_name : parameters for the sum operator (axes, dimension)
    final_demand : str
        Name of the final demand matrix.
    inter_industry : str
        Name of the inter-industry matrix.
    value_added : str
        Name of the value added matrix.
    compute_technical_coefficients : bool or dict
        Whether to compute the technical coefficients matrix.
        If dict, optional parameters for the computation.
    compute_leontief : bool or dict
        Whether to compute the Leontief inverse matrix.
        If dict, optional parameters for the computation.
    save : dict
        Parameters to save the processed MRIO instance.
        Parameters for the saving process.
    """
    log.info("Start formatting MRIO")

    if group_parts:
        for part, args in group_parts.items():
            log.info(f"Group part '{part}' over {args}")
            mrio.parts[part] = mrio.parts[part].sum(**args)

    if reallocate_negatives:
        if isinstance(reallocate_negatives, bool):
            reallocate_negatives = dict()
        mrio.reallocate_negatives(
            final_demand=final_demand,
            value_added=value_added,
            **reallocate_negatives
        )

    if fill_empty_rows:
        if isinstance(fill_empty_rows, bool):
            fill_empty_rows = dict()
        mrio.fill_empty_rows(
            final_demand=final_demand,
            inter_industry=inter_industry,
            **fill_empty_rows
        )
    
    if adjust_intermediates:
        if isinstance(adjust_intermediates, bool):
            adjust_intermediates = dict()
        mrio.adjust_intermediates(
            final_demand=final_demand,
            inter_industry=inter_industry,
            **adjust_intermediates
        )
    
    if balance_va:
        if isinstance(balance_va, bool):
            balance_va = dict()
        mrio.balance_va(
            final_demand=final_demand,
            inter_industry=inter_industry,
            value_added=value_added,
            **balance_va
        )

    if compute_technical_coefficients:
        if isinstance(compute_technical_coefficients, bool):
            compute_technical_coefficients = dict()
        mrio.compute_technical_coefficients(
            inter_industry=inter_industry,
            final_demand=final_demand,
            **compute_technical_coefficients
        )
    
    if compute_leontief:
        if isinstance(compute_leontief, bool):
            compute_leontief = dict()
        mrio.compute_leontief(
            inter_industry=inter_industry,
            final_demand=final_demand,
            **compute_leontief
        )
    
    if save:
        if isinstance(save, bool):
            save = dict()
        mrio.save(**save)

def rename_part(mrio,old_name,new_name):
    """Change the name of an MRIO part"""
    if old_name not in mrio.parts.keys():
        raise KeyError(f"Part '{old_name}' not found in MRIO. Cannot rename it to '{new_name}'.")
    log.info(f"Rename part '{old_name}' to '{new_name}'")
    mrio.parts[new_name] = mrio.parts.pop(old_name)
    mrio.parts[new_name].name = new_name

def rename_parts(mrio,renaming_dict):
    """Change the name of a collection of MRIO parts"""
    for old_name,new_name in renaming_dict.items():
        rename_part(mrio,old_name,new_name)
