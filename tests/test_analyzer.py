"""Tests for inventory system."""

import unittest
from analyzer import DemandForecaster, ABCAnalyzer

class TestDemandForecaster(unittest.TestCase):
    """Test suite for DemandForecaster."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.forecaster = DemandForecaster()
    
    def test_forecaster_initialization(self):
        """Test forecaster init."""
        self.assertIsNotNone(self.forecaster)
    
    def test_abc_analysis(self):
        """Test ABC analysis."""
        analyzer = ABCAnalyzer(pareto_ratio=0.8)
        self.assertIsNotNone(analyzer)

if __name__ == "__main__":
    unittest.main()
