"""Smart Inventory System package."""

__version__ = "1.0.0"
__author__ = "Pankaj Kumar"

from .analyzer import DemandForecaster, ABCAnalyzer, PerformanceMetrics
from .inventory import InventoryManager

__all__ = ["DemandForecaster", "ABCAnalyzer", "PerformanceMetrics", "InventoryManager"]
