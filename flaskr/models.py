from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

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
