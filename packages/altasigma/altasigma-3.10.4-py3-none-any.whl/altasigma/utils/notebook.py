"""
Notebook Utility Module

This module provides utilities for adapting output based on the execution environment,
specifically distinguishing between Jupyter notebooks and other Python environments.
It allows code to display rich content in notebooks while falling back to plain text
in terminal or script environments.
"""

from IPython import get_ipython
from IPython.display import display, HTML, clear_output

def is_in_notebook() -> bool:
    """
    Detect whether the code is running in a Jupyter notebook environment.
    
    This function examines the IPython shell type to determine if the code
    is running in a Jupyter notebook, qtconsole, terminal IPython, or standard
    Python interpreter.
    
    Returns:
        bool: True if running in a Jupyter notebook or qtconsole,
              False if running in terminal IPython, standard Python interpreter,
              or any other environment.
              
    Note:
        This detection is based on the IPython shell class name, which may
        change in future IPython versions.
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


def display_or_print(msg_notebook, msg_other):
    """
    Display content appropriately based on the execution environment.
    
    This function detects the current environment and shows either rich content
    in notebooks or plain text in other environments. It helps create code that
    works well in both interactive and non-interactive contexts.
    
    Args:
        msg_notebook: Content to display in a notebook environment, typically
                     an IPython.display object like HTML or Image.
        msg_other: Content to print in non-notebook environments, typically
                  a string.
    """
    if is_in_notebook():
        display(msg_notebook)
    else:
        print(msg_other)
