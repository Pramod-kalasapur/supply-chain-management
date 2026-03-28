import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

def plot_inventory_levels(inventory, top_n=10):
    """
    Create a bar chart showing inventory levels for top products.
    
    Parameters:
        inventory: DataFrame containing inventory information
        top_n: Number of products to show
        
    Returns:
        Plotly figure
    """
    # Sort by quantity in stock
    inventory_sorted = inventory.sort_values('quantity_in_stock', ascending=False).head(top_n)
    
    # Create figure
    fig = px.bar(
        inventory_sorted,
        x='product_name',
        y=['quantity_in_stock', 'reorder_level'],
        title=f'Top {top_n} Products by Inventory Level',
        labels={'value': 'Quantity', 'product_name': 'Product', 'variable': 'Metric'},
        color_discrete_map={'quantity_in_stock': '#3498db', 'reorder_level': '#e74c3c'},
        barmode='group'
    )
    
    fig.update_layout(
        height=500,
        legend_title_text='',
        xaxis={'categoryorder': 'total descending'}
    )
    
    return fig

def plot_inventory_status_pie(inventory):
    """
    Create a pie chart showing inventory status distribution.
    
    Parameters:
        inventory: DataFrame containing inventory information with stock_status column
        
    Returns:
        Plotly figure
    """
    # Count products by status
    if 'stock_status' not in inventory.columns:
        # Calculate stock status if not present
        conditions = [
            inventory['quantity_in_stock'] == 0,
            inventory['quantity_in_stock'] < inventory['reorder_level'],
            inventory['quantity_in_stock'] >= inventory['reorder_level']
        ]
        choices = ['Out of Stock', 'Low Stock', 'In Stock']
        inventory['stock_status'] = np.select(conditions, choices, default='Unknown')
    
    status_counts = inventory['stock_status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Define colors for each status
    colors = {
        'In Stock': '#2ecc71',  # Green
        'Low Stock': '#f39c12',  # Yellow/Orange
        'Out of Stock': '#e74c3c'  # Red
    }
    
    # Create figure
    fig = px.pie(
        status_counts, 
        values='Count', 
        names='Status',
        title='Inventory Status Distribution',
        color='Status',
        color_discrete_map=colors
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

def plot_order_status(orders):
    """
    Create a pie chart showing order status distribution.
    
    Parameters:
        orders: DataFrame containing order information
        
    Returns:
        Plotly figure
    """
    # Count orders by status
    status_counts = orders['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Define colors for each status
    colors = {
        'Delivered': '#2ecc71',  # Green
        'Shipped': '#3498db',    # Blue
        'Processing': '#f39c12', # Yellow/Orange
        'Cancelled': '#e74c3c'   # Red
    }
    
    # Create figure
    fig = px.pie(
        status_counts, 
        values='Count', 
        names='Status',
        title='Order Status Distribution',
        color='Status',
        color_discrete_map=colors
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

def plot_orders_over_time(orders, interval='day'):
    """
    Create a line chart showing orders over time.
    
    Parameters:
        orders: DataFrame containing order information
        interval: Time interval for aggregation ('day', 'week', 'month')
        
    Returns:
        Plotly figure
    """
    # Ensure order_date is datetime
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    
    # Group by time interval
    if interval == 'day':
        orders['date_group'] = orders['order_date'].dt.date
    elif interval == 'week':
        orders['date_group'] = orders['order_date'].dt.to_period('W').apply(lambda r: r.start_time)
    else:  # month
        orders['date_group'] = orders['order_date'].dt.to_period('M').apply(lambda r: r.start_time)
    
    # Count orders per interval
    orders_by_time = orders.groupby('date_group').size().reset_index()
    orders_by_time.columns = ['Date', 'Orders']
    
    # Create figure
    fig = px.line(
        orders_by_time, 
        x='Date', 
        y='Orders',
        title=f'Orders Over Time (by {interval.capitalize()})',
        markers=True
    )
    
    fig.update_layout(height=400, xaxis_title='Date', yaxis_title='Number of Orders')
    
    return fig

def plot_delivery_performance(orders):
    """
    Create charts showing delivery performance.
    
    Parameters:
        orders: DataFrame containing order information with delivery dates
        
    Returns:
        Plotly figure
    """
    # Filter for delivered orders
    delivered = orders[orders['status'] == 'Delivered'].copy()
    
    if len(delivered) == 0 or 'actual_delivery_date' not in delivered.columns:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            text="No delivery data available",
            showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Calculate delivery time (in days)
    delivered['estimated_delivery_date'] = pd.to_datetime(delivered['estimated_delivery_date'])
    delivered['actual_delivery_date'] = pd.to_datetime(delivered['actual_delivery_date'])
    delivered['order_date'] = pd.to_datetime(delivered['order_date'])
    
    delivered['delivery_time'] = (delivered['actual_delivery_date'] - delivered['order_date']).dt.days
    delivered['expected_time'] = (delivered['estimated_delivery_date'] - delivered['order_date']).dt.days
    delivered['delay'] = (delivered['actual_delivery_date'] - delivered['estimated_delivery_date']).dt.days
    delivered['on_time'] = delivered['delay'] <= 0
    
    # Calculate on-time percentage
    on_time_percent = delivered['on_time'].mean() * 100
    
    # Create a figure with two subplots
    fig = go.Figure()
    
    # Add histogram of delivery delays
    fig.add_trace(go.Histogram(
        x=delivered['delay'],
        name='Delivery Delays',
        marker_color='#3498db',
        autobinx=False,
        xbins=dict(start=-5, end=10, size=1)
    ))
    
    fig.update_layout(
        title_text=f'Delivery Performance (On-Time: {on_time_percent:.1f}%)',
        xaxis_title_text='Delay (Days)',
        yaxis_title_text='Number of Orders',
        height=400
    )
    
    return fig

def plot_product_demand(order_items, products):
    """
    Create a bar chart showing demand by product.
    
    Parameters:
        order_items: DataFrame containing order item details
        products: DataFrame containing product information
        
    Returns:
        Plotly figure
    """
    # Merge with product information
    if 'product_name' not in order_items.columns and not products.empty:
        merged = order_items.merge(products[['product_id', 'product_name']], on='product_id')
    else:
        merged = order_items
    
    # Aggregate by product
    product_demand = merged.groupby('product_id').agg(
        total_quantity=('quantity', 'sum'),
        product_name=('product_name', 'first')
    ).reset_index()
    
    # Sort by demand and get top 10
    product_demand = product_demand.sort_values('total_quantity', ascending=False).head(10)
    
    # Create figure
    fig = px.bar(
        product_demand,
        x='product_name',
        y='total_quantity',
        title='Top 10 Products by Demand',
        labels={'product_name': 'Product', 'total_quantity': 'Quantity Ordered'}
    )
    
    fig.update_layout(
        height=500,
        xaxis={'categoryorder': 'total descending'}
    )
    
    return fig

def plot_forecast_chart(forecast_result):
    """
    Create a line chart showing demand forecast.
    
    Parameters:
        forecast_result: Dictionary containing forecast data
        
    Returns:
        Plotly figure or None if forecast is not available
    """
    if not forecast_result or forecast_result['forecast'] is None:
        return None
    
    # Extract data
    forecast = forecast_result['forecast']
    dates = forecast_result['forecast_dates']
    
    # Create dataframe
    df = pd.DataFrame({
        'Date': dates,
        'Forecasted Demand': forecast
    })
    
    # Create figure
    fig = px.line(
        df, 
        x='Date', 
        y='Forecasted Demand',
        title=f"Demand Forecast for Product {forecast_result['product_id']}",
        markers=True
    )
    
    fig.update_layout(
        height=400, 
        xaxis_title='Date', 
        yaxis_title='Forecasted Quantity'
    )
    
    return fig

def plot_anomaly_detection(anomaly_data, data_type='delivery'):
    """
    Create a scatter plot showing anomalies.
    
    Parameters:
        anomaly_data: DataFrame containing anomaly detection results
        data_type: Type of data ('delivery' or 'inventory')
        
    Returns:
        Plotly figure
    """
    if anomaly_data.empty:
        return None
    
    if data_type == 'delivery':
        # Plot delivery time anomalies
        fig = px.scatter(
            anomaly_data,
            x='order_id',
            y='expected_transit_days',
            color='is_anomaly',
            title='Delivery Time Anomalies',
            labels={'expected_transit_days': 'Expected Transit Days', 'order_id': 'Order ID'},
            color_discrete_map={'Normal': '#3498db', 'Anomaly': '#e74c3c'}
        )
        
        fig.update_layout(height=400)
        
    else:
        # Plot inventory anomalies
        fig = px.scatter(
            anomaly_data,
            x='product_name',
            y='quantity_in_stock',
            size='stock_to_reorder_ratio',
            color='is_anomaly',
            title='Inventory Level Anomalies',
            labels={
                'quantity_in_stock': 'Quantity in Stock', 
                'product_name': 'Product',
                'stock_to_reorder_ratio': 'Stock to Reorder Ratio'
            },
            color_discrete_map={'Normal': '#3498db', 'Anomaly': '#e74c3c'}
        )
        
        fig.update_layout(height=500)
    
    return fig
