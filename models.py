import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class DemandForecaster:
    """
    A class to forecast product demand using historical order data.
    """
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        
    def prepare_data(self, orders, order_items):
        """
        Prepare data for demand forecasting by aggregating orders by date and product.
        
        Parameters:
            orders: DataFrame containing order information
            order_items: DataFrame containing order item details
            
        Returns:
            DataFrame with daily demand aggregated by product
        """
        # Merge order dates with order items
        merged_data = pd.merge(
            order_items, 
            orders[['order_id', 'order_date']], 
            on='order_id'
        )
        
        # Convert to datetime if not already
        merged_data['order_date'] = pd.to_datetime(merged_data['order_date']).dt.date
        
        # Aggregate by date and product
        daily_demand = merged_data.groupby(['order_date', 'product_id'])['quantity'].sum().reset_index()
        return daily_demand
    
    def train_linear_regression(self, product_id, daily_demand, days_to_forecast=30):
        """
        Train a linear regression model for a specific product
        
        Parameters:
            product_id: ID of the product to forecast
            daily_demand: DataFrame with daily demand data
            days_to_forecast: Number of days to forecast into the future
            
        Returns:
            Dictionary with forecast results
        """
        # Filter data for the specific product
        product_demand = daily_demand[daily_demand['product_id'] == product_id].copy()
        
        if len(product_demand) < 5:
            return {
                'product_id': product_id,
                'forecast': None,
                'message': 'Insufficient data for forecasting',
                'forecast_dates': None
            }
        
        # Sort by date
        product_demand.sort_values('order_date', inplace=True)
        
        # Create features based on day number
        product_demand['day_number'] = range(1, len(product_demand) + 1)
        
        # Scale the quantity
        product_demand['scaled_quantity'] = self.scaler.fit_transform(product_demand[['quantity']])
        
        # Prepare X and y
        X = product_demand[['day_number']].values
        y = product_demand['scaled_quantity'].values
        
        # Train linear regression model
        self.model = LinearRegression()
        self.model.fit(X, y)
        
        # Generate forecast days
        last_day = product_demand['day_number'].max()
        forecast_days = np.array(range(last_day + 1, last_day + days_to_forecast + 1))
        forecast_days = forecast_days.reshape(-1, 1)
        
        # Make predictions
        scaled_forecast = self.model.predict(forecast_days)
        
        # Inverse transform to get actual quantities
        forecast = self.scaler.inverse_transform(scaled_forecast.reshape(-1, 1))
        
        # Generate dates for the forecast
        last_date = product_demand['order_date'].max()
        if isinstance(last_date, str):
            last_date = pd.to_datetime(last_date).date()
        
        forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days_to_forecast + 1)]
        
        return {
            'product_id': product_id,
            'forecast': forecast.flatten(),
            'forecast_dates': forecast_dates,
            'message': 'Forecast generated successfully'
        }
    
    def train_arima(self, product_id, daily_demand, days_to_forecast=30):
        """
        Train an ARIMA model for a specific product
        
        Parameters:
            product_id: ID of the product to forecast
            daily_demand: DataFrame with daily demand data
            days_to_forecast: Number of days to forecast into the future
            
        Returns:
            Dictionary with forecast results
        """
        # Filter data for the specific product
        product_demand = daily_demand[daily_demand['product_id'] == product_id].copy()
        
        if len(product_demand) < 10:
            return {
                'product_id': product_id,
                'forecast': None,
                'message': 'Insufficient data for ARIMA forecasting',
                'forecast_dates': None
            }
        
        # Sort by date
        product_demand.sort_values('order_date', inplace=True)
        
        # Set date as index and resample to fill missing dates
        product_demand['order_date'] = pd.to_datetime(product_demand['order_date'])
        
        try:
            # Create a time series
            ts = product_demand.set_index('order_date')['quantity']
            
            # Train ARIMA model (1,1,1) is a common starting point
            model = ARIMA(ts, order=(1, 1, 1))
            model_fit = model.fit()
            
            # Forecast
            forecast = model_fit.forecast(steps=days_to_forecast)
            
            # Generate dates for the forecast
            last_date = product_demand['order_date'].max()
            forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days_to_forecast + 1)]
            
            return {
                'product_id': product_id,
                'forecast': forecast.values,
                'forecast_dates': forecast_dates,
                'message': 'ARIMA forecast generated successfully'
            }
        
        except Exception as e:
            return {
                'product_id': product_id,
                'forecast': None,
                'message': f'ARIMA forecasting error: {str(e)}',
                'forecast_dates': None
            }

class AnomalyDetector:
    """
    A class to detect anomalies in delivery times and inventory levels.
    """
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        
    def detect_delivery_anomalies(self, orders, shipments):
        """
        Detect anomalies in delivery times using Isolation Forest
        
        Parameters:
            orders: DataFrame containing order information
            shipments: DataFrame containing shipment details
            
        Returns:
            DataFrame with anomaly scores
        """
        # Merge orders and shipments
        data = pd.merge(orders, shipments, on='order_id', how='inner')
        
        # Calculate delivery time (in days)
        data['estimated_delivery_date'] = pd.to_datetime(data['estimated_delivery_date'])
        data['shipped_date'] = pd.to_datetime(data['shipped_date'])
        
        # Calculate expected transit time
        data['expected_transit_days'] = (data['estimated_delivery_date'] - data['shipped_date']).dt.days
        
        # Keep only relevant columns for anomaly detection
        features = data[['expected_transit_days']].copy()
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        # Fit the model
        self.model.fit(features)
        
        # Predict anomalies (-1 for anomalies, 1 for normal)
        data['is_anomaly'] = self.model.predict(features)
        data['anomaly_score'] = self.model.decision_function(features)
        
        # Convert to readable flag
        data['is_anomaly'] = data['is_anomaly'].map({1: 'Normal', -1: 'Anomaly'})
        
        return data[['order_id', 'shipment_id', 'expected_transit_days', 'is_anomaly', 'anomaly_score']]
    
    def detect_inventory_anomalies(self, inventory):
        """
        Detect anomalies in inventory levels using Isolation Forest
        
        Parameters:
            inventory: DataFrame containing inventory information
            
        Returns:
            DataFrame with anomaly scores
        """
        # Prepare features for anomaly detection
        inventory_copy = inventory.copy()
        
        # Calculate stock-to-reorder ratio
        inventory_copy['stock_to_reorder_ratio'] = inventory_copy['quantity_in_stock'] / inventory_copy['reorder_level']
        
        # Prepare features
        features = inventory_copy[['quantity_in_stock', 'reorder_level', 'stock_to_reorder_ratio']].copy()
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        # Fit the model
        self.model.fit(features)
        
        # Predict anomalies (-1 for anomalies, 1 for normal)
        inventory_copy['is_anomaly'] = self.model.predict(features)
        inventory_copy['anomaly_score'] = self.model.decision_function(features)
        
        # Convert to readable flag
        inventory_copy['is_anomaly'] = inventory_copy['is_anomaly'].map({1: 'Normal', -1: 'Anomaly'})
        
        return inventory_copy
