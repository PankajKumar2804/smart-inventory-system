"""Example: Demand forecasting."""

from analyzer import DemandForecaster

def main():
    """Example demand forecast."""
    forecaster = DemandForecaster(method='exponential_smoothing')
    print("Demand Forecaster initialized")

if __name__ == "__main__":
    main()
