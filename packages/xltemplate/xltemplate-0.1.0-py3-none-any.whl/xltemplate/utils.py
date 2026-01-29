"""DataFrame iteration utilities supporting Pandas and Polars."""

from typing import Any, Iterator


def iter_dataframe_rows(df: Any, headers: bool = True) -> Iterator[tuple]:
    """
    Yield rows from a Pandas or Polars DataFrame.
    
    Uses duck typing to detect the DataFrame type, avoiding hard dependencies
    on either library.
    
    Args:
        df: A Pandas or Polars DataFrame
        headers: If True, yield column names as the first row
        
    Yields:
        Tuples of row values
        
    Raises:
        TypeError: If df is not a supported DataFrame type
    """
    # Polars DataFrame detection
    if hasattr(df, "iter_rows") and hasattr(df, "columns"):
        if headers:
            yield tuple(df.columns)
        yield from df.iter_rows()
    
    # Pandas DataFrame detection
    elif hasattr(df, "itertuples") and hasattr(df, "columns"):
        if headers:
            yield tuple(df.columns)
        for row in df.itertuples(index=False, name=None):
            yield row
    
    else:
        raise TypeError(
            f"Unsupported DataFrame type: {type(df).__name__}. "
            "Expected a Pandas or Polars DataFrame."
        )


def get_dataframe_shape(df: Any) -> tuple[int, int]:
    """
    Get the shape (rows, columns) of a DataFrame.
    
    Args:
        df: A Pandas or Polars DataFrame
        
    Returns:
        Tuple of (n_rows, n_cols)
    """
    if hasattr(df, "shape"):
        return df.shape
    raise TypeError(f"Cannot determine shape of {type(df).__name__}")
