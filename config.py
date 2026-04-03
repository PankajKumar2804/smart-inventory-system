"""Configuration for Smart Inventory System."""

from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class InventoryConfig:
    """Configuration for inventory system."""
    
    # Database settings
    db_type: str = "sqlite"  # sqlite or postgresql
    db_path: str = "inventory.db"
    
    # Forecasting settings
    forecast_method: str = "exponential_smoothing"  # arima, lstm
    forecast_days: int = 30
    confidence_interval: float = 0.95
    lookback_period: int = 90
    
    # ABC Analysis settings
    pareto_ratio: float = 0.8
    metrics: list = field(default_factory=lambda: ["revenue", "quantity"])
    
    # Reorder settings
    lead_time_days: int = 7
    safety_stock_multiplier: float = 1.5
    
    # Performance tracking
    track_metrics: bool = True
    mape_threshold: float = 0.20
    
    # Logging
    log_level: str = "INFO"
    verbose: bool = False
    
    # Data
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
