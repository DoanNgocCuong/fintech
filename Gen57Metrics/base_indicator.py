"""
Base Indicator class following SOLID principles.

This module defines the abstract base class for all financial indicators.
Indicators can be either:
- DirectIndicator: Values retrieved directly from database
- CalculatedIndicator: Values computed from other indicators
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseIndicator(ABC):
    """
    Abstract base class for all financial indicators.
    
    Following SOLID principles:
    - Single Responsibility: Each indicator is responsible for one metric
    - Open/Closed: Open for extension (new indicators), closed for modification
    - Liskov Substitution: All indicators can be used interchangeably
    - Interface Segregation: Simple, focused interface
    - Dependency Inversion: Depends on abstraction (this base class)
    """
    
    def __init__(
        self,
        indicator_id: int,
        indicator_name: str,
        definition: str,
        group: str,
        **kwargs
    ):
        """
        Initialize base indicator.
        
        Args:
            indicator_id: Unique identifier for the indicator
            indicator_name: Name of the indicator (e.g., "CFO", "EBIT")
            definition: Definition/description of the indicator
            group: Group category (e.g., "BCTC Core - Profit & Cashflow")
            **kwargs: Additional metadata (formula, weights, etc.)
        """
        self.id = indicator_id
        self.name = indicator_name
        self.definition = definition
        self.group = group
        self.metadata = kwargs
        
        # Value cache (computed/retrieved value)
        self._value: Optional[float] = None
        self._value_context: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def get_value(
        self,
        stock: str,
        year: int,
        quarter: Optional[int] = None,
        **kwargs
    ) -> Optional[float]:
        """
        Get the indicator value for given stock, year, and optionally quarter.
        
        This is the main interface method that all indicators must implement.
        For DirectIndicator, it retrieves from database.
        For CalculatedIndicator, it computes from other indicators.
        
        Args:
            stock: Stock symbol (e.g., "MIG", "PGI")
            year: Year (e.g., 2024)
            quarter: Quarter (1-4) or None for annual report
            **kwargs: Additional parameters specific to indicator type
            
        Returns:
            Optional[float]: The indicator value, or None if not available
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_value()")
    
    def clear_cache(self) -> None:
        """Clear cached value."""
        self._value = None
        self._value_context = None
    
    @property
    def cached_value(self) -> Optional[float]:
        """Get cached value if available."""
        return self._value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert indicator to dictionary representation.
        
        Returns:
            Dictionary with all indicator properties
        """
        return {
            "id": self.id,
            "indicator_name": self.name,
            "definition": self.definition,
            "group": self.group,
            "value": self._value,
            **self.metadata
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"

