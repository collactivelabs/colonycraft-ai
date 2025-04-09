# Anomaly Detection

## Machine Learning for Anomaly Detection

The ColonyCraft AI platform implements automated anomaly detection using machine learning to identify unusual patterns and behaviors:

1. **Time Series Analysis**: Detecting unusual patterns in metrics
2. **Outlier Detection**: Identifying abnormal requests or user behavior
3. **Forecasting**: Predicting resource usage and capacity needs

## Time Series Anomaly Detection

Time series anomaly detection is implemented using Facebook's Prophet library:

```python
# Using Prophet for time series anomaly detection
from prophet import Prophet
import pandas as pd
import numpy as np

def detect_anomalies(metric_data, prediction_horizon=24):
    """
    Detect anomalies in time series data using Prophet
    
    Args:
        metric_data: DataFrame with 'ds' (timestamp) and 'y' (metric value)
        prediction_horizon: Hours to forecast
        
    Returns:
        DataFrame with anomalies
    """
    # Train Prophet model
    model = Prophet(
        interval_width=0.95,
        daily_seasonality=True,
        weekly_seasonality=True
    )
    model.fit(metric_data)
    
    # Make predictions
    future = model.make_future_dataframe(periods=prediction_horizon, freq='H')
    forecast = model.predict(future)
    
    # Combine forecast and actual values
    comparison = forecast.merge(metric_data, on='ds', how='left')
    
    # Calculate anomalies (values outside 95% prediction interval)
    comparison['anomaly'] = np.where(
        (comparison['y'] < comparison['yhat_lower']) | 
        (comparison['y'] > comparison['yhat_upper']), 
        True, False
    )
    
    # Return only anomalies
    return comparison[comparison['anomaly']]
```

This model is applied to key metrics including:

1. **Request Volume**: Unusual spikes or drops in request rate
2. **Error Rates**: Abnormal increase in error responses
3. **Response Time**: Unexpected latency increases
4. **Resource Usage**: Unusual patterns in CPU, memory, or storage utilization

## Multivariate Anomaly Detection

For more complex anomaly detection, a multivariate approach is used to identify correlations between different metrics:

```python
# Multivariate anomaly detection with Isolation Forest
from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np

def detect_multivariate_anomalies(metrics_df, contamination=0.05):
    """
    Detect anomalies across multiple metrics using Isolation Forest
    
    Args:
        metrics_df: DataFrame with multiple metric columns
        contamination: Expected proportion of anomalies
        
    Returns:
        DataFrame with anomaly flags
    """
    # Configure and train the model
    model = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=contamination,
        random_state=42
    )
    
    # Fit the model
    model.fit(metrics_df)
    
    # Predict anomalies
    # -1 for anomalies, 1 for normal data points
    metrics_df['anomaly'] = model.predict(metrics_df)
    metrics_df['anomaly'] = metrics_df['anomaly'].map({1: False, -1: True})
    
    # Add anomaly score
    metrics_df['anomaly_score'] = model.decision_function(metrics_df)
    metrics_df['anomaly_score'] = -1 * metrics_df['anomaly_score']
    
    return metrics_df
```

This approach is applied to detect complex anomalies such as:

1. **Resource Leaks**: Gradual increases in resource usage
2. **Service Degradation**: Subtle performance issues across multiple components
3. **Unusual User Behavior**: Potentially suspicious or fraudulent activities
4. **System Instability**: Early signs of cascading failures

## Pattern Recognition for LLM Behavior

Custom anomaly detection for LLM behavior is implemented to identify unusual patterns:

```python
def detect_llm_anomalies(llm_metrics_df):
    """
    Detect anomalies in LLM usage patterns
    
    Args:
        llm_metrics_df: DataFrame with LLM-specific metrics
        
    Returns:
        DataFrame with anomaly flags
    """
    # Calculate rolling statistics
    rolling_mean = llm_metrics_df['token_count'].rolling(window=24).mean()
    rolling_std = llm_metrics_df['token_count'].rolling(window=24).std()
    
    # Define upper and lower bounds (3 sigma)
    upper_bound = rolling_mean + 3 * rolling_std
    lower_bound = rolling_mean - 3 * rolling_std
    
    # Identify anomalies
    llm_metrics_df['anomaly'] = (
        (llm_metrics_df['token_count'] > upper_bound) | 
        (llm_metrics_df['token_count'] < lower_bound)
    )
    
    # Calculate additional metrics
    llm_metrics_df['token_efficiency'] = (
        llm_metrics_df['output_tokens'] / llm_metrics_df['input_tokens']
    )
    
    # Detect unusual efficiency patterns
    efficiency_mean = llm_metrics_df['token_efficiency'].mean()
    efficiency_std = llm_metrics_df['token_efficiency'].std()
    
    llm_metrics_df['efficiency_anomaly'] = (
        abs(llm_metrics_df['token_efficiency'] - efficiency_mean) > 3 * efficiency_std
    )
    
    return llm_metrics_df
```

