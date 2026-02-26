import pyodbc

server = r'DESKTOP-2H8SIVM\SQLEXPRESS'
database = 'InventoryDB'

conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
    f"Encrypt=no;"
    f"TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# ==========================================
# 1. CLEAR EXISTING DATA & RESET IDENTITIES
# ==========================================
print("Clearing old data to prevent duplicates...")

# We MUST delete in this exact reverse order to avoid Foreign Key constraint errors
tables_to_clear = [
    "AssetTransactions", 
    "SalesOrderLines", 
    "SalesOrders", 
    "PurchaseOrderLines", 
    "PurchaseOrders", 
    "Bills", 
    "Assets", 
    "Items", 
    "Locations", 
    "Sites", 
    "Vendors", 
    "Customers"
]

for table in tables_to_clear:
    # 1. Delete all rows from the table
    cursor.execute(f"DELETE FROM {table}")
    
    # 2. Reset the Identity (Auto-Increment) back to 0 so new inserts start at 1
    try:
        cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
    except pyodbc.Error:
        # If a table doesn't have an IDENTITY column, just ignore the error and move on
        pass

print("Old data cleared. Inserting new seed data...")

# ==========================================
# 2. INSERT NEW DATA
# ==========================================

customers = [
    ('CUST001', 'ABC Corp', 'abc@example.com', '01000000001', 'Addr1', 'Cairo', 'Egypt'),
    ('CUST002', 'XYZ Ltd', 'xyz@example.com', '01000000002', 'Addr2', 'Alexandria', 'Egypt'),
    ('CUST003', 'Foo Inc', 'foo@example.com', '01000000003', 'Addr3', 'Giza', 'Egypt'),
    ('CUST004', 'Bar LLC', 'bar@example.com', '01000000004', 'Addr4', 'Mansoura', 'Egypt'),
    ('CUST005', 'Baz Co', 'baz@example.com', '01000000005', 'Addr5', 'Luxor', 'Egypt')
]
for c in customers:
    cursor.execute("""
        INSERT INTO Customers (CustomerCode, CustomerName, Email, Phone, BillingAddress1, BillingCity, BillingCountry)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, c)


vendors = [
    ('VEND001', 'Supply Co', 'supply@example.com', '01000000011', 'Addr1', 'Cairo', 'Egypt'),
    ('VEND002', 'Tech Supplies', 'tech@example.com', '01000000012', 'Addr2', 'Alexandria', 'Egypt'),
    ('VEND003', 'Parts Ltd', 'parts@example.com', '01000000013', 'Addr3', 'Giza', 'Egypt'),
    ('VEND004', 'Tools Inc', 'tools@example.com', '01000000014', 'Addr4', 'Mansoura', 'Egypt'),
    ('VEND005', 'Equip Co', 'equip@example.com', '01000000015', 'Addr5', 'Luxor', 'Egypt')
]
for v in vendors:
    cursor.execute("""
        INSERT INTO Vendors (VendorCode, VendorName, Email, Phone, AddressLine1, City, Country)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, v)

