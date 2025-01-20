import pandas as pd

# Function to process the inventory data
def process_data_inventory(df):
    df = df.fillna('')  # Fill missing values with empty string
    
    # Drop unnecessary columns
    columns_to_drop = ['Nos of PCS/Pallet', 'Safety Stock', 'Qty Held against existing orders awaiting pickup']
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Rename columns for consistency
    df = df.rename(columns={'Grand Total': 'Warehouse+Transit'})

    # List of numeric columns to convert
    numeric_columns = [
        'Nos of PCS/Pallet', 'In Transit Stock', 'Warehouse Stock',
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