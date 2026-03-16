from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    customer_code = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Inventory model
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_code = db.Column(db.String(50), nullable=False)
    indus_part = db.Column(db.String(100), nullable=False)
    customer_part = db.Column(db.String(100), nullable=False)
    in_transit_stock = db.Column(db.Integer, nullable=False)
    warehouse_stock = db.Column(db.Integer, nullable=False)
    reserved_qty = db.Column(db.Integer, nullable=False)
    days_0_30 = db.Column(db.Integer, nullable=False)
    days_31_60 = db.Column(db.Integer, nullable=False)
    days_61_90 = db.Column(db.Integer, nullable=False)
    days_91_120 = db.Column(db.Integer, nullable=False)
    days_121_180 = db.Column(db.Integer, nullable=False)
    days_181_240 = db.Column(db.Integer, nullable=False)
    days_gt_240 = db.Column(db.Integer, nullable=False)
    warehouse_transit = db.Column(db.Integer, nullable=False)
    pallet_size_cms = db.Column(db.Integer, nullable=False)
    pcs_per_pallet = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<Inventory {self.id}>'
    
class Transit(db.Model):
    __tablename__ = 'transit_db'
    id = db.Column(db.Integer, primary_key=True)
    indus_part = db.Column(db.String(100), nullable=True)  # Industry Part
    customer_part_no = db.Column(db.String(100), nullable=True)  # Customer Part No.
    customer_code = db.Column(db.String(50), nullable=True)  # Customer Code
    pallet_qty = db.Column(db.Integer, nullable=True)  # Pallet / Qty
    num_of_pallet = db.Column(db.Integer, nullable=True)  # Number of Pallets
    total_qty = db.Column(db.Integer, nullable=True)  # Total Quantity
    container_number = db.Column(db.String(50), nullable=True)  # Container Number
    in_transit = db.Column(db.Text, nullable=True)  # In Transit (stored as text)
    eta_arrival_to_va = db.Column(db.Date, nullable=True)  # ETA Arrival to VA
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)  # Timestamp for last update

    def __repr__(self):
        return f'<Transit {self.id}>'    

class OOR_db(db.Model):
    __tablename__ = 'customer_orders'  # Table name in PostgreSQL

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Primary Key
    customer_code = db.Column(db.String(50), nullable=False)
    customer_po = db.Column(db.String(100), nullable=True)
    date_of_receiving_po = db.Column(db.Date, nullable=True)
    customer_required_delivery_date = db.Column(db.Date, nullable=True)
    sales_document = db.Column(db.String(100), nullable=True)
    sales_document_item = db.Column(db.String(50), nullable=True)
    customer_material = db.Column(db.String(100), nullable=True)
    indus_product = db.Column(db.String(100), nullable=True)
    ordered_quantity = db.Column(db.Integer, nullable=True, default=0)
    delivered_quantity = db.Column(db.Integer, nullable=True, default=0)
    open_quantity = db.Column(db.Integer, nullable=True, default=0)
    stock_in_virginia = db.Column(db.Integer, nullable=True, default=0)
    stock_in_transit = db.Column(db.Integer, nullable=True, default=0)
    stock_at_indus = db.Column(db.Integer, nullable=True, default=0)
    to_be_manufactured = db.Column(db.Integer, nullable=True, default=0)
    indus_ship_date = db.Column(db.Date, nullable=True)
    actual_ship_date = db.Column(db.Date, nullable=True)  # First shipment date for partial qty
    eta_virginia = db.Column(db.Date, nullable=True)
    actual_customer = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<OOR_db {self.customer_code}>"

class int_stock(db.Model):
    __tablename__ = 'int_stock_db'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    customer_part = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    qty_reserved = db.Column(db.Integer, nullable=False)
    alt_1_qty = db.Column(db.Numeric(10, 0), nullable=False)  
    grs_weight = db.Column(db.Numeric(10, 2), nullable=False)  
    pallet_size = db.Column(db.Numeric(10, 0), nullable=False) 
    customer_code = db.Column(db.String(100), nullable=False)  
    last_updated = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<int_stock {self.id}>'

class Release(db.Model):
    __tablename__ = 'releases_db'  # Matches your database table name

    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(100), nullable=False)
    customer_part = db.Column(db.String(100), nullable=True)   
    indus_part = db.Column(db.String(100), nullable=False)  
    coils_per_pallet = db.Column(db.Numeric(10, 0), nullable=False)  
    no_of_pallets = db.Column(db.Numeric(10, 0), nullable=False)  
    quantity = db.Column(db.Integer, nullable=False)  
    pallets_for_release = db.Column(db.Integer, nullable=True)  
    requested_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f'<Release {self.id}>'