sites = [
    ('SITE001', 'Main Warehouse', 'Addr1', 'Cairo', 'Egypt', 'EET'),
    ('SITE002', 'Branch Warehouse', 'Addr2', 'Alexandria', 'Egypt', 'EET'),
    ('SITE003', 'Remote Warehouse', 'Addr3', 'Giza', 'Egypt', 'EET'),
    ('SITE004', 'East Warehouse', 'Addr4', 'Mansoura', 'Egypt', 'EET'),
    ('SITE005', 'West Warehouse', 'Addr5', 'Luxor', 'Egypt', 'EET')
]
for s in sites:
    cursor.execute("""
        INSERT INTO Sites (SiteCode, SiteName, AddressLine1, City, Country, TimeZone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, s)


locations = [
    (1, 'LOC001', 'Main Storage', None),
    (1, 'LOC002', 'Secondary Storage', None),
    (2, 'LOC003', 'Front Area', None),
    (2, 'LOC004', 'Back Area', None),
    (3, 'LOC005', 'Remote Section', None)
]
for l in locations:
    cursor.execute("""
        INSERT INTO Locations (SiteId, LocationCode, LocationName, ParentLocationId)
        VALUES (?, ?, ?, ?)
    """, l)

items = [
    ('ITEM001', 'Laptop', 'Electronics', 'Piece'),
    ('ITEM002', 'Mouse', 'Electronics', 'Piece'),
    ('ITEM003', 'Desk Chair', 'Furniture', 'Piece'),
    ('ITEM004', 'Monitor', 'Electronics', 'Piece'),
    ('ITEM005', 'Keyboard', 'Electronics', 'Piece')
]
for i in items:
    cursor.execute("""
        INSERT INTO Items (ItemCode, ItemName, Category, UnitOfMeasure)
        VALUES (?, ?, ?, ?)
    """, i)

assets = [
    ('ASSET001', 'Dell Laptop', 1, 1, None, 'Electronics', 'Active', 1200.00, None, 1),
    ('ASSET002', 'HP Laptop', 1, 2, None, 'Electronics', 'Active', 1100.00, None, 2),
    ('ASSET003', 'Ergonomic Chair', 2, 3, None, 'Furniture', 'Active', 300.00, None, 3),
    ('ASSET004', 'Monitor 24"', 2, 4, None, 'Electronics', 'Active', 200.00, None, 4),
    ('ASSET005', 'Mechanical Keyboard', 3, 5, None, 'Electronics', 'Active', 150.00, None, 5)
]
for a in assets:
    cursor.execute("""
        INSERT INTO Assets (AssetTag, AssetName, SiteId, LocationId, SerialNumber, Category, Status, Cost, PurchaseDate, VendorId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, a)


bills = [
    (1, 'BILL001', '2026-01-01', '2026-01-30', 5000.00, 'USD', 'Open'),
    (2, 'BILL002', '2026-02-01', '2026-02-28', 1200.00, 'USD', 'Open'),
    (3, 'BILL003', '2026-03-01', '2026-03-31', 800.00, 'USD', 'Open'),
    (4, 'BILL004', '2026-04-01', '2026-04-30', 2200.00, 'USD', 'Open'),
    (5, 'BILL005', '2026-05-01', '2026-05-31', 1500.00, 'USD', 'Open')
]
for b in bills:
    cursor.execute("""
        INSERT INTO Bills (VendorId, BillNumber, BillDate, DueDate, TotalAmount, Currency, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, b)


pos = [
    ('PO001', 1, '2026-01-10', 'Open', 1),
    ('PO002', 2, '2026-02-12', 'Open', 2),
    ('PO003', 3, '2026-03-15', 'Open', 3),
    ('PO004', 4, '2026-04-18', 'Open', 4),
    ('PO005', 5, '2026-05-20', 'Open', 5)
]
for p in pos:
    cursor.execute("""
        INSERT INTO PurchaseOrders (PONumber, VendorId, PODate, Status, SiteId)
        VALUES (?, ?, ?, ?, ?)
    """, p)

po_lines = [
    (1, 1, 10, 'ITEM001', 'Dell Laptop', 1200.00),
    (2, 1, 20, 'ITEM002', 'Mouse', 10.00),
    (3, 2, 5, 'ITEM003', 'Desk Chair', 150.00),
    (4, 3, 2, 'ITEM004', 'Monitor 24"', 200.00),
    (5, 4, 3, 'ITEM005', 'Mechanical Keyboard', 150.00)
]
for line in po_lines:
    cursor.execute("""
        INSERT INTO PurchaseOrderLines (POId, LineNumber, Quantity, ItemCode, Description, UnitPrice)
        VALUES (?, ?, ?, ?, ?, ?)
    """, line)


sales_orders = [
    ('SO001', 1, '2026-01-15', 'Open', 1),
    ('SO002', 2, '2026-02-18', 'Open', 2),
    ('SO003', 3, '2026-03-20', 'Open', 3),
    ('SO004', 4, '2026-04-22', 'Open', 4),
    ('SO005', 5, '2026-05-25', 'Open', 5)
]
for so in sales_orders:
    cursor.execute("""
        INSERT INTO SalesOrders (SONumber, CustomerId, SODate, Status, SiteId)
        VALUES (?, ?, ?, ?, ?)
    """, so)

so_lines = [
    (1, 1, 2, 'ITEM001', 'Dell Laptop', 1200.00),
    (2, 1, 5, 'ITEM002', 'Mouse', 10.00),
    (3, 2, 1, 'ITEM003', 'Desk Chair', 150.00),
    (4, 3, 1, 'ITEM004', 'Monitor 24"', 200.00),
    (5, 4, 1, 'ITEM005', 'Mechanical Keyboard', 150.00)
]
for line in so_lines:
    cursor.execute("""
        INSERT INTO SalesOrderLines (SOId, LineNumber, Quantity, ItemCode, Description, UnitPrice)
        VALUES (?, ?, ?, ?, ?, ?)
    """, line)


asset_txns = [
    (1, None, 1, 'Move', 1, '2026-01-20', 'Moved to main storage'),
    (2, 1, 2, 'Move', 1, '2026-01-21', 'Moved to secondary storage'),
    (3, 2, 3, 'Move', 1, '2026-02-01', 'Moved to front area'),
    (4, 3, None, 'Use', 1, '2026-02-10', 'In use'),
    (5, 4, None, 'Use', 1, '2026-03-05', 'In use')
]
for txn in asset_txns:
    cursor.execute("""
        INSERT INTO AssetTransactions (AssetId, FromLocationId, ToLocationId, TxnType, Quantity, TxnDate, Note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, txn)


conn.commit()
cursor.close()
conn.close()

print("Script completed: Cleaned old data and inserted 5 rows into all tables successfully.")