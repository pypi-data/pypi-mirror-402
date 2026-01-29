import pandas as pd
from IPython.display import display
import numpy as np

class Utils:
    @staticmethod
    def convert_dataframe(data: list, columns: list[str]) -> None:
        """
        Converts a list of data into a pandas DataFrame, optionally transposes it,
        and displays the result.

        Args:
            data (list): List of rows, where each row is a list of values.
            columns (list[str]): List of column names for the DataFrame (excluding the first 'Column' label).

        Returns:
            None: The function displays the DataFrame using display().
        """
        columns_names = ["Column"] + columns
        dataframe = pd.DataFrame(data, columns=columns_names)
        display(dataframe.head(len(dataframe)))