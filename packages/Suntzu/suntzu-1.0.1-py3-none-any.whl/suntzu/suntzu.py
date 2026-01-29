import pandas as pd

import os

from .cleaning import Cleaning
from .statistics import Statistics


class Suntzu_Dataframe(Cleaning, Statistics):
    pass
def read_file(path: str, **kwargs) -> Suntzu_Dataframe:
    """
    Reads a file from disk and returns its contents as a Suntzu_Dataframe.

    The file format is automatically inferred from the file extension and
    loaded using the appropriate pandas reader.

    Args:
        path (str): Path to the file to be read.
        **kwargs: Additional keyword arguments passed to the corresponding
            pandas read function.

    Returns:
        Suntzu_Dataframe: A Suntzu_Dataframe containing the loaded data.

    Raises:
        ValueError: If the file path is invalid or the file format
            is not supported.

    Examples:
        >>> import suntzu as sz
        >>> df = sz.read_file("data.csv")
        >>> df = sz.read_file("data.parquet")
    """
    if not os.path.isfile(path):
        raise ValueError("Invalid file path.")

    extension = os.path.splitext(path)[1]
    valid_extensions = {
        ".csv": pd.read_csv,
        ".json": pd.read_json,
        ".xlsx": pd.read_excel,
        ".xml": pd.read_xml,
        ".feather": pd.read_feather,
        ".parquet": pd.read_parquet
    }
    
    if extension not in valid_extensions:
        raise ValueError(f"Unsupported file format for {path}. Supported formats: CSV, Parquet, JSON, Excel, XML and Feather.")
    
    return Suntzu_Dataframe(valid_extensions[extension](path, **kwargs))

