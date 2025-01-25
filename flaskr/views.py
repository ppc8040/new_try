from flask import Blueprint, render_template
from flask_login import login_required, current_user
import pandas as pd
from sqlalchemy import text
from flaskr.msal_auth import fetch_excel_data
from flaskr.process_excel import process_data_inventory, process_data_transit
from flaskr.models import db

views = Blueprint('views', __name__)

# Function to get Inventory Data
def get_inventory_data():
    try:
        query = text("""
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
        """)
        # Execute the query and fetch the result into a Pandas DataFrame
        result = db.session.execute(query, {'cust_code': current_user.username})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        

        if not df.empty:
            table_headers = df.columns.tolist()
            table_rows = df.values.tolist()
        else:
            table_headers = ["Currently no stock in the warehouse"]
            table_rows = [[""]]

        return {'headers': table_headers, 'rows': table_rows}

    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

# Function to get Transit Data
def get_transit_data():
    try:
        # Execute the query to get data from transit_db table
        query = text(""" 
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
        """)
        
        # Execute the query and fetch the result into a Pandas DataFrame
        result = db.session.execute(query, {'cust_code': current_user.username})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

        # If the dataframe is empty, return an error
        if df.empty:
            return {'headers': ["Currently no stock in transit to the warehouse"], 'rows': [[""]]}

        # Reorder columns if required (same logic as in your existing code)
        column_to_move = 'Customer Code'
        new_order = [column_to_move] + [col for col in df.columns if col != column_to_move]
        df = df[new_order]

         # Convert date columns to datetime format and format to 'dd-MMM-yy'
        data_column = ['ETA Arrival to VA']
        for col in data_column:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.sort_values(by=col, ascending=True)
                df[col] = df[col].dt.strftime('%d-%b-%y').fillna('')    

        # Prepare table headers and rows for the response
        table_headers = df.columns.tolist()
        table_rows = df.values.tolist()

        return {'headers': table_headers, 'rows': table_rows}

    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

# Route for the Dashboard (default view shows Inventory)
@views.route('/')
@login_required
def home():
    inventory_data = get_inventory_data()  # Get Inventory data
    transit_data = get_transit_data()  # Get Transit data
    tabs_data = {
        'Inventory': inventory_data,
        'Transit': transit_data
    }  # Display all tabs
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Inventory')

# Route for the Transit tab
@views.route('/transit')
@login_required
def transit():
    transit_data = get_transit_data()  # Get Transit data
    tabs_data = {'Transit': transit_data}  # Show Transit data
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Transit')
