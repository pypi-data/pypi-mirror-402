import pandas as pd

from .getter import Getter
from .errors import *

class Cleaning(pd.DataFrame):

    def transform_cols_name(self, cols:list[str] = None, action="capitalize"):
        """
        Transforms the names of specified columns by applying a string method.

        Supported actions:
        - "capitalize": Capitalizes the first letter of each column name.
        - "lower": Converts column names to lowercase.
        - "upper": Converts column names to uppercase.

        Args:
            cols (list[str], optional): List of columns to transform. If None, all columns are transformed.
            action (str, optional): The transformation to apply. Must be one of ["capitalize", "lower", "upper"].
                Default is "capitalize".

        Returns:
            DataFrame: A new instance of the same DataFrame class with transformed column names.

        Raises:
            Exception: If the provided action is not supported.

        Examples:
            >>> df.transform_cols_name(["age", "price"], action="upper")
            # Column names 'age' and 'price' are converted to 'AGE' and 'PRICE'

            >>> df.transform_cols_name(action="lower")
            # All column names are converted to lowercase
        """
        action = action.lower()
        
        if action not in ["capitalize", "lower", "upper"]:
            raise Exception(f"The value of action must be one of these [capitalize, lower, upper]")
        
        if cols is None:
            cols = self.columns
            
        else:
            check_if_columns_exist(self, cols)
        
        # Gets the value of variable action
        new_df = self.rename(
            columns={c: getattr(c, action)() for c in cols}
        )
        return self.__class__(new_df)

    def round_rows_value(self, cols:list[str], decimals: int =1):
        """
        Rounds the values of specified numeric columns to a given number of decimal places.

        Only columns with a floating-point data type are rounded. Non-float columns are ignored.

        Args:
            cols (list[str]): List of columns to round.
            decimals (int, optional): Number of decimal places to round to. Default is 1.

        Returns:
            DataFrame: The original DataFrame with the specified columns rounded.

        Raises:
            ColumnNotExists: If any of the specified columns do not exist in the DataFrame.

        Examples:
            >>> df.round_rows_value(["price", "discount"], decimals=2)
            # Rounds 'price' and 'discount' columns to 2 decimal places
        """
        check_if_columns_exist(self, cols)
            
        numerical_cols = []
        for col in cols:
            dtype = self[col].dtype.name
            # only appends if the col is float
            if "float" in dtype: 
                numerical_cols.append(col)
        self[numerical_cols] = self[numerical_cols].map(lambda x: round(x, decimals))

        return self
    def convert_float_cols_to_int(self, cols:list[str]):
        """
        Converts specified float columns to integer type by rounding their values.

        Columns with missing values will raise an error, as integer conversion is not possible
        with NaNs. Only columns with a float data type are processed; others are ignored.

        Args:
            cols (list[str]): List of columns to convert from float to int.

        Returns:
            DataFrame: The original DataFrame with the specified columns converted to integers.

        Raises:
            ColumnNotExists: If any of the specified columns do not exist in the DataFrame.
            ValueError: If any of the specified columns contain missing values.

        Examples:
            >>> df.convert_float_cols_to_int(["age", "quantity"])
            # Rounds 'age' and 'quantity' columns and converts them to integer type
        """
        check_if_columns_exist(self, cols)
        
        numerical_cols: list = []
        
        for col in cols:
            dtype = self[col].dtype.name
            # only appends if the col is float
            if "float" in dtype: 
                if self[col].isna().any():
                    raise ValueError(f"Missing values found on column {col}. Please fix it")
                numerical_cols.append(col)

        self[numerical_cols] = self[numerical_cols].map(lambda x: round(x, 0)).astype(int)

        return self

    def convert_to_best_dtypes(self, cols: list[str] =None):
        """
        Converts specified columns to their most memory-efficient data types.

        - Errors during conversion are caught and displayed, allowing processing to continue.

        Args:
            cols (list[str], optional): List of columns to convert. If None, all columns are converted.

        Returns:
            DataFrame:
                - Returns the DataFrame with converted dtypes.

        Raises:
            ColumnNotExists: If any of the specified columns do not exist in the DataFrame.

        Examples:
            >>> df.convert_to_best_dtypes(["age", "price"])
            # Converts 'age' and 'price' to their most memory-efficient dtypes
        """
        if cols is None:
            cols = self.columns

        else:
            check_if_columns_exist(self, cols)


        for col in cols:
            try:
                dtype = Getter.get_best_dtype(self, col)   
                self[col] = self[col].astype(dtype)

            except Exception as e:
                print(f"Error on processing columm {col}: {e}")
                continue

        return self

    def convert_binary_to_bool(self, col: str, false_value = 0, true_value = 1):
        """
        Converts a binary column to boolean type based on specified true and false values.

        Args:
            col (str): Name of the column to convert.
            false_value (any, optional): The value representing False. Default is 0.
            true_value (any, optional): The value representing True. Default is 1.

        Returns:
            DataFrame: The original DataFrame with the specified column converted to boolean.

        Raises:
            ColumnNotExists: If the specified column does not exist in the DataFrame.

        Examples:
            >>> df.convert_binary_to_bool("is_active")
            # Converts 0/1 values in 'is_active' to False/True

            >>> df.convert_binary_to_bool("flag", false_value="N", true_value="Y")
            # Converts 'N'/'Y' values in 'flag' to False/True
        """
        check_if_columns_exist(self, [col])
        self[col] = self[col].map({false_value: False, true_value: True})
        self[col] = self[col].astype(bool)
        return self