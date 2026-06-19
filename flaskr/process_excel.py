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

    # Drop columns not needed for DB insertion (plant 2000 and production ship date)
    columns_to_drop = ['Stock at 2000', '2000', 'Indus Ship Date (Production)']
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Rename columns FIRST so all subsequent processing uses snake_case names
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
        '3001': 'stock_in_virginia',
        '3003': 'stock_in_transit',
        '1000': 'stock_at_indus',
        'To be Manufactured': 'to_be_manufactured',
        'Indus Ship Date': 'indus_ship_date',
        'Actual Customer': 'actual_customer',
    }
    df.rename(columns=column_mappings, inplace=True)

    # Convert numeric columns AFTER rename (snake_case names guaranteed to exist)
    numeric_columns = [
        'ordered_quantity', 'delivered_quantity', 'open_quantity',
        'stock_in_virginia', 'stock_in_transit', 'stock_at_indus',
        'to_be_manufactured'
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')

    # Convert date columns AFTER rename -- keep as datetime objects (None for empty/invalid)
    date_columns = [
        'date_of_receiving_po',
        'customer_required_delivery_date',
        'indus_ship_date',
    ]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].where(df[col].notna(), other=None)

    # Filter rows where open_quantity > 0
    if 'open_quantity' in df.columns:
        df = df[df['open_quantity'] > 0]

    # Replace '<NA>' values with empty strings
    df = df.replace('<NA>', '')

    # Retain only the columns relevant for DB insertion
    columns_to_keep = [
        'customer_code', 'customer_po_number', 'date_of_receiving_po',
        'customer_required_delivery_date', 'sales_document', 'sales_document_item',
        'customer_material', 'indus_product', 'ordered_quantity', 'delivered_quantity',
        'open_quantity', 'stock_in_virginia', 'stock_in_transit', 'stock_at_indus',
        'to_be_manufactured', 'indus_ship_date', 'actual_customer'
    ]
    df = df[columns_to_keep]

    # These don't exist in the Excel -- insert as NULL
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
