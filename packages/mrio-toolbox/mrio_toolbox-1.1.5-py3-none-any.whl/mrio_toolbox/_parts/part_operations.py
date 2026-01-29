"""Basic operations on Parts

Because of my inexperience in software development,
I only created this file lately.

I will move the relevant methods from the _Part class to this file
at a later point.
"""

def reformat(part,new_dimensions):
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
    def formatting_iteration(part,new_dimensions):
        if part.get_dimensions() == new_dimensions:
            return part
        for i,dim in enumerate(part.get_dimensions()):
            if dim != new_dimensions[i]:
                part = part.combine_axes(i,i+len(new_dimensions[i])-1)
                return formatting_iteration(part,new_dimensions)
    developed = part.develop(squeeze = False)
    return formatting_iteration(developed,new_dimensions)


