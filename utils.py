import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_data():
    """
    Load data from CSV files if they exist, otherwise generate new sample data.
    
    Returns:
        Dictionary containing DataFrames for products, customers, orders, inventory, and shipments
    """
    # Check if data files exist
    data_files = {
        'products': 'products.csv',
        'customers': 'customers.csv',
        'inventory': 'inventory.csv',
        'orders': 'orders.csv',
        'order_items': 'order_items.csv',
        'shipments': 'shipments.csv'
    }
    
    data = {}
    missing_files = False
    
    for key, filename in data_files.items():
        if os.path.exists(filename):
            try:
                data[key] = pd.read_csv(filename)
                # Convert date columns to datetime
                if key == 'orders':
                    for col in ['order_date', 'estimated_delivery_date', 'actual_delivery_date']:
                        if col in data[key].columns:
                            data[key][col] = pd.to_datetime(data[key][col])
                elif key == 'shipments':
                    for col in ['shipped_date', 'expected_delivery_date', 'actual_delivery_date']:
                        if col in data[key].columns:
                            data[key][col] = pd.to_datetime(data[key][col])
                elif key == 'inventory':
                    if 'last_restock_date' in data[key].columns:
                        data[key]['last_restock_date'] = pd.to_datetime(data[key]['last_restock_date'])
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                missing_files = True
        else:
            missing_files = True
    
    if missing_files:
        # Import data generator only when needed to avoid circular imports
        from data_generator import generate_sample_data
        
        # Generate new sample data
        generated_data = generate_sample_data()
        
        # Unpack orders data
        if 'orders' in generated_data:
            if isinstance(generated_data['orders'], dict):
                data['orders'] = generated_data['orders']['orders']
                data['order_items'] = generated_data['orders']['order_items']
            else:
                data['orders'] = generated_data['orders']
        
        # Add other dataframes
        for key in ['products', 'customers', 'inventory', 'shipments']:
            if key in generated_data:
                data[key] = generated_data[key]
        
        # Save data to CSV files
        for key, df in data.items():
            df.to_csv(f"{key}.csv", index=False)
    
    return data

def calculate_kpis(data):
    """
    Calculate key performance indicators from the data.
    
    Parameters:
        data: Dictionary containing DataFrames for orders, inventory, and shipments
        
    Returns:
        Dictionary of KPIs
    """
    orders = data['orders']
    inventory = data['inventory']
    shipments = data.get('shipments', pd.DataFrame())
    order_items = data.get('order_items', pd.DataFrame())
    
    kpis = {}
    
    # Order KPIs
    kpis['total_orders'] = len(orders)
    kpis['orders_by_status'] = orders['status'].value_counts().to_dict()
    
    # Calculate on-time delivery percentage
    if 'actual_delivery_date' in orders.columns and 'estimated_delivery_date' in orders.columns:
        delivered_orders = orders[orders['status'] == 'Delivered'].copy()
        if len(delivered_orders) > 0:
            delivered_orders['on_time'] = delivered_orders['actual_delivery_date'] <= delivered_orders['estimated_delivery_date']
            kpis['on_time_delivery_percentage'] = round(delivered_orders['on_time'].mean() * 100, 2)
        else:
            kpis['on_time_delivery_percentage'] = 0
    else:
        kpis['on_time_delivery_percentage'] = 0
    
    # Inventory KPIs
    kpis['total_products'] = len(inventory)
    kpis['low_stock_count'] = len(inventory[inventory['quantity_in_stock'] <= inventory['reorder_level']])
    kpis['out_of_stock_count'] = len(inventory[inventory['quantity_in_stock'] == 0])
    
    # Shipment KPIs
    if not shipments.empty and 'current_status' in shipments.columns:
        kpis['shipments_by_status'] = shipments['current_status'].value_counts().to_dict()
        kpis['total_shipments'] = len(shipments)
        
        # Calculate delayed shipments
        if 'expected_delivery_date' in shipments.columns:
            shipments_with_date = shipments.copy()
            shipments_with_date['expected_delivery_date'] = pd.to_datetime(shipments_with_date['expected_delivery_date'])
            today = pd.to_datetime(datetime.now())
            
            delayed_count = len(shipments_with_date[
                (shipments_with_date['current_status'] != 'Delivered') & 
                (shipments_with_date['expected_delivery_date'] < today)
            ])
            kpis['delayed_shipments'] = delayed_count
        else:
            kpis['delayed_shipments'] = 0
    else:
        kpis['shipments_by_status'] = {}
        kpis['total_shipments'] = 0
        kpis['delayed_shipments'] = 0
    
    # Order value KPIs
    if 'total_amount' in orders.columns:
        kpis['total_order_value'] = round(orders['total_amount'].sum(), 2)
        kpis['average_order_value'] = round(orders['total_amount'].mean(), 2)
    elif not order_items.empty and 'total_price' in order_items.columns:
        kpis['total_order_value'] = round(order_items['total_price'].sum(), 2)
        kpis['average_order_value'] = round(order_items['total_price'].sum() / kpis['total_orders'], 2) if kpis['total_orders'] > 0 else 0
    else:
        kpis['total_order_value'] = 0
        kpis['average_order_value'] = 0
    
    return kpis

