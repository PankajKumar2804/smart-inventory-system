"""Advanced demand forecasting with multiple algorithms."""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from loguru import logger

@dataclass
class ForecastResult:
    """Forecasting result with confidence intervals."""
    
    predictions: np.ndarray
    lower_ci: np.ndarray
    upper_ci: np.ndarray
    mape: float
    rmse: float
    algorithm: str
    confidence_level: float

class AdvancedForecaster:
    """Multiple forecasting algorithms with ensemble."""
    
    def __init__(self, lookback: int = 90, confidence: float = 0.95):
        """Initialize with multiple algorithms."""
        self.lookback = lookback
        self.confidence = confidence
        self.historical_data = []
        
    def add_historical_data(self, sales: List[float], dates: Optional[List[datetime]] = None):
        """Add historical sales data."""
        self.historical_data = sales[-self.lookback:]
    
    def forecast_arima(self, periods: int = 30) -> ForecastResult:
        """ARIMA forecasting with auto-fitting."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            data = np.array(self.historical_data)
            
            # Auto-fit ARIMA parameters
            p, d, q = self._find_best_arima_params(data)
            
            model = ARIMA(data, order=(p, d, q))
            results = model.fit()
            
            forecast = results.get_forecast(steps=periods)
            predictions = forecast.predicted_mean.values
            
            ci = forecast.conf_int(alpha=1-self.confidence)
            lower = ci.iloc[:, 0].values
            upper = ci.iloc[:, 1].values
            
            # Calculate metrics
            mape = self._calculate_mape(data, results.fittedvalues)
            rmse = np.sqrt(np.mean(results.resid**2))
            
            return ForecastResult(
                predictions=predictions,
                lower_ci=lower,
                upper_ci=upper,
                mape=mape,
                rmse=rmse,
                algorithm="ARIMA",
                confidence_level=self.confidence
            )
        except ImportError:
            logger.warning("statsmodels not available, using exponential smoothing")
            return self.forecast_exponential_smoothing(periods)
    
    def forecast_lstm(self, periods: int = 30) -> ForecastResult:
        """LSTM neural network forecasting."""
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            from tensorflow.keras.optimizers import Adam
            
            data = np.array(self.historical_data).reshape(-1, 1)
            scaler = self._get_scaler(data)
            scaled_data = scaler.transform(data)
            
            # Prepare sequences
            lookback_seq = 14
            X, y = [], []
            for i in range(len(scaled_data) - lookback_seq):
                X.append(scaled_data[i:i+lookback_seq])
                y.append(scaled_data[i+lookback_seq])
            
            X = np.array(X)
            y = np.array(y)
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, activation='relu', input_shape=(lookback_seq, 1)),
                Dropout(0.2),
                Dense(25, activation='relu'),
                Dense(1, activation='relu')
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            model.fit(X, y, epochs=50, batch_size=16, verbose=0)
            
            # Forecast
            last_sequence = scaled_data[-lookback_seq:].reshape(1, lookback_seq, 1)
            predictions = []
            
            for _ in range(periods):
                next_pred = model.predict(last_sequence, verbose=0)[0, 0]
                predictions.append(next_pred)
                last_sequence = np.append(last_sequence[:, 1:, :], [[[next_pred]]], axis=1)
            
            predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
            
            # Calculate uncertainty (simple method)
            residuals = data.flatten() - model.predict(X, verbose=0).flatten()
            std_error = np.std(residuals)
            
            z_score = stats.norm.ppf((1 + self.confidence) / 2)
            margin = z_score * std_error
            
            return ForecastResult(
                predictions=predictions,
                lower_ci=predictions - margin,
                upper_ci=predictions + margin,
                mape=self._calculate_mape(data.flatten(), model.predict(X, verbose=0).flatten()),
                rmse=np.sqrt(np.mean(residuals**2)),
                algorithm="LSTM",
                confidence_level=self.confidence
            )
        except ImportError:
            logger.warning("TensorFlow not available, falling back to exponential smoothing")
            return self.forecast_exponential_smoothing(periods)
    
    def forecast_exponential_smoothing(self, periods: int = 30) -> ForecastResult:
        """Triple exponential smoothing (Holt-Winters)."""
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            data = np.array(self.historical_data)
            
            # Determine seasonality
            season_length = min(12, len(data) // 2)
            
            model = ExponentialSmoothing(
                data,
                seasonal_periods=season_length,
                trend='add',
                seasonal='add'
            )
            results = model.fit()
            
            forecast = results.get_forecast(steps=periods)
            predictions = forecast.predicted_mean.values
            
            ci = forecast.conf_int(alpha=1-self.confidence)
            lower = ci.iloc[:, 0].values
            upper = ci.iloc[:, 1].values
            
            mape = self._calculate_mape(data, results.fittedvalues)
            rmse = np.sqrt(np.mean(results.resid**2))
            
            return ForecastResult(
                predictions=predictions,
                lower_ci=lower,
                upper_ci=upper,
                mape=mape,
                rmse=rmse,
                algorithm="ExponentialSmoothing",
                confidence_level=self.confidence
            )
        except ImportError:
            logger.warning("Using simple exponential smoothing")
            return self._simple_exponential_smoothing(periods)
    
    def forecast_ensemble(self, periods: int = 30) -> ForecastResult:
        """Ensemble forecast combining multiple algorithms."""
        results = []
        
        try:
            results.append(self.forecast_exponential_smoothing(periods))
        except Exception as e:
            logger.warning(f"Exponential smoothing failed: {e}")
        
        try:
            if len(self.historical_data) >= 50:
                results.append(self.forecast_arima(periods))
        except Exception as e:
            logger.warning(f"ARIMA failed: {e}")
        
        if len(results) == 0:
            results.append(self._simple_exponential_smoothing(periods))
        
        # Weighted ensemble (lower MAPE gets higher weight)
        weights = [1.0 / (r.mape + 0.01) for r in results]
        weights = np.array(weights) / np.sum(weights)
        
        ensemble_pred = np.average([r.predictions for r in results], axis=0, weights=weights)
        ensemble_lower = np.average([r.lower_ci for r in results], axis=0, weights=weights)
        ensemble_upper = np.average([r.upper_ci for r in results], axis=0, weights=weights)
        
        avg_mape = np.average([r.mape for r in results], weights=weights)
        
        return ForecastResult(
            predictions=ensemble_pred,
            lower_ci=ensemble_lower,
            upper_ci=ensemble_upper,
            mape=avg_mape,
            rmse=np.average([r.rmse for r in results], weights=weights),
            algorithm="Ensemble",
            confidence_level=self.confidence
        )
    
    @staticmethod
    def _find_best_arima_params(data: np.ndarray, max_p: int = 5, max_d: int = 2, max_q: int = 5) -> Tuple[int, int, int]:
        """Auto-fit ARIMA parameters using AIC."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            best_aic = np.inf
            best_order = (1, 0, 1)
            
            for p in range(max_p + 1):
                for d in range(max_d + 1):
                    for q in range(max_q + 1):
                        try:
                            model = ARIMA(data, order=(p, d, q))
                            results = model.fit()
                            if results.aic < best_aic:
                                best_aic = results.aic
                                best_order = (p, d, q)
                        except:
                            pass
            
            return best_order
        except:
            return (1, 0, 1)
    
    @staticmethod
    def _calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error."""
        mask = actual != 0
        return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
    
    def _simple_exponential_smoothing(self, periods: int = 30) -> ForecastResult:
        """Simple exponential smoothing."""
        data = np.array(self.historical_data)
        alpha = 0.3
        
        # Fit
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[i-1])
        
        # Forecast
        predictions = []
        last_value = result[-1]
        for _ in range(periods):
            predictions.append(last_value)
        
        predictions = np.array(predictions)
        std_error = np.std(np.array(result) - data)
        z_score = stats.norm.ppf((1 + self.confidence) / 2)
        margin = z_score * std_error
        
        return ForecastResult(
            predictions=predictions,
            lower_ci=predictions - margin,
            upper_ci=predictions + margin,
            mape=self._calculate_mape(data, np.array(result)),
            rmse=np.sqrt(np.mean((np.array(result) - data)**2)),
            algorithm="SimpleExponentialSmoothing",
            confidence_level=self.confidence
        )
    
    @staticmethod
    def _get_scaler(data: np.ndarray):
        """Get MinMaxScaler."""
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaler.fit(data)
        return scaler
