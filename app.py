import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Import custom modules
from data_generator import generate_sample_data
from utils import load_data, calculate_kpis, filter_data, calculate_inventory_health
from visualizations import (
    plot_inventory_levels, plot_inventory_status_pie, plot_order_status,
    plot_orders_over_time, plot_delivery_performance, plot_product_demand,
    plot_forecast_chart, plot_anomaly_detection
)
from models import DemandForecaster, AnomalyDetector

# Set page configuration
st.set_page_config(
    page_title="Order and inventory visibility",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.filters = {
        'date_range': None,
        'product_id': None,
        'status': None,
        'inventory_status': None
    }
    st.session_state.showing_forecast = False
    st.session_state.forecast_result = None
    st.session_state.showing_anomalies = False
    st.session_state.anomaly_results = None

# Main title
st.title("Order and inventory visibility")

# Sidebar
st.sidebar.header("Filters and Controls")

# Date range filter
st.sidebar.subheader("Date Range")
with st.sidebar.expander("Select Date Range", expanded=False):
    col1, col2 = st.columns(2)
    
    min_date = datetime.now() - timedelta(days=90)
    max_date = datetime.now()
    
    with col1:
        start_date = st.date_input("Start Date", min_date)
    
    with col2:
        end_date = st.date_input("End Date", max_date)
    
    if start_date and end_date:
        if start_date <= end_date:
            st.session_state.filters['date_range'] = (pd.to_datetime(start_date), pd.to_datetime(end_date))
        else:
            st.error("End date must be after start date")
            st.session_state.filters['date_range'] = None
    else:
        st.session_state.filters['date_range'] = None

# Product filter
st.sidebar.subheader("Product")
all_products = st.session_state.data['products']
product_options = ['All Products'] + list(all_products['product_name'].unique())
selected_product = st.sidebar.selectbox("Select Product", product_options)

if selected_product != 'All Products':
    product_id = all_products[all_products['product_name'] == selected_product]['product_id'].iloc[0]
    st.session_state.filters['product_id'] = product_id
else:
    st.session_state.filters['product_id'] = None

# Status filter
st.sidebar.subheader("Order Status")
all_statuses = ['All Statuses'] + list(st.session_state.data['orders']['status'].unique())
selected_status = st.sidebar.selectbox("Select Status", all_statuses)

if selected_status != 'All Statuses':
    st.session_state.filters['status'] = selected_status
else:
    st.session_state.filters['status'] = None

# Inventory status filter
st.sidebar.subheader("Inventory Status")
inventory_statuses = ['All', 'In Stock', 'Low Stock', 'Out of Stock']
selected_inventory_status = st.sidebar.selectbox("Select Inventory Status", inventory_statuses)

if selected_inventory_status != 'All':
    st.session_state.filters['inventory_status'] = selected_inventory_status
else:
    st.session_state.filters['inventory_status'] = None

# Apply filters
filtered_data = filter_data(st.session_state.data, st.session_state.filters)

# Calculate KPIs
kpis = calculate_kpis(filtered_data)

# Calculate inventory health metrics
inventory_health = calculate_inventory_health(filtered_data['inventory'])

# Machine Learning section
st.sidebar.markdown("---")
st.sidebar.header("Analytics")

# Demand Forecasting
with st.sidebar.expander("Demand Forecasting", expanded=False):
    st.write("Forecast product demand:")
    
    if st.session_state.filters['product_id']:
        selected_product_id = st.session_state.filters['product_id']
        selected_product_name = all_products[all_products['product_id'] == selected_product_id]['product_name'].iloc[0]
    else:
        # Let user select a product for forecasting
        forecast_product = st.selectbox(
            "Select Product for Forecast",
            all_products['product_name'],
            key="forecast_product_select"
        )
        selected_product_id = all_products[all_products['product_name'] == forecast_product]['product_id'].iloc[0]
        selected_product_name = forecast_product
    
    forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30)
    forecast_model = st.radio("Forecast Model", ["Linear Regression", "ARIMA"])
    
    if st.button("Generate Forecast"):
        st.session_state.showing_forecast = True
        
        # Prepare data for forecasting
        forecaster = DemandForecaster()
        orders = st.session_state.data['orders'] if isinstance(st.session_state.data['orders'], pd.DataFrame) else st.session_state.data['orders']['orders']
        order_items = st.session_state.data['order_items'] if 'order_items' in st.session_state.data else st.session_state.data['orders']['order_items']
        
        daily_demand = forecaster.prepare_data(orders, order_items)
        
        with st.spinner("Generating forecast..."):
            if forecast_model == "Linear Regression":
                st.session_state.forecast_result = forecaster.train_linear_regression(
                    selected_product_id, daily_demand, days_to_forecast=forecast_days
                )
            else:  # ARIMA
                st.session_state.forecast_result = forecaster.train_arima(
                    selected_product_id, daily_demand, days_to_forecast=forecast_days
                )

# Anomaly Detection
with st.sidebar.expander("Anomaly Detection", expanded=False):
    st.write("Detect anomalies in delivery times or inventory levels:")
    
    anomaly_type = st.radio("Anomaly Type", ["Delivery Times", "Inventory Levels"])
    
    if st.button("Detect Anomalies"):
        st.session_state.showing_anomalies = True
        
        # Initialize anomaly detector
        detector = AnomalyDetector()
        
        with st.spinner("Detecting anomalies..."):
            if anomaly_type == "Delivery Times":
                orders = filtered_data['orders']
                shipments = filtered_data['shipments']
                
                st.session_state.anomaly_results = {
                    'type': 'delivery',
                    'data': detector.detect_delivery_anomalies(orders, shipments)
                }
            else:  # Inventory Levels
                st.session_state.anomaly_results = {
                    'type': 'inventory',
                    'data': detector.detect_inventory_anomalies(inventory_health)
                }

