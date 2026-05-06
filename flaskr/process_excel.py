import pandas as pd

# Function to process the inventory data
def process_data_inventory(df):
    df = df.fillna('')  # Fill missing values with empty string
    
    # Drop unnecessary columns
    columns_to_drop = ['Nos of PCS/Pallet', 'Safety Stock']
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Rename columns for consistency
    df = df.rename(columns={'Grand Total': 'Warehouse+Transit'})

    # List of numeric columns to convert
    numeric_columns = [
        'In Transit Stock', 'Warehouse Stock',
        'Qty Held against existing orders awaiting pickup', '0-30 Days', '31-60 Days',
        '61-90 Days', '91-120 Days', '121-180 Days', '181-240 Days', '>240 Days', 'Warehouse+Transit', 'Pcs per pallet'
    ]

    # Convert columns to numeric, coercing errors and filling NaNs with 0
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0).astype('Int64')

    # Filter out rows where 'Warehouse+Transit' is less than or equal to 0
    if 'Warehouse+Transit' in df.columns:
        df = df[df['Warehouse+Transit'] > 0]

    # Replace <NA> values with empty string
    df = df.replace('<NA>', '')

    return df

def process_data_transit(df):
    # Fill missing values with empty strings
    df = df.fillna('')

    # Filter rows where 'In Transit' is in transit
    if 'In Transit' in df.columns:
        df = df[df['In Transit'] == 'In Transit']

    # Drop unnecessary columns
    columns_to_drop = [
        'PO#', 'Date', 'Shipment type', 'Description ',
        'Pallet Dimensoin', 'SHIPMENT SR.NO', 'INV', 'ETA', 'POD', 'Status', 'month', 'Origin',
        'SOB', 'In Transit day', 'Customer name '
    ]
    df = df.drop(columns=columns_to_drop, errors='ignore')
    # Replace '<NA>' values with empty strings
    df = df.replace('<NA>', '')

    return df


def process_oor_data(df):
    # Fill missing values with empty strings
    df = df.fillna('')
    
    # Drop unnecessary columns (e.g., 'Stock at 2000')
    columns_to_drop = ['Stock at 2000']
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # List of numeric columns to convert
    numeric_columns = [
        'Ordered Quantity',
        'Delivered Quantity', 'Open Quantity', 'Stock in Virginia',
        'Stock in Transit', 'Stock at Indus', 'To be manufactured'
    ]

    # List of date columns to format
    date_columns = [
        'Date of receiving PO#', 'Customer Required Delivery Date', 'Indus Ship Date',
        'Actual Ship Date(First shipment date for partitial qty shipped)', 'ETA Virginia'
    ]

    # Convert date columns to datetime format and format to 'dd-MMM-yy'
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].fillna('')
            df[col] = df[col].dt.strftime('%d-%b-%y')  # Format the date as 'dd-MMM-yy'

    # Convert numeric columns to integers (handling NaNs)
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')   

    # Filter rows where 'Open Quantity' is greater than 0
    if 'Open Quantity' in df.columns:
        df = df[df['Open Quantity'] > 0]

    # Replace '<NA>' values with empty strings
    df = df.replace('<NA>', '')

    # Define the column mappings (Excel -> PostgreSQL)
    column_mappings = {
        'Customer Code': 'customer_code',
        'Customer PO#': 'customer_po_number',
        'Date of receiving PO#': 'date_of_receiving_po',
        'Customer Required Delivery Date': 'customer_required_delivery_date',
        'Sales Document': 'sales_document',
        'Sales Document Item': 'sales_document_item',
        'Customer Material': 'customer_material',
        'Indus Product': 'indus_product',
        'Ordered Quantity': 'ordered_quantity',
        'Delivered Quantity': 'delivered_quantity',
        'Open Quantity': 'open_quantity',
        'US Warehouse': 'stock_in_virginia',
        'In Transit': 'stock_in_transit',
        'Indus Warehouse': 'stock_at_indus',
        'Indus Ship Date': 'indus_ship_date',
        'Actual Customer': 'actual_customer',
        'To be Manufactured': 'to_be_manufactured',  # Adjusted mapping
    }

    # Rename columns to match PostgreSQL table
    df.rename(columns=column_mappings, inplace=True)

    # Retain only the columns relevant for insertion
    columns_to_keep = [
        'customer_code', 'customer_po_number', 'date_of_receiving_po',
        'customer_required_delivery_date', 'sales_document', 'sales_document_item',
        'customer_material', 'indus_product', 'ordered_quantity', 'delivered_quantity',
        'open_quantity', 'stock_in_virginia', 'stock_in_transit', 'stock_at_indus',
        'to_be_manufactured', 'indus_ship_date', 'actual_customer'
    ]
    df = df[columns_to_keep]

    # Assign None (NULL) to 'actual_ship_date' and 'eta_virginia' columns since they don't exist in the Excel file
    df['actual_ship_date'] = None
    df['eta_virginia'] = None

    return df

def process_data_int_stock(df):
    # Fill missing values with empty strings
    df = df.fillna('')

    # Drop unnecessary columns
    columns_to_drop = [
        'Warehouse', 'Lot', 'Category', 'Receipt Date',
        'Description', 'Status Qty', 'Unit', 'Alt 1 Unit', 'Days', 'Cross check','Aging'
    ]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Convert necessary columns to numeric (in case some contain strings)
    for col in ['Alt 1 Qty', 'Quantity', 'Qty Reserved', 'Grs Weight','Pallet size']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Pivot table
    df_pivot = df.pivot_table(
        index=['Customer Code', 'Item', 'Customer Part', 'Pallet size'],
        values=['Alt 1 Qty', 'Quantity', 'Qty Reserved', 'Grs Weight'],
        aggfunc='sum',
        fill_value=0
    )

    # Reset index if needed
    df_pivot = df_pivot.reset_index()

    return df_pivot
