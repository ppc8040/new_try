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
        is_master = current_user.username == 'MASTER'
        if is_master:
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
                    warehouse_transit AS "Warehouse + Transit"
                FROM inventory_db 
                ORDER BY cust_code, warehouse_stock DESC
            """)
            result = db.session.execute(query)
        else:
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
                    warehouse_transit AS "Warehouse + Transit"
                FROM inventory_db 
                WHERE cust_code = :cust_code
                ORDER BY warehouse_stock DESC
            """)
            result = db.session.execute(query, {'cust_code': current_user.username})

        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if not df.empty:
            return {'headers': df.columns.tolist(), 'rows': df.values.tolist()}
        else:
            return {'headers': ["Currently no stock in the warehouse"], 'rows': [[""]]}
    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

# Function to get Transit Data
def get_transit_data():
    try:
        is_master = current_user.username == 'MASTER'
        if is_master:
            query = text("""
                SELECT 
                    customer_code AS "Customer Code",
                    indus_part AS "Indus Part", 
                    customer_part_no AS "Customer Part", 
                    pallet_qty AS "Coils/Pallet", 
                    num_of_pallet AS "Number of Pallets", 
                    total_qty AS "Total Coils", 
                    container_number AS "Container Number", 
                    eta_arrival_to_va AS "ETA to Warehouse"
                FROM transit_db 
                ORDER BY customer_code, eta_arrival_to_va ASC
            """)
            result = db.session.execute(query)
        else:
            query = text("""
                SELECT 
                    indus_part AS "Indus Part", 
                    customer_part_no AS "Customer Part", 
                    customer_code AS "Customer Code", 
                    pallet_qty AS "Coils/Pallet", 
                    num_of_pallet AS "Number of Pallets", 
                    total_qty AS "Total Coils", 
                    container_number AS "Container Number", 
                    eta_arrival_to_va AS "ETA to Warehouse"
                FROM transit_db 
                WHERE customer_code = :cust_code
                ORDER BY eta_arrival_to_va ASC
            """)
            result = db.session.execute(query, {'cust_code': current_user.username})

        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if df.empty:
            return {'headers': ["Currently no stock in transit to the warehouse"], 'rows': [[""]]}

        date_columns = ['ETA to Warehouse']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.sort_values(by=col, ascending=True)
                df[col] = df[col].dt.strftime('%d-%b-%y').fillna('')

        return {'headers': df.columns.tolist(), 'rows': df.values.tolist()}
    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

def get_oor_data():
    try:
        is_master = current_user.username == 'MASTER'
        if is_master:
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
                    stock_in_virginia AS "Stock in Warehouse",
                    stock_in_transit AS "Stock in Transit",
                    stock_at_indus AS "Stock at Indus- Dubai", 
                    to_be_manufactured AS "Manufacturing WIP"
                FROM customer_orders 
                ORDER BY actual_customer, date_of_receiving_po ASC
            """)
            result = db.session.execute(query)
        else:
            if len(current_user.username) == 3:
                cust_code_filter = current_user.username
            else:
                cust_code_filter = current_user.username[3:6]
            if not cust_code_filter.strip():
                return {'headers': ["Currently no data available for the OOR"], 'rows': [[""]]}

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
                    """ + ("" if hide_stock_columns else "stock_in_virginia AS \"Stock in Warehouse\", stock_in_transit AS \"Stock in Transit\", ") + """
                    stock_at_indus AS "Stock at Indus- Dubai", 
                    to_be_manufactured AS "Manufacturing WIP"
                FROM customer_orders 
                WHERE actual_customer LIKE :cust_code_filter
                ORDER BY date_of_receiving_po, customer_required_delivery_date, customer_po_number ASC         
            """)
            result = db.session.execute(query, {'cust_code_filter': f'%{cust_code_filter}%'})

        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if df.empty:
            return {'headers': ["Currently no data available for the OOR"], 'rows': [[""]]}

        date_columns = ['Date of Receiving PO#', 'Required Delivery Date', 'Indus Ship Date', 'Actual Ship Date', 'ETA Virginia']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].dt.strftime('%d-%b-%y').fillna('')

        return {'headers': df.columns.tolist(), 'rows': df.values.tolist()}
    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}