## Proactive Monitoring

Machine learning models are used for proactive monitoring:

1. **Trend Analysis**: Identifying gradual degradation before it becomes critical
2. **Correlation**: Finding relationships between different metrics
3. **Seasonal Patterns**: Adjusting thresholds based on expected usage patterns

## Forecasting Resource Usage

Resource usage forecasting helps with capacity planning:

```python
def forecast_resource_usage(resource_data, forecast_days=30):
    """
    Forecast future resource usage for capacity planning
    
    Args:
        resource_data: DataFrame with resource usage history
        forecast_days: Number of days to forecast
        
    Returns:
        DataFrame with forecasted values
    """
    # Train forecasting model
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05
    )
    
    # Add special events
    for holiday in resource_data['holiday'].unique():
        if pd.notna(holiday):
            model.add_country_holidays(holiday)
    
    # Fit model
    model.fit(resource_data)
    
    # Create future dataframe
    future = model.make_future_dataframe(
        periods=forecast_days * 24,  # Hourly forecast
        freq='H'
    )
    
    # Make forecast
    forecast = model.predict(future)
    
    # Add confidence intervals
    forecast['yhat_upper_90'] = forecast['yhat'] + 1.645 * (forecast['yhat_upper'] - forecast['yhat'])
    forecast['yhat_lower_90'] = forecast['yhat'] - 1.645 * (forecast['yhat'] - forecast['yhat_lower'])
    
    return forecast
```

## Anomaly-Based Alerting

The anomaly detection system is integrated with the alerting system:

1. **Smart Thresholds**: Dynamic alerting thresholds based on historical patterns
2. **Anomaly Severity**: Ranking anomalies by their deviation from normal behavior
3. **Root Cause Analysis**: Correlating anomalies across different metrics to identify root causes

Example configuration for anomaly-based alerts:

```yaml
# Prometheus Alertmanager rules for anomaly detection
groups:
- name: AnomalyDetection
  rules:
  - alert: AnomalousRequestRate
    expr: abs(request_rate - predict_request_rate) / predict_request_rate > 0.3
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Anomalous request rate detected"
      description: "Request rate is deviating more than 30% from predicted values for 10 minutes"
      
  - alert: AnomalousLatency
    expr: response_time_p95 > predict_response_time_upper_bound
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Anomalous latency detected"
      description: "95th percentile response time is higher than predicted upper bound for 5 minutes"
```

## Anomaly Visualization

Dedicated dashboards visualize detected anomalies:

1. **Anomaly Timeline**: Historical view of detected anomalies
2. **Correlation View**: Relationships between different anomalies
3. **Forecast View**: Predicted metrics with confidence intervals

## Self-Tuning Thresholds

The anomaly detection system includes self-tuning capabilities:

1. **Feedback Loop**: Incorporating operator feedback on detected anomalies
2. **Adaptive Learning**: Automatically adjusting sensitivity based on false positive rates
3. **Seasonal Adjustment**: Learning and adapting to seasonal patterns in the data

```python
class AdaptiveAnomalyDetector:
    def __init__(self, initial_threshold=3.0, learning_rate=0.01):
        self.threshold = initial_threshold
        self.learning_rate = learning_rate
        self.false_positives = 0
        self.true_positives = 0
    
    def adjust_threshold(self, is_false_positive):
        """Adjust threshold based on feedback"""
        if is_false_positive:
            self.false_positives += 1
            # Increase threshold to reduce false positives
            self.threshold += self.learning_rate
        else:
            self.true_positives += 1
            # Decrease threshold if we're detecting true anomalies
            self.threshold = max(1.0, self.threshold - (self.learning_rate * 0.5))
    
    def detect_anomaly(self, value, expected_value, std_dev):
        """Detect if a value is anomalous based on current threshold"""
        z_score = abs(value - expected_value) / max(std_dev, 0.0001)
        return z_score > self.threshold
```

## Model Retraining

Anomaly detection models are regularly retrained to maintain accuracy:

1. **Scheduled Retraining**: Weekly retraining with the latest data
2. **Triggered Retraining**: Automatic retraining after system changes
3. **Model Versioning**: Tracking model versions and performance metrics

## Integration with Observability Pipeline

The anomaly detection system is fully integrated with the observability pipeline:

1. **Data Source**: Consuming metrics directly from Prometheus
2. **Alerting**: Sending anomaly alerts to Alertmanager
3. **Visualization**: Displaying anomalies in Grafana dashboards
4. **Storage**: Storing detected anomalies for historical analysis
