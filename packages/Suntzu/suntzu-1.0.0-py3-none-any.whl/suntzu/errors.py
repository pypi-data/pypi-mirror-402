class ColumnNotExists(Exception):
    """Error that raises when columns does not exist"""
    pass
class MixedDtypeError(Exception):
    """Error that raises when have mixed dtypes"""
    pass
def check_if_columns_exist(df, cols):
    """
    Checks if the specified columns exist in a DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame to check.
        cols (list[str]): A list of column names to verify.

    Raises:
        ColumnNotExists: If any of the specified columns are missing from the DataFrame.

    Examples:
        >>> from suntzu.errors import check_if_columns_exist
        >>> check_if_columns_exist(df, ["age", "price"])
        # No exception if both columns exist
        >>> check_if_columns_exist(df, ["age", "salary"])
        ColumnNotExists: The following columns are not present in the DataFrame: {'salary'}
    """
    missing_cols = set(cols) - set(df.columns)
    if missing_cols:
        raise ColumnNotExists(f"The following columns are not present in the DataFrame: {missing_cols}")