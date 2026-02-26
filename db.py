import pyodbc

def get_connection():
    server = r'DESKTOP-2H8SIVM\SQLEXPRESS'
    database = 'InventoryDB'

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str)


def execute_query(query: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(query)

    columns = [column[0] for column in cursor.description] if cursor.description else []
    rows = cursor.fetchall() if cursor.description else []

    conn.close()

    return columns, rows