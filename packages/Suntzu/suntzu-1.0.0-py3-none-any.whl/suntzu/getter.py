import pandas as pd
import numpy as np

from .errors import *

class Getter:
    # cleaning functions
    def get_best_int(col_min: int, col_max: int) -> str:
        """
        Determines the smallest integer type capable of representing a range of values.

        Args:
            col_min (int): The minimum value in the range.
            col_max (int): The maximum value in the range.

        Returns:
            str: The name of the smallest integer type that can accommodate all values 
                in the range. Possible returns are "int8", "int16", "int32", or "int64".

        Examples:
            >>> from suntzu import Getter
            >>> Getter.get_best_int(-50, 100)
            'int8'
            >>> Getter.get_best_int(-200, 30000)
            'int16'
            >>> Getter.get_best_int(-50000, 100000)
            'int32'
            >>> Getter.get_best_int(-5000000000, 5000000000)
            'int64'
        """

        if col_min >= -128 and col_max <= 127:
            return "int8"
        elif col_min >= -32768 and col_max <= 32767:
            return "int16"
        elif col_min >= -2147483648 and col_max <= 2147483647:
            return "int32"
        else:
            return "int64"
    
    def get_best_float(col_min: float, col_max: float) -> str:
        """
        Determines the most memory-efficient floating-point type capable of representing 
        a range of values.

        Args:
            col_min (float): The minimum value in the range.
            col_max (float): The maximum value in the range.

        Returns:
            str: The name of the smallest floating-point type that can accommodate all values 
                in the range. Possible returns are "float16", "float32", or "float64".

        Examples:
            >>> from suntzu import Getter
            >>> Getter.get_best_float(0.1, 100.0)
            'float16'
            >>> Getter.get_best_float(-1e5, 1e5)
            'float32'
            >>> Getter.get_best_float(-1e40, 1e40)
            'float64'
        """
        if col_min >= np.finfo(np.float16).min and col_min <= np.finfo(np.float16).max:
            return "float16"
        elif col_max >= np.finfo(np.float32).min and col_max <= np.finfo(np.float32).max:
            return "float32"
        else:
            return "float64"
        

    
    def get_best_dtype(self, col: str) -> str:
        """
        Determines the most memory-efficient data type for a column based on its values.

        The method inspects the column's current data type and value range to infer
        a more optimal dtype:
        - Integers are downcast to the smallest possible integer type.
        - Floats are downcast to the smallest possible floating-point type.
        - Object columns with a low number of unique values are converted to category.
        - Other types are returned unchanged.

        Args:
        col (str): Name of the column to analyze.

        Returns:
        str: The name of the most suitable data type for the column.

        Examples:
            >>> from suntzu import Getter
            >>> Getter.get_best_dtype(df, "age")
            'int8'
            >>> Getter.get_best_dtype(df, "price")
            'float32'
            >>> Getter.get_best_dtype(df, "status")
            'category'
        """
        dtype = self[col].dtype.name # returns int || float || category || bool
        col_min = Getter.get_min_value(self, col)
        col_max = Getter.get_max_value(self, col)
        if "int" in dtype:
            dtype = Getter.get_best_int(col_min, col_max)
        elif "float" in dtype:
            dtype = Getter.get_best_float(col_min, col_max)
        elif dtype == "object":
            if self[col].nunique() <= 10:
                dtype = "category"
        return dtype
    
    # statistics functions
    def get_max_value(self: pd.DataFrame, col: str) -> int | str:
        """
        Returns the maximum value of a DataFrame column, handling different data types appropriately.

        Args:
            col (str): The column of the DataFrame to inspect.

        Returns:
            int | str: 
                - For numeric columns, returns the maximum value.
                - For categorical or boolean columns, returns the most frequent value (mode).

        Raises:
            MixedDtypeError: If the column contains mixed types or null values.

        Examples:
            >>> from suntzu import Getter
            >>> import pandas as pd
            >>> df = pd.DataFrame({'a': [1, 3, 2], 'b': [True, False, True], 'c': ['x', 'y', 'x']})
            >>> Getter.get_max_value(df, 'a')
            3
            >>> Getter.get_max_value(df, 'b')
            True
            >>> Getter.get_max_value(df, 'c')
            'x'
        """

        dtype = self[col].dtype.name
        try:
            if not dtype in ["categorical", "bool", "object"]:
                value = self[col].max()
            else:
                value = self[col].mode()[0]
        except TypeError:
            raise MixedDtypeError(f"Column '{col}' contains mixed types (e.g., str + float) or null values. Please try cleaning it.")

        return value
    def get_min_value(self: pd.DataFrame, col: str) -> int | str:
        """
        Returns the minimum value of a DataFrame column, handling different data types appropriately.

        Args:
            col (str): The column of the DataFrame to inspect.

        Returns:
            int | str: 
                - For numeric columns, returns the minimum value.
                - For categorical or boolean columns, returns the least frequent value.

        Raises:
            MixedDtypeError: If the column contains mixed types or null values.

        Examples:
            >>> from suntzu import Getter
            >>> import pandas as pd
            >>> df = pd.DataFrame({'a': [1, 3, 2], 'b': [True, False, True], 'c': ['x', 'y', 'x']})
            >>> Getter.get_min_value(df, 'a')
            1
            >>> Getter.get_min_value(df, 'b')
            False
            >>> Getter.get_min_value(df, 'c')
            'y'
        """

        dtype = self[col].dtype.name
        try:
            if not dtype in ["categorical", "bool", "object"]:
                value = self[col].min()
            else:
                value = self[col].value_counts().idxmin()
        except TypeError:
            raise MixedDtypeError(f"Column '{col}' contains mixed types (e.g., str + float) or null values. Please try cleaning it.")

        return value

    
    def get_memory_usage(self, col, unit) -> float:
        """
        Calculates the memory usage of a specific column in the DataFrame.

        Args:
            col (str): Name of the column to measure.
            unit (str): Unit for memory measurement. Options are:
                - "b" for bytes
                - "kb" for kilobytes
                - "mb" for megabytes

        Returns:
            float: Memory usage of the specified column, rounded to 2 decimal places.

        Examples:
            >>> df.get_memory_usage("age", "kb")
            12.5
            >>> df.get_memory_usage("price", "mb")
            0.01
        """
        conversion_factors = {
            "kb": 1024,
            "mb": 1024**2,
            "b": 1
        }
        conversion_factor = conversion_factors[unit]
        
        memory_usage = self[col].memory_usage(deep=True)
        value_numeric = round(memory_usage / conversion_factor, 2)
        
    
        return value_numeric
    def get_total_memory_usage(self, unit) -> float:
        """
        Calculates the total memory usage of the DataFrame in the specified unit.

        Args:
            unit (str): Unit for memory measurement. Options are:
                - "b" for bytes
                - "kb" for kilobytes
                - "mb" for megabytes

        Returns:
            float: Total memory usage of the DataFrame, rounded to 2 decimal places.

        Examples:
            >>> df.get_total_memory_usage("kb")
            125.5
            >>> df.get_total_memory_usage("mb")
            0.12
        """
        conversion_factors = {
            "kb": 1024,
            "mb": 1024**2,
            "b": 1
        }
        conversion_factor = conversion_factors[unit]
        total_usage = self.memory_usage(deep=True).sum()
        total_usage = round(total_usage / conversion_factor, 2)
        return total_usage
    
    def get_memory_insights(self, col:str, total_usage: int) -> list:

        nulls_count: int = self[col].isnull().sum()
        col_size: int = len(self[col]) 
        value_numeric = Getter.get_memory_usage(self, col, "kb")
        
        value_percentage = round((value_numeric/total_usage)*100, 2)
        
        try:
            col_info: list[str] = [  
                col,  
                self[col].dtype.name,  
                Getter.get_best_dtype(self, col),  
                f"{value_numeric} kb",  
                f"{value_percentage}%",  
                nulls_count,  
                f"{round(nulls_count/col_size, 2)}%",  
                self[col].nunique(),  
            ]
        # This error stops the whole function so we handle it to continue and give a warning
        except MixedDtypeError:
            print(f"WARNING: {col} has missing values, so the best dtype could not be found")
            col_info: list[str] = [  
                col,  
                self[col].dtype.name,  
                "???",  
                f"{value_numeric} kb",
                f"{value_percentage}%",
                nulls_count,  
                f"{round(nulls_count/col_size, 2)}%",  
                self[col].nunique(),  
            ] 
        finally:
            return col_info