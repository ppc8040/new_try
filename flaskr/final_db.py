import pandas as pd
import psycopg2
import schedule
import time
from datetime import datetime
from flaskr.msal_auth import fetch_excel_data  # Importing fetch_excel_data from msal_auth.py
from flaskr.process_excel import process_data_inventory, process_data_transit  # Importing both functions

# Database connection parameters
uri = "postgres://u5uvdmh4eki2lk:pd24f3a532c9386e873acf172a2f5a60a5a3176daa7b2f850c8c674e14bd83c6d@c9mq4861d16jlm.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d1bglbigug1dqt"
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Retry parameters
MAX_RETRIES = 5  # Maximum number of retries
RETRY_DELAY = 2  # Delay in seconds between retries

# Function to lock and delete table data safely with retry logic
def lock_and_delete_table(cursor, table_name):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Lock the table in EXCLUSIVE mode
            cursor.execute(f"LOCK TABLE {table_name} IN EXCLUSIVE MODE;")
            print(f"Locked table {table_name}. Deleting data...")

            # Delete all rows from the table
            cursor.execute(f"DELETE FROM {table_name};")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]

            if row_count == 0:
                print(f"Table {table_name} successfully emptied.")
                return True
            else:
                print(f"Table {table_name} still contains {row_count} rows.")
                return False
        except Exception as e:
            retry_count += 1
            print(f"Error during locking and deleting {table_name}: {e}. Retry {retry_count}/{MAX_RETRIES}. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    return False

# Function to insert data into inventory_db
def insert_inventory_data(df):
    try:
        conn = psycopg2.connect(uri)
        cursor = conn.cursor()

        # Lock and delete data in the inventory_db table
        if not lock_and_delete_table(cursor, "inventory_db"):
            print("Failed to empty inventory_db. Aborting operation.")
            return

        # Insert processed inventory data
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO inventory_db (
                    cust_code, indus_part, customer_part, in_transit_stock, warehouse_stock, 
                    days_0_30, days_31_60, days_61_90, days_91_120, days_121_180, days_181_240, 
                    days_gt_240, warehouse_transit, pallet_size_cms, pcs_per_pallet, last_updated
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['Cust Code'], row['Indus Part'], row['Customer Part'], row['In Transit Stock'], row['Warehouse Stock'],
                row['0-30 Days'], row['31-60 Days'], row['61-90 Days'], row['91-120 Days'], row['121-180 Days'], 
                row['181-240 Days'], row['>240 Days'], row['Warehouse+Transit'], row['Pallet Size Cms'], 
                row['Pcs per pallet'], datetime.now()
            ))

        conn.commit()
        print("Inventory data inserted successfully.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error inserting inventory data: {e}")

# Function to insert data into transit_db
def insert_transit_data(df):
    try:
        conn = psycopg2.connect(uri)
        cursor = conn.cursor()

        # Lock and delete data in the transit_db table
        if not lock_and_delete_table(cursor, "transit_db"):
            print("Failed to empty transit_db. Aborting operation.")
            return

        # Insert processed transit data
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO transit_db (
                    indus_part, customer_part_no, customer_code, pallet_qty, num_of_pallet, 
                    total_qty, container_number, in_transit, eta_arrival_to_va, last_updated
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['Indus Part'], row['Customer Part No.'], row['Customer Code'], 
                row['Pallet/Qty'], row['No. of Pallet '], row['Total Qty'], row['Container Number'], 
                row['In Transit'], row['ETA Arrival to VA'], datetime.now()
            ))

        conn.commit()
        print("Transit data inserted successfully.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error inserting transit data: {e}")

# Function to handle missing dates
def handle_missing_dates(date_value):
    if date_value == '1900-01-01' or pd.isna(date_value):
        return None
    return date_value

# Function to insert data into customer_orders
def insert_oor_data(df):
    try:
        conn = psycopg2.connect(uri)
        cursor = conn.cursor()

        # Lock and delete data in the customer_orders table
        if not lock_and_delete_table(cursor, "customer_orders"):
            print("Failed to empty customer_orders. Aborting operation.")
            return

        # Insert processed OOR data
        insert_query = """
            INSERT INTO customer_orders (
                customer_code, customer_po_number, date_of_receiving_po,
                customer_required_delivery_date, sales_document, sales_document_item,
                customer_material, indus_product, ordered_quantity, delivered_quantity,
                open_quantity, stock_in_virginia, stock_in_transit, stock_at_indus,
                to_be_manufactured, indus_ship_date, actual_customer, actual_ship_date, 
                eta_virginia, last_updated
            ) VALUES %s
        """
        data_tuples = [
            (
                row['customer_code'], row['customer_po_number'], handle_missing_dates(row['date_of_receiving_po']),
                handle_missing_dates(row['customer_required_delivery_date']), row['sales_document'], 
                row['sales_document_item'], row['customer_material'], row['indus_product'], 
                row['ordered_quantity'], row['delivered_quantity'], row['open_quantity'], 
                row['stock_in_virginia'], row['stock_in_transit'], row['stock_at_indus'], 
                row['to_be_manufactured'], handle_missing_dates(row['indus_ship_date']), 
                row['actual_customer'], handle_missing_dates(row['actual_ship_date']), 
                row['eta_virginia'], datetime.now()
            ) for _, row in df.iterrows()
        ]
        execute_values(cursor, insert_query, data_tuples)

        conn.commit()
        print("Customer orders data inserted successfully.")
    except Exception as e:
        print(f"Error inserting customer orders data: {e}")
    finally:
        cursor.close()
        conn.close()

# Main function to process and insert data
def run_data_update():
    try:
        print("Fetching and processing Inventory data...")
        inventory_df = process_data_inventory(fetch_excel_data(sheet_name="Cus Inventory", header=1, usecols="B:S"))
        insert_inventory_data(inventory_df)

        print("Fetching and processing Transit data...")
        transit_df = process_data_transit(fetch_excel_data(sheet_name="Part wise Data", header=1, usecols="A:W"))
        insert_transit_data(transit_df)

        print("Fetching and processing OOR data...")
        oor_df = process_oor_data(fetch_oor_data(sheet_name="To be manufactured", header=0, usecols="A:W"))
        insert_oor_data(oor_df)

    except Exception as e:
        print(f"Error in data update: {e}")
