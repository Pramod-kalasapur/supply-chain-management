import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

def generate_sample_data(num_products=20, num_customers=30, num_orders=150, num_shipments=150):
    """
    Generate sample data for the Supply Chain Management system.
    
    Parameters:
        num_products: Number of products to generate
        num_customers: Number of customers to generate
        num_orders: Number of orders to generate
        num_shipments: Number of shipments to generate
        
    Returns:
        Dictionary containing DataFrames for products, customers, orders, inventory, and shipments
    """
    print("Generating sample data...")
    
    # Generate products data
    products = generate_products(num_products)
    
    # Generate customers data
    customers = generate_customers(num_customers)
    
    # Generate inventory data
    inventory = generate_inventory(products)
    
    # Generate orders data
    orders = generate_orders(num_orders, products, customers)
    
    # Generate shipments data
    shipments = generate_shipments(orders)
    
    return {
        'products': products,
        'customers': customers,
        'inventory': inventory,
        'orders': orders,
        'shipments': shipments
    }

def generate_products(num_products):
    """Generate sample product data"""
    product_categories = ['Electronics', 'Clothing', 'Food', 'Furniture', 'Books']
    
    # Use a combination of adjective and noun for product names
    product_names = []
    for _ in range(num_products):
        adjective = fake.word()
        noun = random.choice(['Chair', 'Table', 'Lamp', 'Desk', 'Phone', 'Computer', 
                             'Tablet', 'Monitor', 'Keyboard', 'Headphones', 'Speaker',
                             'Shirt', 'Pants', 'Jacket', 'Shoes', 'Hat', 'Bag', 'Watch',
                             'Food Processor', 'Blender', 'Toaster', 'Microwave', 'Refrigerator'])
        product_names.append(f"{adjective.capitalize()} {noun}")
    
    product_data = {
        'product_id': [f'P{i:03d}' for i in range(1, num_products + 1)],
        'product_name': product_names,
        'category': [random.choice(product_categories) for _ in range(num_products)],
        'unit_price': [round(random.uniform(10, 1000), 2) for _ in range(num_products)],
        'supplier': [fake.company() for _ in range(num_products)]
    }
    
    return pd.DataFrame(product_data)

def generate_customers(num_customers):
    """Generate sample customer data"""
    customer_data = {
        'customer_id': [f'C{i:03d}' for i in range(1, num_customers + 1)],
        'customer_name': [fake.name() for _ in range(num_customers)],
        'email': [fake.email() for _ in range(num_customers)],
        'phone': [fake.phone_number() for _ in range(num_customers)],
        'address': [fake.address().replace('\n', ', ') for _ in range(num_customers)],
        'city': [fake.city() for _ in range(num_customers)],
        'country': [fake.country() for _ in range(num_customers)]
    }
    
    return pd.DataFrame(customer_data)

def generate_inventory(products):
    """Generate sample inventory data"""
    inventory_data = {
        'product_id': products['product_id'],
        'quantity_in_stock': [random.randint(0, 200) for _ in range(len(products))],
        'reorder_level': [random.randint(10, 50) for _ in range(len(products))],
        'last_restock_date': [fake.date_between(start_date='-60d', end_date='today') for _ in range(len(products))],
        'warehouse_location': [f'Warehouse-{random.choice(["A", "B", "C", "D"])}' for _ in range(len(products))]
    }
    
    # Merge with product information
    inventory_df = pd.DataFrame(inventory_data)
    inventory_df = pd.merge(inventory_df, products[['product_id', 'product_name']], on='product_id')
    
    return inventory_df

