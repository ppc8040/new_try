import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine, text
import XlsxWriter
from datetime import datetime

# PostgreSQL Database URI (Ensure the prefix fix is applied)
uri = "postgres://u5uvdmh4eki2lk:pd24f3a532c9386e873acf172a2f5a60a5a3176daa7b2f850c8c674e14bd83c6d@c9mq4861d16jlm.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d1bglbigug1dqt"
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy Engine
engine = create_engine(uri)

# Function to fetch data for a specific user
def fetch_data(query, params):
    with engine.connect() as connection:
        result = connection.execute(text(query), params)
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# Function to generate the Excel file
def generate_excel_file(username):
    try:
        # Define queries with filtering for the logged-in user
        inventory_query = """
            SELECT 
                cust_code AS "Customer Code", 
                indus_part AS "Indus Part", 
                customer_part AS "Customer Part", 
                in_transit_stock AS "In Transit Stock", 
                warehouse_stock AS "Warehouse Stock", 
                days_0_30 AS "0-30 Days", 
                days_31_60 AS "31-60 Days", 
                days_61_90 AS "61-90 Days", 
                days_91_120 AS "91-120 Days", 
                days_121_180 AS "121-180 Days", 
                days_181_240 AS "181-240 Days", 
                days_gt_240 AS ">240 Days", 
                warehouse_transit AS "Warehouse+Transit", 
                pallet_size_cms AS "Pallet Size (cms)", 
                pcs_per_pallet AS "Coils/Pallet"
            FROM inventory_db 
            WHERE cust_code = :cust_code
            ORDER BY warehouse_stock DESC
        """

        transit_query = """
            SELECT 
                indus_part AS "Indus Part", 
                customer_part_no AS "Customer Part", 
                customer_code AS "Customer Code", 
                pallet_qty AS "Coils/Pallet", 
                num_of_pallet AS "Number of Pallets", 
                total_qty AS "Total Coils", 
                container_number AS "Container Number", 
                eta_arrival_to_va AS "ETA Arrival to VA"
            FROM transit_db 
            WHERE customer_code = :cust_code
            ORDER BY eta_arrival_to_va ASC
        """

        oor_query = """
            SELECT 
                actual_customer AS "Customer Code", 
                customer_po_number AS "Customer PO#", 
                date_of_receiving_po AS "Date of Receiving PO#", 
                customer_required_delivery_date AS "Required Delivery Date",  
                customer_material AS "Customer Part", 
                indus_product AS "Indus Part", 
                ordered_quantity AS "Ordered Quantity", 
                delivered_quantity AS "Delivered Quantity", 
                open_quantity AS "Open Quantity", 
                stock_in_virginia AS "Stock in Virginia", 
                stock_in_transit AS "Stock in Transit", 
                stock_at_indus AS "Stock at Indus- Dubai", 
                to_be_manufactured AS "Manufacturing WIP"
            FROM customer_orders 
            WHERE actual_customer LIKE :cust_code_filter
            ORDER BY date_of_receiving_po ASC, customer_required_delivery_date ASC         
        """

        # Fetch the data for the user
        inventory_data = fetch_data(inventory_query, {'cust_code': username})
        transit_data = fetch_data(transit_query, {'cust_code': username})
        
        # Conditionally fetch OOR data based on username
        exclude_oor_users = ['001CPT-AT', '001WFI', '001SCT', '001RDT']
        oor_data = None
        if username not in exclude_oor_users:
            oor_data = fetch_data(oor_query, {'cust_code_filter': f'%{username[3:6]}%'})

        # Convert date columns to the format 'dd-MMM-yy'
        for df, date_columns in [
            (transit_data, ['ETA Arrival to VA']),
            (oor_data, ['Date of Receiving PO#', 'Required Delivery Date']) if oor_data is not None else (None, [])
        ]:
            if df is not None:
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d-%b-%y').fillna('')

        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        filename = f"{username}_data_{timestamp}.xlsx"

        # Create an in-memory Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            cell_format = workbook.add_format({'border': 1})  # Border format

            # Function to write data with formatting
            def write_sheet(df, sheet_name):
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    worksheet = writer.sheets[sheet_name]

                    # Apply border and auto-size columns
                    for row_num in range(df.shape[0] + 1):  # Include header row
                        for col_num in range(df.shape[1]):
                            worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num] if row_num > 0 else df.columns[col_num], cell_format)

                    # Adjust column width
                    for col_num, col_name in enumerate(df.columns):
                        max_length = max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2
                        worksheet.set_column(col_num, col_num, max_length)

            # Write sheets
            write_sheet(inventory_data, 'Inventory')
            write_sheet(transit_data, 'Transit')
            if oor_data is not None:  # Only include OOR if it was fetched
                write_sheet(oor_data, 'OOR')

        output.seek(0)  # Reset the buffer position

        return output, filename  # Return the Excel file object and filename

    except Exception as e:
        print(f"Error generating Excel: {e}")  # Log error
        return None, None  # Handle errors gracefully
