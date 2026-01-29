"""Schema classes for template structure extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TableSchema:
    """
    Represents the column structure extracted from a template header.
    
    Use this to create DataFrames that match a template's expected structure,
    or to validate that existing DataFrames conform to the template.
    
    The schema captures hierarchical column headers (e.g., grouped columns)
    and creates DataFrames with pandas MultiIndex columns so that each cell
    can be addressed by all levels of the hierarchy.
    
    Attributes:
        column_names: List of column names in order (leaf-level for multi-row headers)
        header_rows: List of header rows above the leaf row, from top to bottom.
                     Each row is a list of (label, span) tuples.
    
    Example:
        >>> schema = sheet.extract_header_schema(row=6, col=2, n_cols=16, n_header_rows=3)
        >>> df = schema.empty_df()
        >>> df[("Prevalence by Domain", "Domain: XXX", "N")]  # Access by hierarchy
    """
    
    column_names: list[str]
    header_rows: list[list[tuple[str, int]]] = field(default_factory=list)
    
    @property
    def groups(self) -> list[tuple[str, int]] | None:
        """Backward-compatible alias for the first header row."""
        return self.header_rows[0] if self.header_rows else None
    
    @property
    def n_levels(self) -> int:
        """Number of header levels (header_rows + leaf column_names)."""
        return len(self.header_rows) + 1
    
    def _expand_header_row(self, row: list[tuple[str, int]]) -> list[str]:
        """
        Expand (label, span) tuples into per-column labels.
        
        Example:
            [('A', 2), ('B', 3)] -> ['A', 'A', 'B', 'B', 'B']
        """
        result = []
        for label, span in row:
            result.extend([label] * span)
        return result
    
    def to_multiindex(self) -> Any:
        """
        Build a pandas MultiIndex from the header structure.
        
        Each level of the MultiIndex corresponds to a header row,
        with the leaf column_names as the final level.
        
        Returns:
            pandas.MultiIndex with one level per header row + leaf columns
            
        Raises:
            ImportError: If pandas is not installed
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required to use to_multiindex(). "
                "Install it with: pip install pandas"
            ) from e
        
        if not self.header_rows:
            # Single-level header: just return Index
            return pd.Index(self.column_names)
        
        # Build tuples for each column position
        n_cols = len(self.column_names)
        tuples = []
        
        for col_idx in range(n_cols):
            col_tuple = []
            # Add label from each header row
            for header_row in self.header_rows:
                expanded = self._expand_header_row(header_row)
                col_tuple.append(expanded[col_idx])
            # Add the leaf column name
            col_tuple.append(self.column_names[col_idx])
            tuples.append(tuple(col_tuple))
        
        return pd.MultiIndex.from_tuples(tuples)
    
    def empty_df(self, n_rows: int = 0) -> Any:
        """
        Create an empty DataFrame with MultiIndex columns matching this schema.
        
        For multi-row headers, the DataFrame will have hierarchical columns
        that can be accessed by the full path, e.g.:
            df[("Prevalence by Domain", "Domain: XXX", "N")]
        
        Args:
            n_rows: Number of rows to pre-allocate (default: 0)
            
        Returns:
            A pandas DataFrame with MultiIndex columns matching the schema.
            
        Raises:
            ImportError: If pandas is not installed
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required to use empty_df(). "
                "Install it with: pip install pandas"
            ) from e
        
        columns = self.to_multiindex()
        
        if n_rows > 0:
            return pd.DataFrame(index=range(n_rows), columns=columns)
        return pd.DataFrame(columns=columns)
    
    def validate_df(self, df: Any) -> bool:
        """
        Check if a DataFrame's columns match this schema's MultiIndex structure.
        
        Args:
            df: A pandas DataFrame to validate
            
        Returns:
            True if columns match exactly (all levels, names, and order)
        """
        if not hasattr(df, "columns"):
            return False
        
        expected = self.to_multiindex()
        actual = df.columns
        
        # Compare the column structures
        if len(expected) != len(actual):
            return False
        
        return list(expected) == list(actual)
    
    def __len__(self) -> int:
        """Return the number of columns in the schema."""
        return len(self.column_names)