def calculate_inventory_health(inventory):
    """
    Calculate inventory health indicators.
    
    Parameters:
        inventory: DataFrame containing inventory information
        
    Returns:
        DataFrame with additional inventory health metrics
    """
    inventory_health = inventory.copy()
    
    # Calculate days of supply based on average daily demand (assume 30-day period)
    # For simplicity, we'll use a random but consistent daily demand between 1-5 units
    np.random.seed(42)  # For consistent results
    inventory_health['avg_daily_demand'] = np.random.uniform(1, 5, size=len(inventory))
    
    # Calculate days of supply
    inventory_health['days_of_supply'] = (inventory_health['quantity_in_stock'] / 
                                           inventory_health['avg_daily_demand']).round(0)
    
    # Determine stock status
    conditions = [
        inventory_health['quantity_in_stock'] == 0,
        inventory_health['quantity_in_stock'] < inventory_health['reorder_level'],
        inventory_health['quantity_in_stock'] >= inventory_health['reorder_level']
    ]
    choices = ['Out of Stock', 'Low Stock', 'In Stock']
    inventory_health['stock_status'] = np.select(conditions, choices, default='Unknown')
    
    return inventory_health

def filter_data(data, filters):
    """
    Apply filters to the data.
    
    Parameters:
        data: Dictionary containing DataFrames
        filters: Dictionary of filter criteria
        
    Returns:
        Dictionary of filtered DataFrames
    """
    filtered_data = {}
    
    for key, df in data.items():
        filtered_df = df.copy()
        
        # Apply date range filter to orders and shipments
        if key in ['orders', 'shipments'] and 'date_range' in filters and filters['date_range']:
            date_col = 'order_date' if key == 'orders' else 'shipped_date'
            if date_col in filtered_df.columns:
                start_date, end_date = filters['date_range']
                filtered_df = filtered_df[(filtered_df[date_col] >= start_date) & 
                                          (filtered_df[date_col] <= end_date)]
        
        # Apply product filter
        if 'product_id' in filters and filters['product_id']:
            if key == 'inventory' and 'product_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['product_id'] == filters['product_id']]
            elif key == 'order_items' and 'product_id' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['product_id'] == filters['product_id']]
            elif key == 'orders' and 'order_id' in filtered_df.columns:
                # Get order IDs that contain the filtered product
                order_items = data.get('order_items', pd.DataFrame())
                if not order_items.empty and 'product_id' in order_items.columns:
                    filtered_order_ids = order_items[order_items['product_id'] == filters['product_id']]['order_id'].unique()
                    filtered_df = filtered_df[filtered_df['order_id'].isin(filtered_order_ids)]
        
        # Apply status filter to orders and shipments
        if 'status' in filters and filters['status']:
            if key == 'orders' and 'status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['status'] == filters['status']]
            elif key == 'shipments' and 'current_status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['current_status'] == filters['status']]
        
        # Apply inventory status filter
        if 'inventory_status' in filters and filters['inventory_status']:
            if key == 'inventory':
                if filters['inventory_status'] == 'Low Stock':
                    filtered_df = filtered_df[filtered_df['quantity_in_stock'] <= filtered_df['reorder_level']]
                elif filters['inventory_status'] == 'Out of Stock':
                    filtered_df = filtered_df[filtered_df['quantity_in_stock'] == 0]
                elif filters['inventory_status'] == 'In Stock':
                    filtered_df = filtered_df[filtered_df['quantity_in_stock'] > filtered_df['reorder_level']]
        
        filtered_data[key] = filtered_df
    
    return filtered_data
