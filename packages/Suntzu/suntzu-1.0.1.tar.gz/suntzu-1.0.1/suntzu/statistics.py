import pandas as pd 
import numpy as np

from .getter import Getter
from .utils import Utils
from .errors import *

class Statistics(pd.DataFrame):

    
    def show_nulls(self, cols:list[str]=None)-> None:
        """
        Displays the number and percentage of null values for specified DataFrame columns.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are analyzed.

        Returns:
            None: The function prints a summary table of null counts and percentages and does not return a value.

        Raises:
            ColumnNotExists: If any column in `cols` does not exist in the DataFrame.
        """

        if cols is None:
            cols: list[pd.Series] = self.columns
        else:
            check_if_columns_exist(self, cols)
        
        nulls_percentage: list= [] # will be converted later to a dataframe
  

        for col in cols:
            value: int = self[col].isnull().sum()
            # len(self[col]) returns the size of the columns
            percentage: float = round((value/len(self[col])) * 100, 2)
            nulls_percentage.append([col, value, f"{percentage}%"])


        Utils.convert_dataframe(nulls_percentage, ["Nulls Count","Percentage"])

    def show_num_unique_values(self, cols: list[str]=None) -> None:
        """
        Displays the number of unique values for specified DataFrame columns.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are analyzed.

        Returns:
            None: The function prints a summary table of unique value counts and does not return a value.

        Raises:
            ColumnNotExists: If any column in `cols` does not exist in the DataFrame.
        """

        if cols is None:
            cols: list[pd.Series] = self.columns
        else:
            check_if_columns_exist(self, cols)
        unique_values: list = []  

        for col in cols:
            
            num_unique_values: int = self[col].nunique()
            unique_values.append([col, num_unique_values])
        Utils.convert_dataframe(unique_values, ["Num of Unique Values"])

    def show_max_values(self, cols: list[str] =None) -> None:
        """
        Displays the maximum (or most common) values for specified DataFrame columns, 
        including their count and percentage of occurrences.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are analyzed.

        Returns:
            None: The function prints a summary table of maximum values and does not return a value.

        Raises:
            ColumnNotExists: If any column in `cols` does not exist in the DataFrame.
        """

        if cols is None:
            cols: list[pd.Series] = self.columns
        else:
            check_if_columns_exist(self, cols)

        max_values_list: list = []

        for col in cols:

            max_value = Getter.get_max_value(self, col)
            max_value_count = self[col].eq(max_value).sum()  
        
            perc = round((max_value_count / len(self[col])) * 100, 2)
            max_values_list.append([col, max_value, max_value_count, perc])

        Utils.convert_dataframe(max_values_list,  ["Max/Most Common Value", "Occurences", "Percentage"])

    def show_min_values(self, cols: list[str]=None) -> None:
        """
        Displays the minimum (or least common) values for specified DataFrame columns, 
        including their count and percentage of occurrences.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are analyzed.

        Returns:
            None: The function prints a summary table of minimum values and does not return a value.

        Raises:
            ColumnNotExists: If any column in `cols` does not exist in the DataFrame.
        """

        if cols is None:
            cols: list[pd.Series] = self.columns
        else:
            check_if_columns_exist(self, cols)

        min_values_list: list = []

        for col in cols:

            min_value = Getter.get_min_value(self, col)
            min_value_count = self[col].eq(min_value).sum()  
        
            perc = round((min_value_count / len(self[col])) * 100, 2)
            min_values_list.append([col, min_value, min_value_count, perc])

        Utils.convert_dataframe(min_values_list,  ["Min/Less Common Value", "Occurences", "Percentage"])

    def show_values_insight(self, cols: list[str]= None) -> None:
        """
        Displays key insights for specified DataFrame columns, including data type, unique values, 
        max/min values with their counts and percentages, and null value statistics.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are analyzed.

        Returns:
            None: The function prints a summary table of insights and does not return a value.

        Raises:
            ColumnNotExists: If any column in `cols` does not exist in the DataFrame.
        """

        if cols is None:
            cols: list[pd.Series] = self.columns
        else:
            check_if_columns_exist(self, cols)
            
        dataframe_data: list = []  
        
        for col in cols:
            nulls_count: int = self[col].isnull().sum()
            
            col_size: int = len(self[col])
                    
            max_value_count: int =self[col].eq(Getter.get_max_value(self, col)).sum()
            
            min_value_count: int =self[col].eq(Getter.get_min_value(self, col)).sum()
            # In each column it will retrieve this info
            col_info = [  
                col,  
                self[col].dtype.name,  
                Getter.get_unique_values(self, col),  
                Getter.get_max_value(self, col),  
                max_value_count,  
                f"{round((max_value_count/col_size)*100, 2)}%",  
                Getter.get_min_value(self, col),  
                min_value_count,  
                f"{round((min_value_count/col_size)*100, 2)}%",   
                nulls_count,  
                f"{round((nulls_count/col_size)*100,2)}%"  
            ]
            dataframe_data.append(col_info)  

        column_names = [    
            'Dtype',  
            'Distinct Values',  
            'Max Value',  
            'Max Value Occurrences',  
            'Max Value Occurences Percentage',  
            'Min Value',  
            'Min Value Occurrences',  
            'Min Value Occurences Percentage',  
            'Null Values',  
            'Null Values Percentage'  
        ] 
    
        Utils.convert_dataframe(dataframe_data, column_names)  
    def show_best_dtypes(self, cols: list[str] =None):
        """
        Displays the current and recommended memory-efficient data types for specified columns.

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are included.

        Returns:
            None: The function outputs a formatted DataFrame using Utils.convert_dataframe,
                showing each column's current dtype and the suggested best dtype.

        Examples:
            >>> df.show_best_dtypes(["age", "price"])
            # Displays current and recommended dtypes for 'age' and 'price'
            >>> df.show_best_dtypes()
            # Displays dtypes for all columns
        """
        if cols is None:
            cols = self.columns

        else:
            check_if_columns_exist(self, cols)

        best_dypes: list = [] 

        for col in cols:
            best_dtype = Getter.get_best_dtype(self, col)
            dtype = self[col].dtype.name
            best_dypes.append([col, dtype, best_dtype])
    
        Utils.convert_dataframe(best_dypes, ["Dtype","Best_Dtype"])
    def show_memory_insights(self, cols: list[str] = None,):
        """
        Displays detailed memory usage insights for specified columns in a DataFrame.

        The insights include:
        - Current data type
        - Recommended memory-efficient data type
        - Memory usage and percentage of total memory
        - Number and percentage of missing values
        - Number of distinct values

        Args:
            cols (list[str], optional): List of columns to analyze. If None, all columns are included.
   

        Returns:
            None: The function outputs a formatted DataFrame using Utils.convert_dataframe.

        Examples:
            >>> df.show_memory_insights(["age", "price"])
            # Displays detailed memory and data insights for 'age' and 'price'

        """
        if cols is None:
            cols = self.columns

        else:
            check_if_columns_exist(self, cols)
        dataframe: list = []
        total_usage = Getter.get_total_memory_usage(self, "kb")
         
        for col in cols:  
            col_info = Getter.get_memory_insights(self, col, total_usage)
            dataframe.append(col_info)  

        column_names: list[str] = [    
            'Dtype',  
            'Recommend Dtype',  
            'Memory',  
            'Memory Percentage',  
            'Missing Values',  
            'Percentage of Missing Values',  
            'Distinct Values'  
        ]
        Utils.convert_dataframe(dataframe, column_names)  
        
    def show_memory_usage(self: pd.DataFrame, cols: list[str]=None, unit: str ="kb"):
        """
        Displays the memory usage of selected columns in a DataFrame, including each column's 
        contribution as a percentage of the total memory usage.

        Args:
        cols (list[str], optional): List of columns to analyze. If None, all columns are included.
        unit (str, optional): Unit for memory measurement. Options are:
            - "b" for bytes
            - "kb" for kilobytes
            - "mb" for megabytes
            Default is "kb".

        Returns:
        None: The function outputs a formatted DataFrame using Utils.convert_dataframe.

        Examples:
            >>> df.show_memory_usage(["age", "price"], unit="mb")
            # Displays memory usage of 'age' and 'price' in MB with their percentage of total memory
            >>> df.show_memory_usage()
            # Displays memory usage for all columns in KB
        """
        if cols is None:
            cols = self.columns
        else:
            check_if_columns_exist(self, cols)
            
        data: list = []

        for col in cols:

            value_numeric, total_usage = Getter.get_memory_usage(self, col, unit)

            value_percentage: float = round((value_numeric/total_usage) * 100, 2)
            data.append([col, value_numeric, value_percentage])   
        
        Utils.convert_dataframe(data, [f"Memory_Usage({unit})", f"Percentage_of_Memory_Usage({unit})"])  

