import mysql.connector
from app.config import DB_CONFIG

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Database connection successful")
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise e 