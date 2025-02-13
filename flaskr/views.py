from flask import Blueprint, render_template, request,jsonify, redirect,url_for
from flask_login import login_required, current_user
import pandas as pd
from sqlalchemy import text
from flaskr.models import db
from flaskr.excel_download import generate_excel_file
from flask import send_file
from datetime import datetime
from flaskr.mail_config import send_email_graph_api

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
                reserved_qty as "Released Qty Awaiting Pickup",
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
            ORDER BY eta_arrival_to_va ASC
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

def get_oor_data():
    try:
        # Extract the customer code from the current user's username (cust_code_filter)
        if len(current_user.username) == 3:
            cust_code_filter = current_user.username
        else:
            cust_code_filter = current_user.username[3:6]
        if not cust_code_filter.strip():  # .strip() handles whitespace too
            return {'headers': ["Currently no data available for the OOR"], 'rows': [[""]]}

        # Check if the user is in the hidden_tab for OOR
        hidden_tabs_status = get_hidden_tabs(current_user.username)
        hide_stock_columns = hidden_tabs_status["hide_transit_button"]

        query = text("""
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
                """ + ("" if hide_stock_columns else "stock_in_virginia AS \"Stock in Virginia\", stock_in_transit AS \"Stock in Transit\", ") + """
                stock_at_indus AS "Stock at Indus- Dubai", 
                to_be_manufactured AS "Manufacturing WIP"
            FROM customer_orders 
            WHERE actual_customer LIKE :cust_code_filter
            ORDER BY customer_required_delivery_date, date_of_receiving_po ASC         
        """)
        
        # Execute the query and fetch the result into a Pandas DataFrame
        result = db.session.execute(query, {'cust_code_filter': f'%{cust_code_filter}%'})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

        # If the dataframe is empty, return an error message
        if df.empty:
            return {'headers': ["Currently no data available for the OOR"], 'rows': [[""]]}

        # Convert date columns to datetime format and format to 'dd-MMM-yy'
        date_columns = ['Date of Receiving PO#', 'Required Delivery Date', 'Indus Ship Date', 'Actual Ship Date', 'ETA Virginia']
        for col in date_columns:
            if col in df.columns:
                # Convert to datetime, where missing values will be handled correctly
                df[col] = pd.to_datetime(df[col], errors='coerce')

                # Format the date column to 'dd-MMM-yy' and replace NaT with blanks
                df[col] = df[col].dt.strftime('%d-%b-%y').fillna('')

        # Prepare table headers and rows for the response
        table_headers = df.columns.tolist()
        table_rows = df.values.tolist()

        return {'headers': table_headers, 'rows': table_rows}

    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

def get_int_stock_data():
    try:
        query = text("""
            SELECT 
                customer_code AS "Customer Code",
                customer_part AS "Customer Part",     
                item AS "Indus Part", 
                pallet_size AS "Coils/Pallet",
                alt_1_qty AS "Number of Pallets", 
                quantity AS "Quantity"
            FROM INT_stock_db 
            WHERE customer_code = :customer_code
            ORDER BY alt_1_qty DESC
        """)

        # Execute the query and fetch the result into a Pandas DataFrame
        result = db.session.execute(query, {'customer_code': current_user.username})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

        if not df.empty:
            table_headers = df.columns.tolist()
            table_rows = df.values.tolist()
        else:
            table_headers = ["No inventory available for releases"]
            table_rows = [[""]]

        return {'headers': table_headers, 'rows': table_rows}

    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}



def get_hidden_tabs(username):
    hidden_tabs = {
        "OOR": {'001CPT-AT', '001WFI', '001SCT', '001RDT'},
        "Transit": {'ALD','BDT','BON','COM','ETX','ETP','KAL','EMB','ETE','HCL','HEL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','WBT','JOL','LIE','QTM','SRG','RDE'},
        "Inventory": {'ALD','BDT','BON','COM','ETX','ETP','KAL','EMB','ETE','HCL','HEL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','WBT','JOL','LIE','QTM','SRG','RDE'},
        "Release": {'ALD','BDT','BON','COM','ETX','ETP','KAL','EMB','ETE','HCL','HEL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','WBT','JOL','LIE','QTM','SRG','RDE'}
    }

    return {
        "hide_oor_button": username in hidden_tabs["OOR"],
        "hide_transit_button": username in hidden_tabs["Transit"],
        "hide_inventory_button": username in hidden_tabs["Inventory"],
        "hide_release_button": username in hidden_tabs["Release"]
    }



