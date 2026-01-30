"""
Report Formatting Utilities Module

This module provides utility functions for formatting data into standardized report 
formats expected by AltaSigma. It includes functions for converting
common data structures like pandas DataFrames into properly structured report data.
"""

from typing import Dict, Union, List
import pandas as pd 
import json


def dataframe_to_table_report_data(df: pd.DataFrame) -> Dict[str, List[Dict[str, Union[str, float, bool]]]]:
    """
    Convert a pandas DataFrame to the JSON format expected for table reports.
    
    This function takes a pandas DataFrame and transforms it into a standardized
    dictionary format that can be used directly in AltaSigma table reports. It
    handles proper serialization of various data types including dates (using ISO format).
    
    Args:
        df (pd.DataFrame): The pandas DataFrame to convert to report data.
        
    Returns:
        Dict[str, List[Dict[str, Union[str, float, bool]]]]: A dictionary with a 'data' key
            containing a list of row dictionaries, where each dictionary represents
            a row from the DataFrame with column names as keys.
        
    Note:
        Dates and timestamps are automatically converted to ISO format strings (YYYY-MM-DDTHH:MM:SS.sss).
        Complex data types that aren't natively supported by JSON may need pre-processing
        before passing the DataFrame to this function.
    """
    return {"data": json.loads(df.to_json(orient="records", date_format="iso"))}
