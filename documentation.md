# Supply Chain Management (SCM) Dashboard Documentation

## 1. Problem Analysis

### Problem Statement
**"Difficulty in tracking and monitoring orders and shipments, spotting delays and bottlenecks, and managing inventory levels."**

### Business Impact
Supply chain disruptions and inefficiencies have significant business impacts:
- **Revenue Loss**: Stockouts lead to missed sales opportunities
- **Increased Costs**: Expedited shipping for delayed orders, holding excess inventory
- **Customer Dissatisfaction**: Delivery delays damage brand reputation
- **Operational Inefficiency**: Manual tracking processes consume excessive time and resources

### SCM Areas Covered
1. **Order Management**: Tracking order status, volumes, and fulfillment rates
2. **Inventory Management**: Monitoring stock levels, identifying restock needs
3. **Logistics & Shipping**: Tracking shipments, identifying delivery delays
4. **Analytics**: Forecasting demand, detecting anomalies

## 2. Data Design

### Data Schema

The solution implements a relational data model with the following tables:

#### Products
- `product_id`: Unique identifier for products
- `product_name`: Name of the product
- `category`: Product category
- `unit_price`: Price per unit
- `supplier`: Product supplier

#### Customers
- `customer_id`: Unique identifier for customers
- `customer_name`: Name of the customer
- `email`: Customer email
- `phone`: Customer phone number
- `address`: Customer address
- `city`: Customer city
- `country`: Customer country

#### Inventory
- `product_id`: Foreign key to Products table
- `product_name`: Name of the product
- `quantity_in_stock`: Current available quantity
- `reorder_level`: Minimum threshold for reordering
- `last_restock_date`: Date of last inventory replenishment
- `warehouse_location`: Physical location of inventory

#### Orders
- `order_id`: Unique identifier for orders
- `customer_id`: Foreign key to Customers table
- `order_date`: Date the order was placed
- `status`: Order status (Processing, Shipped, Delivered, Cancelled)
- `estimated_delivery_date`: Expected delivery date
- `actual_delivery_date`: Actual date of delivery (if delivered)
- `total_amount`: Total monetary value of the order

#### Order Items
- `order_id`: Foreign key to Orders table
- `product_id`: Foreign key to Products table
- `quantity`: Number of units ordered
- `unit_price`: Price per unit at time of order
- `total_price`: Total price for the line item

#### Shipments
- `shipment_id`: Unique identifier for shipments
- `order_id`: Foreign key to Orders table
- `carrier`: Shipping carrier (FedEx, UPS, etc.)
- `tracking_number`: Shipment tracking number
- `shipped_date`: Date the order was shipped
- `expected_delivery_date`: Expected delivery date
- `current_status`: Current shipment status
- `actual_delivery_date`: Actual delivery date (if delivered)

### Relationships
- **Products to Inventory**: One-to-one relationship (each product has one inventory record)
- **Customers to Orders**: One-to-many relationship (a customer can place multiple orders)
- **Orders to Order Items**: One-to-many relationship (an order can contain multiple items)
- **Orders to Shipments**: One-to-one relationship (each order has one shipment record)
- **Products to Order Items**: One-to-many relationship (a product can be in multiple order items)

## 3. Sample Dataset Generation

The application generates realistic sample data using the Faker library and custom logic:

### Key features of the generated data:
- **Realistic patterns**: Order frequencies, delivery times, and inventory levels follow realistic patterns
- **Varied statuses**: Includes orders in different states (processing, shipped, delivered, cancelled)
- **Deliberate anomalies**: Contains some delayed shipments and stock issues for demonstration
- **Time consistency**: Ensures logical time sequences (order → ship → deliver)
- **Varied products and categories**: Creates diverse product catalog with different stock levels

## 4. Interactive Dashboard

The dashboard is built with Streamlit and includes the following components:

### KPI Section
- Total Orders
- On-Time Delivery Percentage
- Low Stock Items Count
- Delayed Shipments Count

### Orders Tab
- Order Status Distribution (pie chart)
- Orders Over Time (line chart)
- Top Products by Demand (bar chart)
- Orders data table

### Inventory Tab
- Top Products by Inventory Level (bar chart)
- Inventory Status Distribution (pie chart)
- Inventory data table with health metrics

### Shipments Tab
- Delivery Performance chart showing delays
- Shipment Status Breakdown
- Shipments data table

### Analytics Tab
- Demand Forecasting (Linear Regression or ARIMA)
- Anomaly Detection for delivery times and inventory levels

### Filtering Capabilities
- Date Range: Filter data by date period
- Product: Filter by specific product
- Order Status: Filter by order status
- Inventory Status: Filter by inventory level status

## 5. Machine Learning Integration

### Demand Forecasting
The dashboard implements two forecasting methods:

#### Linear Regression
- Uses day number as the feature to predict future demand
- Suitable for products with linear demand patterns
- Provides daily forecasts for the selected number of days

#### ARIMA (AutoRegressive Integrated Moving Average)
- Time series model that captures temporal dependencies
- Better for seasonal or cyclical demand patterns
- More sophisticated than linear regression for complex patterns

### Anomaly Detection
The dashboard uses Isolation Forest algorithm for anomaly detection:

#### Delivery Time Anomalies
- Identifies unusually long or short delivery times
- Helps spot potential logistics problems or carrier issues

#### Inventory Level Anomalies
- Identifies unusual stock-to-reorder ratios
- Helps spot potential inventory management issues
- Highlights products requiring attention

## 6. Usage Instructions

### Accessing the Dashboard
1. Run the application with `streamlit run app.py`
2. The dashboard will be available at http://localhost:5000

### Using Filters
- Use the sidebar to apply filters
- All visualizations and data tables will update dynamically

### Working with Analytics
1. **For Demand Forecasting**:
   - Select a product
   - Choose forecast days (7-90)
   - Select model (Linear Regression or ARIMA)
   - Click "Generate Forecast"

2. **For Anomaly Detection**:
   - Select anomaly type (Delivery Times or Inventory Levels)
   - Click "Detect Anomalies"

### Regenerating Data
- Click "Regenerate Sample Data" to create a fresh dataset
- This is useful for testing different scenarios

## 7. Implementation Details

### Code Structure
- **app.py**: Main Streamlit application
- **data_generator.py**: Generates sample data
- **models.py**: Machine learning models for forecasting and anomaly detection
- **utils.py**: Utility functions for data loading and processing
- **visualizations.py**: Functions for creating charts and graphs

### Technical Approach
- **Modular design**: Each component is in a separate module
- **Data persistence**: Generated data is saved as CSV files
- **Reactive UI**: Dashboard updates automatically when filters change
- **Error handling**: Graceful fallbacks when data is insufficient
