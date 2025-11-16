"""
DirectIndicator class for indicators retrieved directly from database.

These indicators have Get_Direct_From_DB = "yes" in the JSON template.
They fetch values directly from database using ma_so (code number).
"""

from typing import Optional
from Gen57Metrics.base_indicator import BaseIndicator
from Gen57Metrics.utils_database_manager import get_value_by_ma_so


class DirectIndicator(BaseIndicator):
    """
    Indicator that retrieves values directly from database.
    
    This class handles indicators where Get_Direct_From_DB = "yes".
    Values are fetched using ma_so (code number) from financial statements.
    """
    
    def __init__(
        self,
        indicator_id: int,
        indicator_name: str,
        definition: str,
        group: str,
        ma_so: int,
        table_name: Optional[str] = None,
        value_field: str = "so_cuoi_nam",
        **kwargs
    ):
        """
        Initialize direct indicator.
        
        Args:
            indicator_id: Unique identifier for the indicator
            indicator_name: Name of the indicator
            definition: Definition/description
            group: Group category
            ma_so: Code number to query in database (e.g., 111, 20, 21)
            table_name: Database table name (default: from utils_database_manager)
            value_field: Field name containing value (default: "so_cuoi_nam")
            **kwargs: Additional metadata
        """
        super().__init__(indicator_id, indicator_name, definition, group, **kwargs)
        self.ma_so = ma_so
        self.table_name = table_name
        self.value_field = value_field
        
        # Add ma_so to metadata
        self.metadata["ma_so"] = ma_so
        self.metadata["get_direct_from_db"] = "yes"
    
    def get_value(
        self,
        stock: str,
        year: int,
        quarter: Optional[int] = None,
        **kwargs
    ) -> Optional[float]:
        """
        Get indicator value directly from database.
        
        Args:
            stock: Stock symbol
            year: Year
            quarter: Quarter (1-4) or None for annual
            **kwargs: Additional parameters (table_name, value_field can be overridden)
            
        Returns:
            Optional[float]: Value from database, or None if not found
        """
        # Allow override of table_name and value_field via kwargs
        table_name = kwargs.get("table_name", self.table_name)
        value_field = kwargs.get("value_field", self.value_field)
        
        # Retrieve value from database
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=self.ma_so,
            quarter=quarter,
            table_name=table_name,
            value_field=value_field
        )
        
        # Cache the value
        self._value = value
        self._value_context = {
            "stock": stock,
            "year": year,
            "quarter": quarter,
            "table_name": table_name,
            "value_field": value_field
        }
        
        return value
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}', ma_so={self.ma_so})"

