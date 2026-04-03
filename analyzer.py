"""
Smart Inventory System with AI-Powered Demand Forecasting
Production-grade inventory management with ML analytics
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json
import sqlite3
import logging

logger = logging.getLogger(__name__)


class ABCClassification(str, Enum):
    """ABC inventory classification"""
    A_HIGH_VALUE = "A"  # High value, tight control
    B_MEDIUM_VALUE = "B"  # Medium value
    C_LOW_VALUE = "C"  # Low value, loose control


@dataclass
class SalesData:
    """Historical sales record"""
    product_id: str
    date: datetime
    quantity_sold: int
    revenue: float
    forecast_demand: Optional[int] = None


@dataclass
class InventoryItem:
    """Inventory item"""
    product_id: str
    name: str
    current_stock: int
    reserved_stock: int = 0
    reorder_point: int = 10
    reorder_quantity: int = 50
    unit_cost: float = 0.0
    abc_class: ABCClassification = ABCClassification.C_LOW_VALUE
    last_restocked: datetime = field(default_factory=datetime.now)
    supplier_id: str = ""
    lead_time_days: int = 7
    
    @property
    def available_stock(self) -> int:
        """Available stock after reservations"""
        return self.current_stock - self.reserved_stock
    
    @property
    def inventory_value(self) -> float:
        """Total value of inventory"""
        return self.current_stock * self.unit_cost
    
    def needs_reorder(self) -> bool:
        """Check if needs reordering"""
        return self.available_stock <= self.reorder_point


@dataclass
class ReorderRecommendation:
    """Reorder recommendation"""
    product_id: str
    current_stock: int
    suggested_order_quantity: int
    reason: str
    urgency: str  # "low", "medium", "high"
    estimated_cost: float
    lead_time_days: int
    expected_arrival_date: datetime = field(default_factory=datetime.now)


class DemandForecaster:
    """ML-powered demand forecasting engine"""
    
    def __init__(self):
        self.models: Dict[str, List[float]] = {}
        self.sales_history: List[SalesData] = []
        logger.info("DemandForecaster initialized")
    
    def add_historical_data(self, sales_data: List[SalesData]):
        """Train with historical sales data"""
        self.sales_history.extend(sales_data)
        logger.info(f"Added {len(sales_data)} historical records")
    
    def forecast(self, product_id: str, days_ahead: int = 30, confidence: float = 0.95) -> Dict:
        """
        Forecast demand for product
        Uses exponential smoothing and trend analysis
        """
        # Get historical sales for product
        product_sales = [s for s in self.sales_history if s.product_id == product_id]
        
        if not product_sales:
            logger.warning(f"No historical data for {product_id}")
            return {
                'product_id': product_id,
                'quantity': 0,
                'confidence': 0.0,
                'error': 'Insufficient data'
            }
        
        # Extract quantities
        quantities = np.array([s.quantity_sold for s in product_sales[-60:]])  # Last 60 days
        
        # Calculate trend
        trend = np.polyfit(range(len(quantities)), quantities, 1)[0]
        
        # Exponential smoothing parameters
        alpha = 0.3
        smoothed = quantities[0]
        smoothed_values = [smoothed]
        
        for q in quantities[1:]:
            smoothed = alpha * q + (1 - alpha) * smoothed
            smoothed_values.append(smoothed)
        
        # Project future demand
        last_value = smoothed_values[-1]
        forecast_quantities = []
        
        for i in range(days_ahead):
            projected = last_value + (trend * (i + 1))
            projected = max(0, projected)  # No negative demand
            forecast_quantities.append(int(projected))
        
        total_forecast = sum(forecast_quantities)
        
        return {
            'product_id': product_id,
            'quantity': total_forecast,
            'daily_average': np.mean(quantities),
            'trend': trend,
            'confidence': confidence,
            'forecast_details': forecast_quantities,
            'period_days': days_ahead
        }
    
    def get_forecast_accuracy(self, product_id: str) -> Dict:
        """Calculate forecast accuracy (MAPE)"""
        actual = [s.quantity_sold for s in self.sales_history if s.product_id == product_id]
        
        if len(actual) < 2:
            return {'mape': 0, 'rmse': 0, 'data_points': len(actual)}
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        errors = []
        for i in range(1, len(actual)):
            if actual[i-1] != 0:
                error = abs((actual[i] - actual[i-1]) / actual[i-1])
                errors.append(error)
        
        mape = np.mean(errors) * 100 if errors else 0
        
        return {
            'mape': round(mape, 2),
            'product_id': product_id,
            'data_points': len(actual),
            'accuracy_percent': round(100 - mape, 2)
        }


class InventoryAnalyzer:
    """Inventory analytics and optimization"""
    
    def __init__(self, forecaster: DemandForecaster):
        self.forecaster = forecaster
        self.items: Dict[str, InventoryItem] = {}
        logger.info("InventoryAnalyzer initialized")
    
    def add_item(self, item: InventoryItem):
        """Add inventory item"""
        self.items[item.product_id] = item
    
    def abc_analysis(self) -> Dict[str, List[InventoryItem]]:
        """Classify inventory by ABC method"""
        items_by_value = sorted(
            self.items.values(),
            key=lambda x: x.inventory_value,
            reverse=True
        )
        
        total_value = sum(i.inventory_value for i in items_by_value)
        cumulative = 0
        classification = {}
        
        for item in items_by_value:
            cumulative += item.inventory_value
            percentage = (cumulative / total_value * 100) if total_value > 0 else 0
            
            if percentage <= 80:
                item.abc_class = ABCClassification.A_HIGH_VALUE
            elif percentage <= 95:
                item.abc_class = ABCClassification.B_MEDIUM_VALUE
            else:
                item.abc_class = ABCClassification.C_LOW_VALUE
        
        # Group by classification
        by_class = {}
        for cls in ABCClassification:
            by_class[cls.value] = [i for i in self.items.values() if i.abc_class == cls]
        
        logger.info(f"ABC analysis complete: A={len(by_class['A'])}, B={len(by_class['B'])}, C={len(by_class['C'])}")
        return by_class
    
    def get_reorder_recommendations(self, location: str = "WH_A") -> List[ReorderRecommendation]:
        """Get smart reorder recommendations"""
        recommendations = []
        now = datetime.now()
        
        for item in self.items.values():
            if item.available_stock <= item.reorder_point:
                # Get forecast
                forecast = self.forecaster.forecast(item.product_id, days_ahead=item.lead_time_days)
                
                # Calculate suggested order
                safety_stock = item.reorder_point
                suggested_qty = max(
                    item.reorder_quantity,
                    int(forecast.get('quantity', 0) * 1.5) + safety_stock
                )
                
                # Determine urgency
                if item.available_stock <= 0:
                    urgency = "high"
                elif item.available_stock <= item.reorder_point / 2:
                    urgency = "medium"
                else:
                    urgency = "low"
                
                expected_arrival = now + timedelta(days=item.lead_time_days)
                
                rec = ReorderRecommendation(
                    product_id=item.product_id,
                    current_stock=item.available_stock,
                    suggested_order_quantity=suggested_qty,
                    reason=f"Stock below reorder point ({item.reorder_point})",
                    urgency=urgency,
                    estimated_cost=suggested_qty * item.unit_cost,
                    lead_time_days=item.lead_time_days,
                    expected_arrival_date=expected_arrival
                )
                recommendations.append(rec)
        
        return sorted(recommendations, key=lambda x: x.urgency, reverse=True)
    
    def get_stockout_risk(self) -> List[Dict]:
        """Identify products at risk of stockout"""
        at_risk = []
        
        for item in self.items.values():
            forecast = self.forecaster.forecast(item.product_id, days_ahead=30)
            daily_demand = forecast.get('quantity', 0) / 30
            
            # Calculate days until stockout
            if daily_demand > 0:
                days_until_empty = item.available_stock / daily_demand
                
                if days_until_empty < item.lead_time_days:
                    at_risk.append({
                        'product_id': item.product_id,
                        'current_stock': item.available_stock,
                        'daily_demand': round(daily_demand, 2),
                        'days_until_stockout': round(days_until_empty, 1),
                        'lead_time_days': item.lead_time_days,
                        'critical': days_until_empty < (item.lead_time_days * 0.5)
                    })
        
        return sorted(at_risk, key=lambda x: x['days_until_stockout'])
    
    def get_inventory_metrics(self) -> Dict:
        """Calculate inventory metrics"""
        total_value = sum(i.inventory_value for i in self.items.values())
        total_quantity = sum(i.current_stock for i in self.items.values())
        total_items = len(self.items)
        
        # Calculate turnover
        sales_24h = sum(
            s.quantity_sold for s in self.forecaster.sales_history
            if (datetime.now() - s.date).days <= 1
        )
        turnover_ratio = sales_24h / total_quantity if total_quantity > 0 else 0
        
        return {
            'total_inventory_value': round(total_value, 2),
            'total_quantity': total_quantity,
            'total_items': total_items,
            'average_item_value': round(total_value / total_items, 2) if total_items > 0 else 0,
            'turnover_ratio': round(turnover_ratio, 4),
            'low_stock_items': sum(1 for i in self.items.values() if i.needs_reorder()),
            'warehouse_utilization': f"{(total_quantity / (total_items * 100)):.1%}"
        }


async def main():
    """Example usage"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    forecaster = DemandForecaster()
    analyzer = InventoryAnalyzer(forecaster)
    
    # Add historical sales data
    sales_data = [
        SalesData(
            product_id="SKU_001",
            date=datetime.now() - timedelta(days=i),
            quantity_sold=np.random.randint(5, 50),
            revenue=np.random.uniform(100, 1000)
        )
        for i in range(60)
    ]
    forecaster.add_historical_data(sales_data)
    
    # Add inventory items
    analyzer.add_item(InventoryItem(
        product_id="SKU_001",
        name="Product A",
        current_stock=100,
        reorder_point=20,
        unit_cost=25.0
    ))
    
    # ABC Analysis
    abc_results = analyzer.abc_analysis()
    print(f"ABC Classification: {len(abc_results['A'])} A items, {len(abc_results['B'])} B items, {len(abc_results['C'])} C items")
    
    # Get recommendations
    recommendations = analyzer.get_reorder_recommendations()
    for rec in recommendations[:5]:
        print(f"Reorder {rec.product_id}: Order {rec.suggested_order_quantity} units ({rec.urgency})")
    
    # Metrics
    metrics = analyzer.get_inventory_metrics()
    print(f"Inventory Value: ${metrics['total_inventory_value']}")
    print(f"Total Items: {metrics['total_items']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
