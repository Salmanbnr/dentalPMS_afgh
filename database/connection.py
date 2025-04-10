# database/connection.py
import sqlite3
import os
from pathlib import Path
import platform
import appdirs

# Define the application name and author for the user data directory
APP_NAME = "DentalClinic"
APP_AUTHOR = "Muhammad Salman"

# Get the user data directory based on the operating system
def get_user_data_dir():
    """Get the appropriate user data directory based on OS"""
    try:
        # Use appdirs if available (recommended)
        return Path(appdirs.user_data_dir(APP_NAME, APP_AUTHOR))
    except (NameError, ImportError):
        # Fallback implementation if appdirs is not available
        system = platform.system()
        home = Path.home()
        
        if system == "Windows":
            # Windows: AppData/Local/APP_NAME
            return home / "AppData" / "Local" / APP_NAME
        elif system == "Darwin":
            # macOS: ~/Library/Application Support/APP_NAME
            return home / "Library" / "Application Support" / APP_NAME
        else:
            # Linux/Unix: ~/.local/share/APP_NAME
            return home / ".local" / "share" / APP_NAME

# Get the user data directory
USER_DATA_DIR = get_user_data_dir()
DATABASE_NAME = "dental_clinic.db"
DATABASE_PATH = USER_DATA_DIR / DATABASE_NAME

def get_db_connection():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the database.
                             Returns None if connection fails.
    """
    conn = None
    try:
        # Ensure the directory exists
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"Attempting to connect to database at: {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        conn.execute("PRAGMA foreign_keys = ON;")  # Enforce foreign key constraints
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
    # Display where the database is located
    print(f"Database will be stored at: {DATABASE_PATH}")
    
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