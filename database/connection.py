# dental_clinic/database/connection.py
import sqlite3
import os
from pathlib import Path

# Define the path for the database file relative to the project root
# This assumes the script is run from the project root or the dental_clinic directory
# For robustness, especially when packaged, consider placing the DB in user data folders.
# For now, we place it inside the 'database' directory.
DATABASE_DIR = Path(__file__).parent
DATABASE_NAME = "dental_clinic.db"
DATABASE_PATH = DATABASE_DIR / DATABASE_NAME

def get_db_connection():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the database.
                             Returns None if connection fails.
    """
    conn = None
    try:
        print(f"Attempting to connect to database at: {DATABASE_PATH}")
        # Ensure the directory exists
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
        print("Database connection successful.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        # In a real app, log this error or show a user-friendly message
        return None
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}")
        return None

def close_db_connection(conn):
    """
    Closes the database connection if it's open.

    Args:
        conn (sqlite3.Connection): The connection object to close.
    """
    if conn:
        try:
            conn.close()
            print("Database connection closed.")
        except sqlite3.Error as e:
            print(f"Error closing database connection: {e}")

if __name__ == '__main__':
    # Example usage: Test connection
    print("Testing database connection...")
    connection = get_db_connection()
    if connection:
        print("Test connection successful.")
        # Example: Check foreign key support
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()
        print(f"Foreign Key Support: {'Enabled' if fk_status and fk_status[0] == 1 else 'Disabled'}")
        cursor.close()
        close_db_connection(connection)
    else:
        print("Test connection failed.")