def get_int_stock_data():
    try:
        is_master = current_user.username == 'MASTER'
        if is_master:
            query = text("""
                SELECT 
                    customer_code AS "Customer Code",
                    customer_part AS "Customer Part",     
                    item AS "Indus Part", 
                    pallet_size AS "Coils/Pallet",
                    CASE 
                        WHEN pallet_size > 0 THEN FLOOR((quantity - qty_reserved) / pallet_size)
                        ELSE 0
                    END AS "Number of Pallets", 
                    (quantity - qty_reserved) AS "Quantity"
                FROM INT_stock_db 
                ORDER BY customer_code, (quantity - qty_reserved) DESC
            """)
            result = db.session.execute(query)
        else:
            query = text("""
                SELECT 
                    customer_code AS "Customer Code",
                    customer_part AS "Customer Part",     
                    item AS "Indus Part", 
                    pallet_size AS "Coils/Pallet",
                    CASE 
                        WHEN pallet_size > 0 THEN FLOOR((quantity - qty_reserved) / pallet_size)
                        ELSE 0
                    END AS "Number of Pallets", 
                    (quantity - qty_reserved) AS "Quantity"
                FROM INT_stock_db 
                WHERE customer_code = :customer_code
                ORDER BY (quantity - qty_reserved) DESC
            """)
            result = db.session.execute(query, {'customer_code': current_user.username})

        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if not df.empty:
            return {'headers': df.columns.tolist(), 'rows': df.values.tolist()}
        else:
            return {'headers': ["No inventory available for releases"], 'rows': [[""]]}
    except Exception as e:
        return {'headers': ["Error"], 'rows': [[str(e)]]}