# Regenerate Data button
st.sidebar.markdown("---")
if st.sidebar.button("Regenerate Sample Data"):
    with st.spinner("Regenerating sample data..."):
        # Generate new sample data
        new_data = generate_sample_data()
        
        # Save as CSV files
        for key, value in new_data.items():
            if isinstance(value, dict):
                for subkey, subdf in value.items():
                    subdf.to_csv(f"{subkey}.csv", index=False)
            else:
                value.to_csv(f"{key}.csv", index=False)
        
        # Update session state
        st.session_state.data = load_data()
        st.rerun()

# Main dashboard area
# KPI row
st.header("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Orders", 
        value=kpis['total_orders'],
        delta=None
    )

with col2:
    st.metric(
        label="On-Time Delivery", 
        value=f"{kpis['on_time_delivery_percentage']}%",
        delta=None
    )

with col3:
    st.metric(
        label="Low Stock Items", 
        value=kpis['low_stock_count'],
        delta=None
    )

with col4:
    st.metric(
        label="Delayed Shipments", 
        value=kpis['delayed_shipments'],
        delta=None
    )

# Dashboard tabs
tab1, tab2, tab3, tab4 = st.tabs(["Orders", "Inventory", "Shipments", "Analytics"])

# Orders tab
with tab1:
    st.subheader("Order Management")
    
    # Order charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_order_status(filtered_data['orders']), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_orders_over_time(filtered_data['orders']), use_container_width=True)
    
    # Order items demand
    st.plotly_chart(
        plot_product_demand(
            filtered_data.get('order_items', filtered_data['orders'].get('order_items', pd.DataFrame())), 
            filtered_data['products']
        ),
        use_container_width=True
    )
    
    # Orders data table
    with st.expander("View Orders Data", expanded=False):
        st.dataframe(filtered_data['orders'], use_container_width=True)

# Inventory tab
with tab2:
    st.subheader("Inventory Management")
    
    # Inventory charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_inventory_levels(inventory_health), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_inventory_status_pie(inventory_health), use_container_width=True)
    
    # Inventory data table
    with st.expander("View Inventory Data", expanded=False):
        st.dataframe(inventory_health, use_container_width=True)

# Shipments tab
with tab3:
    st.subheader("Shipments & Delivery Performance")
    
    # Delivery performance
    st.plotly_chart(plot_delivery_performance(filtered_data['orders']), use_container_width=True)
    
    # Shipment status breakdown
    if 'current_status' in filtered_data['shipments'].columns:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            shipment_status = filtered_data['shipments']['current_status'].value_counts()
            st.bar_chart(shipment_status)
    
    # Shipments data table
    with st.expander("View Shipments Data", expanded=False):
        st.dataframe(filtered_data['shipments'], use_container_width=True)

# Analytics tab
with tab4:
    st.subheader("Advanced Analytics")
    
    # Demand Forecasting
    if st.session_state.showing_forecast and st.session_state.forecast_result:
        st.write(f"### Demand Forecast for {selected_product_name}")
        
        forecast_result = st.session_state.forecast_result
        
        if forecast_result['forecast'] is not None:
            forecast_chart = plot_forecast_chart(forecast_result)
            if forecast_chart:
                st.plotly_chart(forecast_chart, use_container_width=True)
            
            st.write(f"**Forecast Message:** {forecast_result['message']}")
            
            # Display forecast data in a table
            forecast_data = {
                'Date': forecast_result['forecast_dates'],
                'Forecasted Demand': forecast_result['forecast']
            }
            forecast_df = pd.DataFrame(forecast_data)
            st.dataframe(forecast_df, use_container_width=True)
        else:
            st.warning(f"Insufficient data to forecast demand for {selected_product_name}. {forecast_result['message']}")
    
    # Anomaly Detection
    if st.session_state.showing_anomalies and st.session_state.anomaly_results:
        anomaly_results = st.session_state.anomaly_results
        
        if anomaly_results['type'] == 'delivery':
            st.write("### Delivery Time Anomalies")
            anomaly_chart = plot_anomaly_detection(anomaly_results['data'], data_type='delivery')
        else:
            st.write("### Inventory Level Anomalies")
            anomaly_chart = plot_anomaly_detection(anomaly_results['data'], data_type='inventory')
        
        if anomaly_chart:
            st.plotly_chart(anomaly_chart, use_container_width=True)
            
            # Calculate percentage of anomalies
            anomaly_count = sum(anomaly_results['data']['is_anomaly'] == 'Anomaly')
            total_count = len(anomaly_results['data'])
            anomaly_percentage = (anomaly_count / total_count) * 100 if total_count > 0 else 0
            
            st.write(f"**Detected {anomaly_count} anomalies ({anomaly_percentage:.1f}% of data points)**")
            
            # Display anomalies in a table
            anomalies_only = anomaly_results['data'][anomaly_results['data']['is_anomaly'] == 'Anomaly']
            if not anomalies_only.empty:
                st.dataframe(anomalies_only, use_container_width=True)
            else:
                st.info("No anomalies detected in the current data.")
        else:
            st.warning("Insufficient data for anomaly detection.")

# Footer
st.markdown("---")
st.caption("Supply Chain Management Dashboard - Built with Streamlit")
