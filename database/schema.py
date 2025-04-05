# database/schema.py

import sqlite3
from .connection import get_db_connection, close_db_connection, DATABASE_PATH

# --- SQL Statements for Table Creation ---

SQL_CREATE_PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    father_name TEXT,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    age INTEGER CHECK(age >= 0), -- Age stored as integer instead of date of birth
    address TEXT, -- Added address field
    phone_number TEXT, -- Removed UNIQUE constraint to allow duplicate phone numbers
    medical_history TEXT,
    first_visit_date DATE DEFAULT CURRENT_DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_SERVICES_TABLE = """
CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    default_price REAL NOT NULL CHECK(default_price >= 0),
    is_active INTEGER DEFAULT 1, -- Boolean (1 for true, 0 for false)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_MEDICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS medications (
    medication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT, -- e.g., Dosage, form (Tablet, Syrup)
    default_price REAL CHECK(default_price >= 0), -- Optional default price
    is_active INTEGER DEFAULT 1, -- Boolean
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_VISITS_TABLE = """
CREATE TABLE IF NOT EXISTS visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    visit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    visit_number INTEGER NOT NULL, -- Added visit_number column
    notes TEXT, -- Doctor's general notes for the visit
    lab_results TEXT, -- Store text results or file paths (consider separate table/storage for files later)
    total_amount REAL NOT NULL DEFAULT 0.0 CHECK(total_amount >= 0),
    paid_amount REAL NOT NULL DEFAULT 0.0 CHECK(paid_amount >= 0),
    due_amount REAL NOT NULL DEFAULT 0.0 CHECK(due_amount >= 0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE -- If patient deleted, visits are removed
);
"""

# Index for faster patient visit lookup
SQL_CREATE_VISITS_PATIENT_ID_INDEX = """
CREATE INDEX IF NOT EXISTS idx_visits_patient_id ON visits(patient_id);
"""

# Index for faster debt lookup
SQL_CREATE_VISITS_DUE_AMOUNT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_visits_due_amount ON visits(due_amount);
"""

SQL_CREATE_VISIT_SERVICES_TABLE = """
CREATE TABLE IF NOT EXISTS visit_services (
    visit_service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    tooth_number INTEGER, -- 1-32, NULL if not tooth-specific
    price_charged REAL NOT NULL CHECK(price_charged >= 0), -- Price at the time of service
    notes TEXT, -- Specific notes for this service instance
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visit_id) REFERENCES visits (visit_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services (service_id) ON DELETE RESTRICT -- Prevent deleting service if used in visits
);
"""

# Index for faster visit service lookup
SQL_CREATE_VISIT_SERVICES_VISIT_ID_INDEX = """
CREATE INDEX IF NOT EXISTS idx_visit_services_visit_id ON visit_services(visit_id);
"""

SQL_CREATE_VISIT_PRESCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS visit_prescriptions (
    visit_prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1 CHECK(quantity > 0),
    price_charged REAL NOT NULL CHECK(price_charged >= 0), -- Price for this specific prescription instance
    instructions TEXT, -- Specific instructions for this patient/visit
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (visit_id) REFERENCES visits (visit_id) ON DELETE CASCADE,
    FOREIGN KEY (medication_id) REFERENCES medications (medication_id) ON DELETE RESTRICT -- Prevent deleting med if prescribed
);
"""

# Index for faster visit prescription lookup
SQL_CREATE_VISIT_PRESCRIPTIONS_VISIT_ID_INDEX = """
CREATE INDEX IF NOT EXISTS idx_visit_prescriptions_visit_id ON visit_prescriptions(visit_id);
"""

# --- Function to Initialize Database ---

def initialize_database():
    """
    Creates all necessary tables in the database if they don't already exist.
    """
    conn = None
    created = False
    db_existed = DATABASE_PATH.exists()

    try:
        print("Initializing database...")
        conn = get_db_connection()
        if not conn:
            print("Failed to get database connection. Initialization aborted.")
            return False

        cursor = conn.cursor()

        print("Creating tables...")
        cursor.execute(SQL_CREATE_PATIENTS_TABLE)
        cursor.execute(SQL_CREATE_SERVICES_TABLE)
        cursor.execute(SQL_CREATE_MEDICATIONS_TABLE)
        cursor.execute(SQL_CREATE_VISITS_TABLE)
        cursor.execute(SQL_CREATE_VISIT_SERVICES_TABLE)
        cursor.execute(SQL_CREATE_VISIT_PRESCRIPTIONS_TABLE)
        print("Tables created (or already existed).")

        print("Creating indexes...")
        cursor.execute(SQL_CREATE_VISITS_PATIENT_ID_INDEX)
        cursor.execute(SQL_CREATE_VISITS_DUE_AMOUNT_INDEX)
        cursor.execute(SQL_CREATE_VISIT_SERVICES_VISIT_ID_INDEX)
        cursor.execute(SQL_CREATE_VISIT_PRESCRIPTIONS_VISIT_ID_INDEX)
        print("Indexes created (or already existed).")

        conn.commit()
        print("Database changes committed.")
        created = True

    except sqlite3.Error as e:
        print(f"Database Error during initialization: {e}")
        if conn:
            conn.rollback() # Rollback changes if error occurs
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            close_db_connection(conn)

    if created:
        if not db_existed:
            print(f"Database file created successfully at: {DATABASE_PATH}")
        else:
            print(f"Database schema verified/updated successfully at: {DATABASE_PATH}")
    else:
        print("Database initialization failed.")

    return created

if __name__ == "__main__":
    # This allows running the script directly to initialize the database
    print("Running schema setup directly...")
    if initialize_database():
        print("--- Database Initialization Complete ---")
    else:
        print("--- Database Initialization Failed ---")