def get_hidden_tabs(username):
    hidden_tabs = {
        "OOR": {'001CPT-AT', '001WFI', '001SCT'},
        "Transit": {'ALD', '001STG','BDT','BON','COM','ETX','ETP','EBS','EMB','HCL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','JOL','LIE','QTM','SRG','NIM','TCS','LER','SPS','NMT','001ACP' },
        "Inventory": {'ALD','001STG','BDT','BON','COM','ETX','ETP','EBS','EMB','HCL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','JOL','LIE','QTM','SRG','NIM','TCS','LER','SPS','NMT','001ACP'},
        "Release": {'ALD','001STG','BDT','BON','COM','ETX','ETP','EBS','EMB','HCL','HGD','MIE','NBE','SML','SPM','SDC','SRO','STL','WOF','LOK','JOL','LIE','QTM','SRG','NIM','TCS','LER','SPS','NMT','001ACP'}
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
    is_master=current_user.username == 'MASTER'
    # Add this right after the hidden_tabs line in all 4 routes:
    if is_master:
        hidden_tabs = {
            "hide_oor_button": False,
            "hide_transit_button": False,
            "hide_inventory_button": False,
            "hide_release_button": False
        }

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
    is_master=current_user.username == 'MASTER'
    # Add this right after the hidden_tabs line in all 4 routes:
    if is_master:
        hidden_tabs = {
            "hide_oor_button": False,
            "hide_transit_button": False,
            "hide_inventory_button": False,
            "hide_release_button": False
        }
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Transit',**hidden_tabs)

# Route for the OOR tab
@views.route('/open-order')
@login_required
def oor():
    oor_data = get_oor_data()  # Get OOR data
    tabs_data = {'Open Order': oor_data}  # Show OOR data
    hidden_tabs = get_hidden_tabs(current_user.username)
    is_master=current_user.username == 'MASTER'
    # Add this right after the hidden_tabs line in all 4 routes:
    if is_master:
        hidden_tabs = {
            "hide_oor_button": False,
            "hide_transit_button": False,
            "hide_inventory_button": False,
            "hide_release_button": False
        }
    return render_template('dashboard.html', tabs_data=tabs_data, active_tab='Open Order',**hidden_tabs)

@views.route('/releases')
@login_required
def releases():
    releases = get_int_stock_data()  # Fetch INT Stock data
    tabs_data = {'Releases': releases}  # Prepare data for rendering
    hidden_tabs = get_hidden_tabs(current_user.username)
    is_master=current_user.username == 'MASTER'
    # Add this right after the hidden_tabs line in all 4 routes:
    if is_master:
        hidden_tabs = {
            "hide_oor_button": False,
            "hide_transit_button": False,
            "hide_inventory_button": False,
            "hide_release_button": False
        }
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


@views.route('/get-po-allocation', methods=['POST'])
@login_required
def get_po_allocation():
    """
    Receives a list of release items and returns a PO allocation table.
    For each Indus Part being released, it finds all open POs (oldest first)
    and allocates the release quantity across them sequentially.
    """
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expecting JSON."}), 400

    request_json = request.get_json()
    items = request_json.get('items', [])

    if not items:
        return jsonify({"error": "No items provided."}), 400

    # Determine the customer code filter (same logic as get_oor_data)
    username = current_user.username
    if len(username) == 3:
        cust_code_filter = username
    else:
        cust_code_filter = username[3:6]

    result_rows = []

    try:
        for item in items:
            indus_part   = item.get('indus_part', '').strip()
            release_qty  = int(item.get('release_qty', 0))

            if not indus_part or release_qty <= 0:
                continue

            # Fetch open POs for this Indus Part ordered oldest first
            query = text("""
                SELECT
                    actual_customer        AS customer_code,
                    customer_po_number     AS customer_po,
                    date_of_receiving_po   AS date_receiving_po,
                    customer_material      AS customer_part,
                    indus_product          AS indus_part,
                    open_quantity          AS open_qty
                FROM customer_orders
                WHERE indus_product = :indus_part
                  AND actual_customer LIKE :cust_code_filter
                  AND open_quantity > 0
                ORDER BY date_of_receiving_po ASC
            """)
            result = db.session.execute(query, {
                'indus_part': indus_part,
                'cust_code_filter': f'%{cust_code_filter}%'
            })

            po_rows = result.fetchall()
            remaining_release = release_qty

            for po in po_rows:
                if remaining_release <= 0:
                    break

                open_qty         = int(po.open_qty)
                allocated        = min(open_qty, remaining_release)
                remaining_open   = open_qty - allocated
                remaining_release -= allocated

                # Format date
                date_val = po.date_receiving_po
                if date_val:
                    try:
                        if hasattr(date_val, 'strftime'):
                            date_str = date_val.strftime('%d-%b-%y')
                        else:
                            date_str = pd.to_datetime(date_val).strftime('%d-%b-%y')
                    except Exception:
                        date_str = str(date_val)
                else:
                    date_str = ''

                result_rows.append([
                    str(po.customer_code),
                    str(po.customer_po),
                    date_str,
                    str(po.customer_part),
                    str(po.indus_part),
                    open_qty,
                    allocated,
                    remaining_open
                ])

        return jsonify({"rows": result_rows}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

    notes = request_json.get('notes', '').strip()

    recipient_email = ["shabbir.kachwala@indusair.ae","logisticsdbx3@indusair.ae","logisticsdbx2@indusair.ae","logisticsdbx@indusair.ae","logisticsdbx1@indusair.ae", "meet.shah@indusair.ae"]
    subject = f"{username}_New Release Request"

    notes_section = ""
    if notes:
        notes_section = f"<p><strong>Release Notes:</strong></p><p style='white-space: pre-wrap;'>{notes}</p>"

    body = f"""
        <p>A new release request has been submitted. Below are the details:</p>
        {table_html}
        {notes_section}
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

@views.route('/get-po-allocation', methods=['POST'])
@login_required
def get_po_allocation():
    """
    Input JSON:
    {
      "lines": [
        {
          "customer_code": "001RPC",
          "customer_part": "10016389",
          "indus_part": "AJM0488",
          "pallets_for_release": 100,
          "coils_per_pallet": 36
        },
        ...
      ]
    }
    """
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expecting JSON."}), 400

    payload = request.get_json()
    lines = payload.get("lines", [])
    if not lines:
        return jsonify({"error": "No lines provided."}), 400

    # Build result rows
    result_rows = []

    try:
        for line in lines:
            customer_code = line.get("customer_code")
            indus_part = line.get("indus_part")
            customer_part = line.get("customer_part")
            pallets_for_release = int(line.get("pallets_for_release", 0) or 0)
            coils_per_pallet = int(line.get("coils_per_pallet", 0) or 0)

            if not customer_code or not indus_part or pallets_for_release <= 0 or coils_per_pallet <= 0:
                continue

            release_qty = pallets_for_release * coils_per_pallet
            remaining_release = release_qty

            # Query open orders for this customer + indus part, in the same order as the OOR tab
            oor_query = text("""
                SELECT 
                    actual_customer       AS "Customer Code",
                    customer_po_number    AS "Customer PO#",
                    date_of_receiving_po  AS "Date of Receiving PO#",
                    customer_material     AS "Customer Part",
                    indus_product         AS "Indus Part",
                    open_quantity         AS "Open Quantity"
                FROM customer_orders
                WHERE actual_customer LIKE :cust_code_filter
                  AND indus_product = :indus_part
                  AND open_quantity > 0
                ORDER BY date_of_receiving_po, customer_required_delivery_date, customer_po_number
            """)

            # For non-MASTER logins your existing logic uses a like-filter on the 3‑char code
            if len(customer_code) == 3:
                cust_code_filter = customer_code
            else:
                cust_code_filter = customer_code[3:6]

            oor_result = db.session.execute(
                oor_query,
                {"cust_code_filter": f"%{cust_code_filter}%", "indus_part": indus_part}
            )

            oor_rows = oor_result.fetchall()

            if not oor_rows:
                # Case 3: no open POs – still show a row saying that
                result_rows.append({
                    "customer_code": customer_code,
                    "customer_po": "—",
                    "date_of_receiving_po": "—",
                    "customer_part": customer_part or "",
                    "indus_part": indus_part,
                    "open_quantity": "",
                    "quantity_for_release": release_qty,
                    "remaining_open_quantity": "No open POs found"
                })
                continue

            # Allocate in the exact order returned by the query
            for r in oor_rows:
                if remaining_release <= 0:
                    break

                cust_code = r["Customer Code"]
                po_num = r["Customer PO#"]
                date_rcv = r["Date of Receiving PO#"]
                cust_part_row = r["Customer Part"]
                indus_part_row = r["Indus Part"]
                open_qty = int(r["Open Quantity"] or 0)

                if open_qty <= 0:
                    continue

                allocated = min(open_qty, remaining_release)
                remaining_open = open_qty - allocated
                remaining_release -= allocated

                # Only show rows with some allocation
                if allocated > 0:
                    # Format date like other views
                    if date_rcv:
                        date_str = pd.to_datetime(date_rcv, errors="coerce")
                        if pd.notna(date_str):
                            date_rcv = date_str.strftime("%d-%b-%y")
                    result_rows.append({
                        "customer_code": cust_code,
                        "customer_po": po_num,
                        "date_of_receiving_po": date_rcv,
                        "customer_part": cust_part_row,
                        "indus_part": indus_part_row,
                        "open_quantity": open_qty,
                        "quantity_for_release": allocated,
                        "remaining_open_quantity": remaining_open
                    })

            # Case 2 (release qty > total open qty) – for now we just let remaining_release go > 0
            # and DO NOT add extra rows; you said we will handle this later.

        return jsonify({"rows": result_rows}), 200

    except Exception as e:
        return jsonify({"error": f"Error while calculating allocation: {str(e)}"}), 500
