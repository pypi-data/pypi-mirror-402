"""
Time Series Analyzer for pattern recognition and trend analysis
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


class AnalysisType(Enum):
    TREND = "trend"
    SEASONALITY = "seasonality"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    FORECAST = "forecast"


@dataclass
class AnalysisResult:
    """Result of time series analysis"""
    analysis_type: AnalysisType
    measurement: str
    field: str
    start_time: datetime
    end_time: datetime
    results: Dict[str, Any]
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class TimeSeriesAnalyzer:
    """
    Advanced analyzer for time series data patterns and trends
    """

    def __init__(self, manager):
        """
        Initialize analyzer

        Args:
            manager: TimeSeriesManager instance
        """
        self.manager = manager
        self.logger = logging.getLogger(__name__)

    async def analyze_trends(self, measurement: str, field: str,
                           start_time: datetime, end_time: datetime,
                           backend_type) -> Dict[str, Any]:
        """
        Analyze trends in time series data

        Args:
            measurement: Measurement name
            field: Field name to analyze
            start_time: Analysis start time
            end_time: Analysis end time
            backend_type: Backend to query

        Returns:
            Analysis results dictionary
        """
        try:
            # Query data
            data = await self._get_time_series_data(measurement, field, start_time, end_time, backend_type)

            if not data:
                return {"error": "No data available for analysis"}

            # Convert to DataFrame for analysis
            df = self._create_dataframe(data)

            # Perform trend analysis
            trend_result = self._analyze_trend(df, field)

            # Perform seasonality analysis
            seasonal_result = self._analyze_seasonality(df, field)

            # Detect anomalies
            anomaly_result = self._detect_anomalies(df, field)

            return {
                "trend": trend_result,
                "seasonality": seasonal_result,
                "anomalies": anomaly_result,
                "data_points": len(df),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {"error": str(e)}

    async def _get_time_series_data(self, measurement: str, field: str,
                                  start_time: datetime, end_time: datetime,
                                  backend_type) -> List[Dict[str, Any]]:
        """
        Retrieve time series data for analysis

        Args:
            measurement: Measurement name
            field: Field name
            start_time: Start time
            end_time: End time
            backend_type: Backend type

        Returns:
            List of data points
        """
        if backend_type.value == "influxdb":
            query = f'''
            from(bucket: "default")
            |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => r._field == "{field}")
            |> sort(columns: ["_time"])
            '''
        elif backend_type.value == "questdb":
            query = f'''
            SELECT timestamp, {field}
            FROM {measurement}
            WHERE timestamp BETWEEN '{start_time.isoformat()}' AND '{end_time.isoformat()}'
            ORDER BY timestamp
            '''
        else:
            raise ValueError(f"Unsupported backend: {backend_type}")

        return await self.manager.query_data(query, backend_type)

    def _create_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Create pandas DataFrame from query results

        Args:
            data: Query result data

        Returns:
            Pandas DataFrame
        """
        records = []

        for record in data:
            if 'timestamp' in record:
                timestamp = record['timestamp']
                value = record.get('value', record.get(record.keys()[1] if len(record) > 1 else 'value', 0))
            else:
                # InfluxDB format
                timestamp = record.get('_time', record.get('timestamp'))
                value = record.get('_value', record.get('value', 0))

            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)

            records.append({
                'timestamp': timestamp,
                'value': float(value) if value is not None else 0.0
            })

        df = pd.DataFrame(records)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        return df

    def _analyze_trend(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """
        Analyze trend using linear regression

        Args:
            df: DataFrame with time series data
            field: Field name

        Returns:
            Trend analysis results
        """
        try:
            if len(df) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # Prepare data for regression
            X = np.arange(len(df)).reshape(-1, 1)
            y = df['value'].values

            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)

            # Calculate trend metrics
            slope = model.coef_[0]
            intercept = model.intercept_
            r_squared = model.score(X, y)

            # Determine trend direction
            if slope > 0.01:
                direction = "increasing"
            elif slope < -0.01:
                direction = "decreasing"
            else:
                direction = "stable"

            # Calculate trend strength
            trend_strength = abs(slope) / np.std(y) if np.std(y) > 0 else 0

            return {
                "direction": direction,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "trend_strength": trend_strength,
                "start_value": float(df['value'].iloc[0]),
                "end_value": float(df['value'].iloc[-1]),
                "change_percent": ((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100) if df['value'].iloc[0] != 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {"error": str(e)}

    def _analyze_seasonality(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """
        Analyze seasonality patterns

        Args:
            df: DataFrame with time series data
            field: Field name

        Returns:
            Seasonality analysis results
        """
        try:
            if len(df) < 24:  # Need at least 24 points for meaningful seasonality
                return {"detected": False, "reason": "Insufficient data for seasonality analysis"}

            # Resample to hourly if needed
            if len(df) > 1000:
                df_resampled = df.resample('H').mean()
            else:
                df_resampled = df

            # Check for daily seasonality
            daily_pattern = self._check_periodic_pattern(df_resampled, period=24)

            # Check for weekly seasonality
            weekly_pattern = self._check_periodic_pattern(df_resampled, period=168)  # 24*7

            return {
                "detected": daily_pattern["detected"] or weekly_pattern["detected"],
                "daily_seasonality": daily_pattern,
                "weekly_seasonality": weekly_pattern,
                "data_points_analyzed": len(df_resampled)
            }

        except Exception as e:
            self.logger.error(f"Error in seasonality analysis: {e}")
            return {"error": str(e)}

    def _check_periodic_pattern(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """
        Check for periodic patterns in data

        Args:
            df: DataFrame
            period: Period to check (in hours)

        Returns:
            Pattern detection results
        """
        try:
            if len(df) < period * 2:
                return {"detected": False, "reason": "Insufficient data for period analysis"}

            # Calculate autocorrelation
            autocorr = []
            for lag in range(1, min(period + 1, len(df) // 2)):
                corr = df['value'].autocorr(lag=lag)
                if not np.isnan(corr):
                    autocorr.append((lag, corr))

            if not autocorr:
                return {"detected": False, "reason": "No valid autocorrelation values"}

            # Find peaks in autocorrelation
            max_corr = max(autocorr, key=lambda x: abs(x[1]))

            detected = abs(max_corr[1]) > 0.5  # Threshold for detection

            return {
                "detected": detected,
                "period_hours": max_corr[0],
                "correlation": max_corr[1],
                "strength": abs(max_corr[1])
            }

        except Exception as e:
            return {"detected": False, "error": str(e)}

    def _detect_anomalies(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """
        Detect anomalies using statistical methods

        Args:
            df: DataFrame with time series data
            field: Field name

        Returns:
            Anomaly detection results
        """
        try:
            if len(df) < 10:
                return {"detected": False, "reason": "Insufficient data for anomaly detection"}

            values = df['value'].values

            # Method 1: Z-score based detection
            z_scores = np.abs(stats.zscore(values))
            z_score_anomalies = np.where(z_scores > 3)[0]  # 3 standard deviations

            # Method 2: IQR based detection
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            iqr_anomalies = np.where((values < Q1 - 1.5 * IQR) | (values > Q3 + 1.5 * IQR))[0]

            # Combine anomalies
            all_anomalies = set(z_score_anomalies) | set(iqr_anomalies)

            anomaly_details = []
            for idx in sorted(all_anomalies):
                timestamp = df.index[idx]
                value = values[idx]
                z_score = z_scores[idx] if idx < len(z_scores) else 0

                anomaly_details.append({
                    "timestamp": timestamp.isoformat(),
                    "value": float(value),
                    "z_score": float(z_score),
                    "index": int(idx)
                })

            return {
                "detected": len(anomaly_details) > 0,
                "count": len(anomaly_details),
                "anomalies": anomaly_details,
                "total_points": len(df),
                "anomaly_percentage": len(anomaly_details) / len(df) * 100
            }

        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return {"error": str(e)}

    async def analyze_correlation(self, measurement1: str, field1: str,
                                measurement2: str, field2: str,
                                start_time: datetime, end_time: datetime,
                                backend_type) -> Dict[str, Any]:
        """
        Analyze correlation between two time series

        Args:
            measurement1: First measurement
            field1: First field
            measurement2: Second measurement
            field2: Second field
            start_time: Analysis start time
            end_time: Analysis end time
            backend_type: Backend to query

        Returns:
            Correlation analysis results
        """
        try:
            # Get data for both series
            data1 = await self._get_time_series_data(measurement1, field1, start_time, end_time, backend_type)
            data2 = await self._get_time_series_data(measurement2, field2, start_time, end_time, backend_type)

            if not data1 or not data2:
                return {"error": "Insufficient data for correlation analysis"}

            df1 = self._create_dataframe(data1)
            df2 = self._create_dataframe(data2)

            # Align timestamps (simple approach - could be improved)
            common_index = df1.index.intersection(df2.index)
            if len(common_index) < 10:
                return {"error": "Insufficient overlapping data points"}

            series1 = df1.loc[common_index, 'value']
            series2 = df2.loc[common_index, 'value']

            # Calculate correlation
            pearson_corr, pearson_p = stats.pearsonr(series1, series2)
            spearman_corr, spearman_p = stats.spearmanr(series1, series2)

            # Determine correlation strength
            def get_correlation_strength(corr):
                abs_corr = abs(corr)
                if abs_corr >= 0.8:
                    return "strong"
                elif abs_corr >= 0.6:
                    return "moderate"
                elif abs_corr >= 0.3:
                    return "weak"
                else:
                    return "very_weak"

            return {
                "pearson_correlation": {
                    "coefficient": pearson_corr,
                    "p_value": pearson_p,
                    "strength": get_correlation_strength(pearson_corr),
                    "significant": pearson_p < 0.05
                },
                "spearman_correlation": {
                    "coefficient": spearman_corr,
                    "p_value": spearman_p,
                    "strength": get_correlation_strength(spearman_corr),
                    "significant": spearman_p < 0.05
                },
                "data_points": len(common_index),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Error in correlation analysis: {e}")
            return {"error": str(e)}

    async def forecast_values(self, measurement: str, field: str,
                            start_time: datetime, end_time: datetime,
                            forecast_periods: int, backend_type) -> Dict[str, Any]:
        """
        Simple forecasting using moving averages

        Args:
            measurement: Measurement name
            field: Field name
            start_time: Historical data start time
            end_time: Historical data end time
            forecast_periods: Number of periods to forecast
            backend_type: Backend to query

        Returns:
            Forecast results
        """
        try:
            data = await self._get_time_series_data(measurement, field, start_time, end_time, backend_type)

            if not data:
                return {"error": "No data available for forecasting"}

            df = self._create_dataframe(data)

            if len(df) < 10:
                return {"error": "Insufficient historical data for forecasting"}

            # Simple moving average forecast
            window_size = min(10, len(df) // 2)
            ma_forecast = df['value'].rolling(window=window_size).mean().iloc[-1]

            # Calculate trend
            recent_trend = (df['value'].iloc[-1] - df['value'].iloc[-window_size]) / window_size

            # Generate forecast
            last_timestamp = df.index[-1]
            forecast_values = []

            for i in range(1, forecast_periods + 1):
                # Estimate time interval
                time_diff = df.index[-1] - df.index[-2] if len(df) > 1 else timedelta(hours=1)
                forecast_time = last_timestamp + (time_diff * i)

                # Simple forecast: moving average + trend
                forecast_value = ma_forecast + (recent_trend * i)

                forecast_values.append({
                    "timestamp": forecast_time.isoformat(),
                    "value": float(forecast_value),
                    "method": "moving_average_with_trend"
                })

            return {
                "forecast": forecast_values,
                "method": "simple_moving_average",
                "window_size": window_size,
                "historical_points": len(df),
                "last_value": float(df['value'].iloc[-1]),
                "moving_average": float(ma_forecast),
                "trend": float(recent_trend)
            }

        except Exception as e:
            self.logger.error(f"Error in forecasting: {e}")
            return {"error": str(e)}