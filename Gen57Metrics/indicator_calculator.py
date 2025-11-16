"""
Indicator Calculator - Calculate all 57 indicators for a stock.

This module handles calculation of all indicators with dependency resolution,
error handling, and caching.
"""

from typing import Dict, Optional, Any, List, Set, Tuple
from datetime import datetime
from collections import defaultdict, deque
import re

from Gen57Metrics.indicator_registry import IndicatorRegistry, IndicatorDefinition, get_registry
from Gen57Metrics.indicator_mapper import IndicatorMapper, get_mapper


class IndicatorCalculator:
    """
    Calculate all indicators for a stock.
    
    Following SOLID principles:
    - Single Responsibility: Calculate indicators for a stock
    - Open/Closed: Easy to extend with new calculation logic
    - Dependency Inversion: Depends on registry and mapper abstractions
    """
    
    def __init__(
        self,
        registry: Optional[IndicatorRegistry] = None,
        mapper: Optional[IndicatorMapper] = None
    ):
        """
        Initialize calculator.
        
        Args:
            registry: Indicator registry. If None, uses default.
            mapper: Indicator mapper. If None, uses default.
        """
        self.registry = registry or get_registry()
        self.mapper = mapper or get_mapper()
        
        # Cache for calculated values
        self._value_cache: Dict[str, Optional[float]] = {}
        self._calculation_order: List[str] = []
        
        # Auto-register direct indicators that don't have explicit mappings
        self._auto_register_direct_indicators()
    
    def _auto_register_direct_indicators(self) -> None:
        """Auto-register direct indicators that don't have explicit functions."""
        for indicator in self.registry.get_direct_indicators():
            if not self.mapper.has_mapping(indicator.indicator_name):
                self.mapper.auto_register_from_definition(indicator)
    
    def _parse_dependencies(self, indicator: IndicatorDefinition) -> Set[str]:
        """
        Parse dependencies from indicator's formula or TT200_Formula.
        
        Examples:
            "EBITDA = EBIT + D&A" → {"EBIT"}
            "NOPAT = EBIT × (1 – Tax rate)" → {"EBIT"}
            "GM = Gross Profit / Revenue" → {"Gross Profit", "Revenue"}
        
        Args:
            indicator: Indicator definition
            
        Returns:
            Set of dependency indicator names
        """
        dependencies: Set[str] = set()
        
        # Check Formula field
        formula = indicator.formula or ""
        
        # Known dependency patterns
        dependency_patterns = [
            r'EBIT\b',  # EBITDA, NOPAT depend on EBIT
            r'Gross Profit\b',  # Gross Margin depends on Gross Profit
            r'Revenue\b',  # Gross Margin depends on Revenue
            r'NI\b',  # Various ratios depend on NI
            r'CFO\b',  # Various ratios depend on CFO
            r'NOPAT\b',  # ROIC depends on NOPAT
            r'EBITDA\b',  # EV/EBITDA depends on EBITDA
        ]
        
        # Extract potential dependencies from formula
        for pattern in dependency_patterns:
            if re.search(pattern, formula, re.IGNORECASE):
                dependency_name = re.search(pattern, formula, re.IGNORECASE).group(0)
                # Normalize name (e.g., "EBIT" might be "EBIT" or "EBIT ")
                dependency_name = dependency_name.strip()
                
                # Check if it's a valid indicator name in registry
                if self.registry.get_by_name(dependency_name):
                    dependencies.add(dependency_name)
        
        # Manual dependency mapping for known cases
        manual_dependencies = {
            "EBITDA": ["EBIT"],
            "NOPAT": ["EBIT"],
            "Gross Margin": ["Gross Profit", "Revenue"],
            # Add more as needed
        }
        
        if indicator.indicator_name in manual_dependencies:
            dependencies.update(manual_dependencies[indicator.indicator_name])
        
        return dependencies
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort to determine calculation order.
        
        Direct indicators (no dependencies) are calculated first,
        followed by calculated indicators in dependency order.
        
        Returns:
            List of indicator names in calculation order
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = defaultdict(int)
        
        # Initialize all indicators
        all_indicators = self.registry.get_all()
        for indicator in all_indicators:
            indicator_name = indicator.indicator_name
            graph[indicator_name] = self._parse_dependencies(indicator)
            in_degree[indicator_name] = len(graph[indicator_name])
        
        # Kahn's algorithm for topological sort
        queue = deque()
        
        # Start with direct indicators (no dependencies)
        for indicator in self.registry.get_direct_indicators():
            if in_degree[indicator.indicator_name] == 0:
                queue.append(indicator.indicator_name)
        
        # Start with calculated indicators that have no dependencies
        for indicator in self.registry.get_calculated_indicators():
            if in_degree[indicator.indicator_name] == 0:
                queue.append(indicator.indicator_name)
        
        result: List[str] = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Decrease in-degree of dependent nodes
            for indicator in all_indicators:
                if node in graph[indicator.indicator_name]:
                    in_degree[indicator.indicator_name] -= 1
                    if in_degree[indicator.indicator_name] == 0:
                        queue.append(indicator.indicator_name)
        
        # Add remaining indicators (circular dependencies or no dependencies)
        remaining = set(indicator.indicator_name for indicator in all_indicators) - set(result)
        result.extend(remaining)
        
        return result
    
    def calculate_all(
        self,
        stock: str,
        year: int,
        quarter: Optional[int] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate all 57 indicators for a stock.
        
        Args:
            stock: Stock symbol (e.g., "MIG", "PGI")
            year: Year (e.g., 2024)
            quarter: Quarter (1-4) or None for annual
            include_metadata: Whether to include calculation metadata
            
        Returns:
            Dictionary with all indicators and metadata
        """
        # Clear cache for new calculation
        self._value_cache.clear()
        
        # Get calculation order (topological sort)
        calculation_order = self._topological_sort()
        self._calculation_order = calculation_order
        
        # Calculate each indicator in order
        calculated_indicators: Dict[str, Optional[float]] = {}
        indicators_with_id: List[Dict[str, Any]] = []
        successful: List[str] = []
        failed: List[str] = []
        
        for indicator_name in calculation_order:
            try:
                value = self._calculate_indicator(indicator_name, stock, year, quarter)
                calculated_indicators[indicator_name] = value
                
                # Get indicator definition to include ID
                indicator_def = self.registry.get_by_name(indicator_name)
                indicator_id = indicator_def.id if indicator_def else None
                
                # Add to indicators_with_id list
                indicators_with_id.append({
                    "id": indicator_id,
                    "name": indicator_name,
                    "value": value
                })
                
                if value is not None:
                    successful.append(indicator_name)
                else:
                    failed.append(indicator_name)
                    
            except Exception as e:
                calculated_indicators[indicator_name] = None
                
                # Get indicator definition to include ID even for failed ones
                indicator_def = self.registry.get_by_name(indicator_name)
                indicator_id = indicator_def.id if indicator_def else None
                
                # Add to indicators_with_id list
                indicators_with_id.append({
                    "id": indicator_id,
                    "name": indicator_name,
                    "value": None
                })
                
                failed.append(indicator_name)
                try:
                    print(f"  ⚠ Error calculating {indicator_name}: {e}")
                except UnicodeEncodeError:
                    print(f"  [WARN] Error calculating {indicator_name}: {e}")
        
        # Sort indicators_with_id by ID
        indicators_with_id.sort(key=lambda x: x["id"] if x["id"] is not None else 9999)
        
        # Build result
        result: Dict[str, Any] = {
            "stock": stock,
            "year": year,
            "quarter": quarter,
            "indicators_with_id": indicators_with_id,  # Format with ID (sorted by ID)
        }
        
        if include_metadata:
            result["metadata"] = {
                "calculated_at": datetime.now().isoformat(),
                "total_indicators": len(calculated_indicators),
                "successful": len(successful),
                "failed": len(failed),
                "failed_list": failed,
                "calculation_order": calculation_order
            }
        
        return result
    
    def _calculate_indicator(
        self,
        indicator_name: str,
        stock: str,
        year: int,
        quarter: Optional[int] = None
    ) -> Optional[float]:
        """
        Calculate a single indicator.
        
        Args:
            indicator_name: Name of the indicator
            stock: Stock symbol
            year: Year
            quarter: Quarter or None
            
        Returns:
            Indicator value or None if calculation failed
        """
        # Check cache first
        cache_key = f"{indicator_name}_{stock}_{year}_{quarter}"
        if cache_key in self._value_cache:
            return self._value_cache[cache_key]
        
        # Get indicator definition
        indicator = self.registry.get_by_name(indicator_name)
        if not indicator:
            try:
                print(f"  ⚠ Indicator '{indicator_name}' not found in registry")
            except UnicodeEncodeError:
                print(f"  [WARN] Indicator '{indicator_name}' not found in registry")
            return None
        
        # Get calculation function
        calc_func = self.mapper.get_function(indicator_name)
        if not calc_func:
            try:
                print(f"  ⚠ No calculation function for '{indicator_name}'")
            except UnicodeEncodeError:
                print(f"  [WARN] No calculation function for '{indicator_name}'")
            return None
        
        # Calculate value
        try:
            value = calc_func(stock, year, quarter)
            self._value_cache[cache_key] = value
            return value
        except Exception as e:
            try:
                print(f"  ✗ Error calculating {indicator_name}: {e}")
            except UnicodeEncodeError:
                print(f"  [ERROR] Error calculating {indicator_name}: {e}")
            return None
    
    def calculate_single(
        self,
        indicator_name: str,
        stock: str,
        year: int,
        quarter: Optional[int] = None
    ) -> Optional[float]:
        """
        Calculate a single indicator.
        
        Args:
            indicator_name: Name of the indicator
            stock: Stock symbol
            year: Year
            quarter: Quarter or None
            
        Returns:
            Indicator value or None
        """
        return self._calculate_indicator(indicator_name, stock, year, quarter)
    
    def clear_cache(self) -> None:
        """Clear value cache."""
        self._value_cache.clear()
    
    def __repr__(self) -> str:
        return f"IndicatorCalculator(registry={len(self.registry)} indicators)"


# Convenience function
def calculate_all_indicators(
    stock: str,
    year: int,
    quarter: Optional[int] = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Calculate all 57 indicators for a stock (convenience function).
    
    Args:
        stock: Stock symbol (e.g., "MIG", "PGI")
        year: Year (e.g., 2024)
        quarter: Quarter (1-4) or None for annual
        include_metadata: Whether to include calculation metadata
        
    Returns:
        Dictionary with all indicators and metadata
        
    Example:
        >>> result = calculate_all_indicators("MIG", 2024)
        >>> print(result["indicators"]["CFO"])
        1234567890.0
    """
    calculator = IndicatorCalculator()
    return calculator.calculate_all(stock, year, quarter, include_metadata)