# Route for the Dashboard (default view shows Inventory)
@views.route('/')
@login_required
def home():
    inventory_data = get_inventory_data()  # Get Inventory data
    transit_data = get_transit_data()  # Get Transit data
    oor_data = get_oor_data()
    releases = get_int_stock_data()
    tabs_data = {
        'Inventory': inventory_data,
        'Transit': transit_data,
        'OOR': oor_data,
        'Releases': releases
    }  
    hidden_tabs = get_hidden_tabs(current_user.username)
    if not hidden_tabs["hide_inventory_button"]:
        default_tab = 'Inventory'
    elif not hidden_tabs["hide_transit_button"]:
        return redirect(url_for('views.transit'))  # Redirect if Inventory is hidden
    else:
        return redirect(url_for('views.oor'))  # Redirect if Inventory & Transit are hidden
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Inventory',**hidden_tabs)

# Route for the Transit tab
@views.route('/transit')
@login_required
def transit():
    transit_data = get_transit_data()  # Get Transit data
    tabs_data = {'Transit': transit_data}  # Show Transit data
    hidden_tabs = get_hidden_tabs(current_user.username)
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Transit',**hidden_tabs)

# Route for the OOR tab
@views.route('/open-order')
@login_required
def oor():
    oor_data = get_oor_data()  # Get OOR data
    tabs_data = {'Open Order': oor_data}  # Show OOR data
    hidden_tabs = get_hidden_tabs(current_user.username)
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Open Order',**hidden_tabs)

@views.route('/releases')
@login_required
def releases():
    releases = get_int_stock_data()  # Fetch INT Stock data
    tabs_data = {'Releases': releases}  # Prepare data for rendering
    hidden_tabs = get_hidden_tabs(current_user.username)
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Releases', **hidden_tabs)

@views.route('/download-all')
@login_required
def download_all_tables():
    # Get the logged-in username
    username = current_user.username
    
    # Call function to generate the Excel file
    excel_file, file_name = generate_excel_file(username)  # Unpack the returned tuple

    if excel_file is None:
        return "Failed to generate Excel file", 500

    return send_file(
        excel_file,
        as_attachment=True,
        download_name=file_name,  # Use the correct filename
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@views.route('/submit-releases', methods=['POST'])
@login_required
def submit_releases():
    username = current_user.username

    # Ensure request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expecting JSON."}), 400

    request_json = request.get_json()
    data = request_json.get('data', [])

    # Check if the 'data' field is empty or missing
    if not data:
        return jsonify({"error": "No 'data' field found in request JSON or it's empty."}), 400

    try:
        # Insert data into the database
        for row in data:
            if len(row) < 7:
                return jsonify({"error": "Invalid row format. Each row must have at least 7 values."}), 400

            query = text("""
                INSERT INTO releases_db 
                (customer_code, customer_part, indus_part, coils_per_pallet, no_of_pallets, quantity, pallets_for_release, requested_at)
                VALUES 
                (:customer_code, :customer_part, :indus_part, :coils_per_pallet, :no_of_pallets, :quantity, :pallets_for_release, :requested_at)
            """)

            db.session.execute(query, {
                'customer_code': row[0],
                'customer_part': row[1],
                'indus_part': row[2],
                'coils_per_pallet': row[3],
                'no_of_pallets': row[4],
                'quantity': row[5],
                'pallets_for_release': int(row[6]),
                'requested_at': datetime.now()
            })

        db.session.commit()  # Commit only after all inserts succeed

    except Exception as db_error:
        db.session.rollback()  # Rollback only if there was a DB failure
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500

    # Convert table data to HTML for email
    table_html = "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
    table_html += "<tr><th>Customer Code</th><th>Customer Part</th><th>Indus Part</th><th>Coils Per Pallet</th><th>No of Pallets</th><th>Quantity</th><th>Pallets for Release</th></tr>"
    for row in data:
        table_html += "<tr>" + "".join(f"<td>{col}</td>" for col in row) + "</tr>"
    table_html += "</table>"

    recipient_email = ["ppc@indusair.ae","hitesh.moghariya@indusair.ae","logisticsdbx2@indusair.ae", "logisticsdbx@indusair.ae", "logisticsdbx1@indusair.ae"]
    subject = f"{username}_New Release Request"
    body = f"""
        <p>A new release request has been submitted. Below are the details:</p>
        {table_html}
        <p>Best Regards,<br>Your System</p>
    """

    try:
        # Send email using Microsoft Graph API
        email_response = send_email_graph_api(recipient_email, subject, body)
        
        if email_response["status"] == "success":
            return jsonify({"success": "Releases submitted successfully, email sent!"}), 200
        else:
            return jsonify({"error": f"Email sending failed: {email_response['message']}"}), 500

    except Exception as email_error:
        return jsonify({"error": f"An error occurred while sending the email: {str(email_error)}"}), 500


