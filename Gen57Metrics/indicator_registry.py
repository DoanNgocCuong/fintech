"""
Indicator Registry - Load and manage all 57 indicators from JSON.

This module loads indicators from 57BaseIndicators.json and provides
a registry for accessing indicators by ID, name, or group.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class IndicatorDefinition:
    """
    Definition of an indicator loaded from JSON.
    
    Following SOLID principles - Single Responsibility:
    Each indicator definition contains all metadata needed to calculate it.
    """
    id: int
    indicator_name: str
    definition: str
    group: str
    formula: Optional[str] = None
    tt200_formula: Optional[str] = None
    get_direct_from_db: Optional[str] = None
    used_in_qgv: Optional[str] = None
    used_in_4m: Optional[str] = None
    formula_in_qgv: Optional[str] = None
    formula_in_4m: Optional[str] = None
    scoring_metric: Optional[str] = None
    weight_in_4m: Optional[float] = None
    weight_in_qgv: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_direct(self) -> bool:
        """Check if indicator is retrieved directly from database."""
        return self.get_direct_from_db == "yes"
    
    @property
    def is_calculated(self) -> bool:
        """Check if indicator is calculated from other indicators."""
        return not self.is_direct
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "ID": self.id,
            "Indicator_Name": self.indicator_name,
            "Definition": self.definition,
            "Group": self.group,
            "Formula": self.formula,
            "TT200_Formula": self.tt200_formula,
            "Get_Direct_From_DB": self.get_direct_from_db,
            "Used_in_QGV": self.used_in_qgv,
            "Used_in_4M": self.used_in_4m,
            "Formula_in_QGV": self.formula_in_qgv,
            "Formula_in_4M": self.formula_in_4m,
            "Scoring_Metric": self.scoring_metric,
            "Weight_in_4M": self.weight_in_4m,
            "Weight_in_QGV": self.weight_in_qgv,
            **self.metadata
        }


class IndicatorRegistry:
    """
    Registry for all 57 indicators.
    
    Following SOLID principles:
    - Single Responsibility: Manage indicator definitions
    - Open/Closed: Easy to extend with new indicators
    - Interface Segregation: Simple, focused interface
    """
    
    def __init__(self, json_file_path: Optional[str] = None):
        """
        Initialize registry by loading indicators from JSON file.
        
        Args:
            json_file_path: Path to JSON file. If None, uses default 57BaseIndicators.json
        """
        if json_file_path is None:
            # Default to 57BaseIndicators.json in same directory
            current_dir = Path(__file__).parent
            json_file_path = current_dir / "57BaseIndicators.json"
        
        self.json_file_path = Path(json_file_path)
        self._indicators: Dict[int, IndicatorDefinition] = {}
        self._indicators_by_name: Dict[str, IndicatorDefinition] = {}
        self._indicators_by_group: Dict[str, List[IndicatorDefinition]] = {}
        
        self._load_indicators()
    
    def _load_indicators(self) -> None:
        """Load indicators from JSON file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            indicators_list = data.get("Base_Indicators_57", [])
            
            for ind_data in indicators_list:
                indicator = IndicatorDefinition(
                    id=ind_data.get("ID"),
                    indicator_name=ind_data.get("Indicator_Name", ""),
                    definition=ind_data.get("Definition", ""),
                    group=ind_data.get("Group", ""),
                    formula=ind_data.get("Formula"),
                    tt200_formula=ind_data.get("TT200_Formula"),
                    get_direct_from_db=ind_data.get("Get_Direct_From_DB"),
                    used_in_qgv=ind_data.get("Used_in_QGV"),
                    used_in_4m=ind_data.get("Used_in_4M"),
                    formula_in_qgv=ind_data.get("Formula_in_QGV"),
                    formula_in_4m=ind_data.get("Formula_in_4M"),
                    scoring_metric=ind_data.get("Scoring_Metric"),
                    weight_in_4m=ind_data.get("Weight_in_4M"),
                    weight_in_qgv=ind_data.get("Weight_in_QGV")
                )
                
                # Store in dictionaries for quick lookup
                self._indicators[indicator.id] = indicator
                self._indicators_by_name[indicator.indicator_name] = indicator
                
                # Group by category
                if indicator.group not in self._indicators_by_group:
                    self._indicators_by_group[indicator.group] = []
                self._indicators_by_group[indicator.group].append(indicator)
            
            try:
                print(f"✓ Loaded {len(self._indicators)} indicators from {self.json_file_path.name}")
            except UnicodeEncodeError:
                print(f"[OK] Loaded {len(self._indicators)} indicators from {self.json_file_path.name}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.json_file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading indicators: {e}")
    
    def get_by_id(self, indicator_id: int) -> Optional[IndicatorDefinition]:
        """Get indicator by ID."""
        return self._indicators.get(indicator_id)
    
    def get_by_name(self, indicator_name: str) -> Optional[IndicatorDefinition]:
        """Get indicator by name."""
        return self._indicators_by_name.get(indicator_name)
    
    def get_by_group(self, group: str) -> List[IndicatorDefinition]:
        """Get all indicators in a group."""
        return self._indicators_by_group.get(group, [])
    
    def get_all(self) -> List[IndicatorDefinition]:
        """Get all indicators sorted by ID."""
        return sorted(self._indicators.values(), key=lambda x: x.id)
    
    def get_direct_indicators(self) -> List[IndicatorDefinition]:
        """Get all direct indicators (Get_Direct_From_DB = 'yes')."""
        return [ind for ind in self._indicators.values() if ind.is_direct]
    
    def get_calculated_indicators(self) -> List[IndicatorDefinition]:
        """Get all calculated indicators (Get_Direct_From_DB != 'yes')."""
        return [ind for ind in self._indicators.values() if ind.is_calculated]
    
    def count(self) -> int:
        """Get total number of indicators."""
        return len(self._indicators)
    
    def __len__(self) -> int:
        """Get total number of indicators."""
        return len(self._indicators)
    
    def __repr__(self) -> str:
        return f"IndicatorRegistry({len(self._indicators)} indicators)"


# Global registry instance
_default_registry: Optional[IndicatorRegistry] = None


def get_registry(json_file_path: Optional[str] = None) -> IndicatorRegistry:
    """
    Get global registry instance (singleton pattern).
    
    Args:
        json_file_path: Path to JSON file. Only used on first call.
        
    Returns:
        IndicatorRegistry instance
    """
    global _default_registry
    
    if _default_registry is None:
        _default_registry = IndicatorRegistry(json_file_path)
    
    return _default_registry

