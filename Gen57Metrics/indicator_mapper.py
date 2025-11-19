"""
Indicator Mapper - Map Indicator_Name to Python calculation functions.

This module maps indicator names to their corresponding calculation functions.
It handles both direct indicators (from database) and calculated indicators.
"""

from typing import Dict, Callable, Optional, Any
import re
from Gen57Metrics.indicator_registry import IndicatorDefinition


# Import calculation functions from module folders
try:
    from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id1_CFO import get_CFO_value
    from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id2_NI import get_NI_value
    from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id3_EBIT import get_EBIT_value
    from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id4_EBITDA import get_EBITDA_value
    from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id5_NOPAT import get_NOPAT_value
except ImportError as e:
    print(f"Warning: Could not import some calculation functions: {e}")


def extract_ma_so_from_tt200_formula(tt200_formula: Optional[str]) -> Optional[int]:
    """
    Extract ma_so (code number) from TT200_Formula string.
    
    Examples:
        "KQKD – Mã 60" → 60
        "LCTT (TT200) – Mã 20" → 20
        "EBIT = (KQKD – Mã 50) + (KQKD – Mã 23)" → None (multiple ma_so)
    
    Args:
        tt200_formula: TT200_Formula string from JSON
        
    Returns:
        ma_so if single ma_so found, None otherwise
    """
    if not tt200_formula:
        return None
    
    # Pattern to match "Mã <number>" or "Mã số <number>"
    pattern = r'Mã\s*(?:số)?\s*(\d+)'
    matches = re.findall(pattern, tt200_formula, re.IGNORECASE)
    
    if len(matches) == 1:
        try:
            return int(matches[0])
        except ValueError:
            return None
    
    # Multiple ma_so found or no match
    return None


class IndicatorMapper:
    """
    Maps Indicator_Name to Python calculation functions.
    
    Following SOLID principles:
    - Single Responsibility: Map indicators to functions
    - Open/Closed: Easy to extend with new mappings
    - Dependency Inversion: Depends on abstraction (function interface)
    """
    
    def __init__(self):
        """Initialize mapper with built-in mappings."""
        self._function_map: Dict[str, Callable] = {}
        self._ma_so_map: Dict[str, int] = {}
        
        # Register built-in mappings
        self._register_builtin_mappings()
    
    def _register_builtin_mappings(self) -> None:
        """Register built-in indicator-to-function mappings."""
        # Profit & Cashflow indicators
        self.register("CFO", get_CFO_value)
        self.register("Net Income (NI)", get_NI_value)
        self.register("NI", get_NI_value)  # Alias
        self.register("EBIT", get_EBIT_value)
        self.register("EBITDA", get_EBITDA_value)
        self.register("NOPAT", get_NOPAT_value)
        
        # TODO: Add more mappings as modules are created
        # Revenue, Gross Profit, Gross Margin, etc.
    
    def register(self, indicator_name: str, func: Callable, ma_so: Optional[int] = None) -> None:
        """
        Register a function for an indicator.
        
        Args:
            indicator_name: Name of the indicator
            func: Function to calculate the indicator
            ma_so: Optional ma_so for direct indicators
        """
        self._function_map[indicator_name] = func
        if ma_so is not None:
            self._ma_so_map[indicator_name] = ma_so
    
    def get_function(self, indicator_name: str) -> Optional[Callable]:
        """Get calculation function for an indicator."""
        return self._function_map.get(indicator_name)
    
    def get_ma_so(self, indicator_name: str) -> Optional[int]:
        """Get ma_so for an indicator (if direct)."""
        return self._ma_so_map.get(indicator_name)
    
    def has_mapping(self, indicator_name: str) -> bool:
        """Check if indicator has a registered function."""
        return indicator_name in self._function_map
    
    def auto_register_from_definition(self, definition: IndicatorDefinition) -> bool:
        """
        Automatically register a direct indicator from its definition.
        
        For direct indicators, extracts ma_so from TT200_Formula and creates
        a wrapper function that calls get_value_by_ma_so.
        
        Args:
            definition: Indicator definition
            
        Returns:
            True if registered successfully, False otherwise
        """
        if not definition.is_direct:
            return False
        
        # Try to extract ma_so from TT200_Formula
        ma_so = extract_ma_so_from_tt200_formula(definition.tt200_formula)
        
        if ma_so is None:
            # Cannot auto-register without ma_so
            return False
        
        # Create a wrapper function
        from Gen57Metrics.utils_database_manager import get_value_by_ma_so
        
        def wrapper_func(stock: str, year: int, quarter: Optional[int] = None) -> Optional[float]:
            """Auto-generated function for direct indicator."""
            return get_value_by_ma_so(stock, year, ma_so, quarter)
        
        # Register the function
        self.register(definition.indicator_name, wrapper_func, ma_so)
        
        return True
    
    def get_all_mappings(self) -> Dict[str, Callable]:
        """Get all registered mappings."""
        return self._function_map.copy()
    
    def __repr__(self) -> str:
        return f"IndicatorMapper({len(self._function_map)} mappings)"


# Global mapper instance
_default_mapper: Optional[IndicatorMapper] = None


def get_mapper() -> IndicatorMapper:
    """
    Get global mapper instance (singleton pattern).
    
    Returns:
        IndicatorMapper instance
    """
    global _default_mapper
    
    if _default_mapper is None:
        _default_mapper = IndicatorMapper()
    
    return _default_mapper

