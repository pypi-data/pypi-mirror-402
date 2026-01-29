"""Sheet class for worksheet operations."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from openpyxl.worksheet.worksheet import Worksheet

from xltemplate.utils import iter_dataframe_rows

if TYPE_CHECKING:
    from xltemplate.workbook import Workbook


class Sheet:
    """
    Represents a worksheet within a Workbook.
    
    Provides methods for writing DataFrames and values while preserving
    existing formatting and formulas.
    
    Attributes:
        name: The name of the worksheet
    """
    
    def __init__(self, worksheet: Worksheet, workbook: Workbook) -> None:
        """
        Initialize a Sheet wrapper.
        
        Args:
            worksheet: The underlying openpyxl Worksheet object
            workbook: Reference to the parent Workbook
        """
        self._ws = worksheet
        self._wb = workbook
    
    @property
    def name(self) -> str:
        """The name of this worksheet."""
        return self._ws.title
    
    def write_df(
        self,
        df: Any,
        row: int,
        col: int,
        *,
        headers: bool = True,
        preserve_format: bool = True,
        preserve_formulas: bool = True,
    ) -> Sheet:
        """
        Write a DataFrame to the worksheet starting at the specified position.
        
        Args:
            df: A Pandas or Polars DataFrame
            row: Starting row (1-indexed)
            col: Starting column (1-indexed)
            headers: Include column headers as the first row (default: True)
            preserve_format: Keep existing cell formatting (default: True)
            preserve_formulas: Skip cells containing formulas (default: True)
            
        Returns:
            Self for method chaining
            
        Raises:
            TypeError: If df is not a supported DataFrame type
            ValueError: If row or col is less than 1
        """
        if row < 1 or col < 1:
            raise ValueError("row and col must be >= 1 (1-indexed)")
        
        for r_idx, data_row in enumerate(iter_dataframe_rows(df, headers), start=row):
            for c_idx, value in enumerate(data_row, start=col):
                self._write_cell(
                    r_idx, c_idx, value,
                    preserve_format=preserve_format,
                    preserve_formulas=preserve_formulas,
                )
        
        return self
    
    def write_value(
        self,
        value: Any,
        row: int,
        col: int,
        *,
        preserve_format: bool = True,
    ) -> Sheet:
        """
        Write a single value to a cell.
        
        Args:
            value: The value to write
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            preserve_format: Keep existing cell formatting (default: True)
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If row or col is less than 1
        """
        if row < 1 or col < 1:
            raise ValueError("row and col must be >= 1 (1-indexed)")
        
        self._write_cell(row, col, value, preserve_format=preserve_format)
        return self
    
    def _write_cell(
        self,
        row: int,
        col: int,
        value: Any,
        *,
        preserve_format: bool = True,
        preserve_formulas: bool = False,
    ) -> None:
        """
        Internal method to write a value to a cell with optional preservation.
        
        Args:
            row: Row number (1-indexed)
            col: Column number (1-indexed)
            value: The value to write
            preserve_format: Keep existing cell formatting
            preserve_formulas: Skip if cell contains a formula
        """
        cell = self._ws.cell(row=row, column=col)
        
        # Skip cells with formulas if preserve_formulas is True
        if preserve_formulas:
            current_value = cell.value
            if isinstance(current_value, str) and current_value.startswith("="):
                return
        
        if preserve_format:
            # Store the existing style ID before writing
            existing_style = cell._style
            cell.value = value
            # Restore the style after writing
            cell._style = existing_style
        else:
            cell.value = value
