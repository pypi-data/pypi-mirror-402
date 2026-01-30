"""
Routines for checking and extending file paths to avoid overwriting existing files.
"""
import os
import re

def check_path(path):
    """
    Extend the name path to avoid overwriting existing files.

    Parameters
    ----------
    path : str
        Path currently selected
    """

    i = 1
    while os.path.isfile(path):
        base_path, ext = os.path.splitext(path)
        
        # Remove existing _number suffix if present
        base_path = re.sub(r'_\d+$', repl, base_path)

        path = f"{base_path}_{i}{ext}"
        i += 1
        
    return path

def repl(match):
    '''
    Condition for replacing the _number suffix
    
    If the suffix as 2 or 4 digits, we keep it and add version number after
    2 digits can be used to identify MRIO tables, 4 digits for years
    '''
    s = match.group()
    return s if len(s) == 3 or len(s) == 5 else ""