def generate_orders(num_orders, products, customers):
    """Generate sample order data"""
    statuses = ['Processing', 'Shipped', 'Delivered', 'Cancelled']
    status_weights = [0.2, 0.3, 0.4, 0.1]  # Probability weights
    
    today = datetime.now()
    
    order_data = {
        'order_id': [f'ORD{i:05d}' for i in range(1, num_orders + 1)],
        'customer_id': [random.choice(customers['customer_id']) for _ in range(num_orders)],
        'order_date': [fake.date_time_between(start_date='-90d', end_date='now') for _ in range(num_orders)],
        'status': random.choices(statuses, weights=status_weights, k=num_orders),
        'total_amount': [round(random.uniform(100, 5000), 2) for _ in range(num_orders)]
    }
    
    # Add estimated and actual delivery dates, accounting for occasional delays
    order_data['estimated_delivery_date'] = [
        order_date + timedelta(days=random.randint(3, 14)) 
        for order_date in order_data['order_date']
    ]
    
    order_data['actual_delivery_date'] = []
    for i in range(num_orders):
        if order_data['status'][i] == 'Delivered':
            # 70% on time, 30% delayed
            if random.random() < 0.7:
                actual_date = order_data['estimated_delivery_date'][i]
            else:
                delay_days = random.randint(1, 10)
                actual_date = order_data['estimated_delivery_date'][i] + timedelta(days=delay_days)
            order_data['actual_delivery_date'].append(actual_date)
        else:
            order_data['actual_delivery_date'].append(None)
    
    # Create order items
    order_items = []
    for order_id in order_data['order_id']:
        # Each order has 1-5 products
        num_items = random.randint(1, 5)
        selected_products = random.sample(list(products['product_id']), num_items)
        
        for product_id in selected_products:
            quantity = random.randint(1, 10)
            unit_price = products.loc[products['product_id'] == product_id, 'unit_price'].values[0]
            
            order_items.append({
                'order_id': order_id,
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': quantity * unit_price
            })
    
    orders_df = pd.DataFrame(order_data)
    order_items_df = pd.DataFrame(order_items)
    
    return {
        'orders': orders_df,
        'order_items': order_items_df
    }

def generate_shipments(orders):
    """Generate sample shipment data"""
    orders_df = orders['orders']
    shippable_orders = orders_df[orders_df['status'].isin(['Shipped', 'Delivered'])].copy()
    
    carriers = ['FedEx', 'UPS', 'DHL', 'USPS', 'Amazon Logistics']
    status_options = ['In Transit', 'Out for Delivery', 'Delivered', 'Delayed']
    
    shipment_data = {
        'shipment_id': [f'SHP{i:05d}' for i in range(1, len(shippable_orders) + 1)],
        'order_id': shippable_orders['order_id'].values,
        'carrier': [random.choice(carriers) for _ in range(len(shippable_orders))],
        'tracking_number': [fake.bothify(text='??##?#####?##?') for _ in range(len(shippable_orders))]
    }
    
    shipment_data['shipped_date'] = []
    shipment_data['expected_delivery_date'] = []
    shipment_data['current_status'] = []
    shipment_data['actual_delivery_date'] = []
    
    for i, order_id in enumerate(shipment_data['order_id']):
        order_row = orders_df[orders_df['order_id'] == order_id].iloc[0]
        
        # Shipped date is 1-3 days after order date
        shipped_date = order_row['order_date'] + timedelta(days=random.randint(1, 3))
        shipment_data['shipped_date'].append(shipped_date)
        
        # Expected delivery matches the order's estimated delivery date
        expected_delivery = order_row['estimated_delivery_date']
        shipment_data['expected_delivery_date'].append(expected_delivery)
        
        # Current status based on order status
        if order_row['status'] == 'Delivered':
            current_status = 'Delivered'
            actual_delivery = order_row['actual_delivery_date']
        else:
            # For shipped but not delivered, determine current status
            if shipped_date.date() == datetime.now().date():
                current_status = 'In Transit'
                actual_delivery = None
            elif expected_delivery < datetime.now():
                # Past expected date but not delivered
                if random.random() < 0.8:
                    current_status = 'Delayed'
                else:
                    current_status = 'Lost'
                actual_delivery = None
            else:
                status_probabilities = [0.7, 0.2, 0, 0.1]  # Transit, Out for Delivery, Delivered, Delayed
                current_status = random.choices(status_options, weights=status_probabilities)[0]
                actual_delivery = None
                
        shipment_data['current_status'].append(current_status)
        shipment_data['actual_delivery_date'].append(actual_delivery)
    
    return pd.DataFrame(shipment_data)

if __name__ == "__main__":
    # Test the data generation
    data = generate_sample_data()
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                print(f"{key} - {subkey}: {subvalue.shape}")
        else:
            print(f"{key}: {value.shape}")
