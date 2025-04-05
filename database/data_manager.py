# database/data_manager.py
import sqlite3
import shutil
import os
from datetime import date, datetime
from pathlib import Path
# Use absolute imports assuming running from project root
from database.connection import get_db_connection, close_db_connection, DATABASE_PATH
from database.schema import initialize_database # For restore

# --- Helper Functions ---

def _execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """Helper function to execute SQL queries."""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed in _execute_query.")
        return None
    result = None
    last_row_id = None
    try:
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch_one:
            row = cursor.fetchone()
            result = dict(row) if row else None
        elif fetch_all:
            rows = cursor.fetchall()
            result = [dict(row) for row in rows] if rows else []

        if commit:
            conn.commit()
            last_row_id = cursor.lastrowid
            # print(f"Query committed successfully: {query[:60]}...")
        # else:
            # print(f"Query executed successfully (no commit): {query[:60]}...")

    except sqlite3.IntegrityError as e:
        print(f"Database Integrity Error: {e} executing query: {query}")
        if conn and commit: conn.rollback()
        result = False # Indicate specific failure type (e.g., UNIQUE constraint)
    except sqlite3.Error as e:
        print(f"Database Error: {e} executing query: {query}")
        if conn and commit: conn.rollback()
        result = None # General failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn and commit: conn.rollback()
        result = None
    finally:
        close_db_connection(conn)

    # Return dictionary, list of dictionaries, ID, True, False, or None
    if commit:
        # For successful INSERT, return the new ID
        # For successful UPDATE/DELETE, return True
        # For IntegrityError, return False
        # For other errors, return None
        if isinstance(result, bool): return result # Return False for IntegrityError
        return last_row_id if last_row_id is not None and last_row_id > 0 else True if result is None else result
    else:
        # For fetch operations or non-committing execute
        return result

# --- Patient Management ---

def add_patient(name: str, father_name: str, gender: str, age: int, address: str, phone_number: str, medical_history: str):
    """Adds a new patient to the database. Returns patient_id on success, None/False on failure."""
    query = """
        INSERT INTO patients (name, father_name, gender, age, address, phone_number, medical_history, first_visit_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    today_str = date.today().strftime('%Y-%m-%d')
    params = (name, father_name, gender, age, address, phone_number, medical_history, today_str)
    result = _execute_query(query, params, commit=True)
    return result if isinstance(result, int) else None # Return ID only if it's an int

def get_patient_by_id(patient_id):
    """Retrieves a single patient by their ID. Returns dict or None."""
    query = "SELECT * FROM patients WHERE patient_id = ?"
    return _execute_query(query, (patient_id,), fetch_one=True)

def get_all_patients(search_term=""):
    """Retrieves all patients, optionally filtering. Returns list of dicts."""
    if search_term:
        query = "SELECT * FROM patients WHERE name LIKE ? OR phone_number LIKE ? OR CAST(patient_id AS TEXT) LIKE ? ORDER BY name COLLATE NOCASE"
        params = (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%')
    else:
        query = "SELECT * FROM patients ORDER BY name COLLATE NOCASE"
        params = ()
    return _execute_query(query, params, fetch_all=True)

def update_patient(patient_id: int, name: str, father_name: str, gender: str, age: int, address: str, phone_number: str, medical_history: str):
    """Updates an existing patient's details. Returns True/False/None."""
    query = """
        UPDATE patients
        SET name = ?, father_name = ?, gender = ?, age = ?, address = ?,
            phone_number = ?, medical_history = ?, last_updated = CURRENT_TIMESTAMP
        WHERE patient_id = ?
    """
    params = (name, father_name, gender, age, address, phone_number, medical_history, patient_id)
    return _execute_query(query, params, commit=True)

def delete_patient(patient_id):
    """Deletes a patient and their associated visits (CASCADE). Returns True/False/None."""
    query = "DELETE FROM patients WHERE patient_id = ?"
    return _execute_query(query, (patient_id,), commit=True)

# --- Service Management ---
def add_service(name, description, default_price):
    """Adds a new service. Returns service_id or None/False."""
    query = "INSERT INTO services (name, description, default_price) VALUES (?, ?, ?)"
    params = (name, description, default_price)
    result = _execute_query(query, params, commit=True)
    return result if isinstance(result, int) else None

def get_service_by_id(service_id):
    """Gets a service by ID. Returns dict or None."""
    query = "SELECT * FROM services WHERE service_id = ?"
    return _execute_query(query, (service_id,), fetch_one=True)

def get_all_services(active_only=True):
    """Gets all services. Returns list of dicts."""
    query = "SELECT * FROM services"
    params = ()
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name COLLATE NOCASE"
    return _execute_query(query, params, fetch_all=True)

def update_service(service_id, name, description, default_price, is_active):
    """Updates a service. Returns True/False/None."""
    query = """
        UPDATE services
        SET name = ?, description = ?, default_price = ?, is_active = ?, last_updated = CURRENT_TIMESTAMP
        WHERE service_id = ?
    """
    params = (name, description, default_price, 1 if is_active else 0, service_id)
    return _execute_query(query, params, commit=True)

def delete_service(service_id):
    """Deletes a service (if not in use). Returns True/False/None."""
    query = "DELETE FROM services WHERE service_id = ?"
    return _execute_query(query, (service_id,), commit=True)


# --- Medication Management ---
def add_medication(name, description, default_price):
    """Adds a new medication. Returns medication_id or None/False."""
    query = "INSERT INTO medications (name, description, default_price) VALUES (?, ?, ?)"
    params = (name, description, default_price if default_price is not None else 0.0)
    result = _execute_query(query, params, commit=True)
    return result if isinstance(result, int) else None

def get_medication_by_id(medication_id):
    """Gets a medication by ID. Returns dict or None."""
    query = "SELECT * FROM medications WHERE medication_id = ?"
    return _execute_query(query, (medication_id,), fetch_one=True)

def get_all_medications(active_only=True):
    """Gets all medications. Returns list of dicts."""
    query = "SELECT * FROM medications"
    params=()
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name COLLATE NOCASE"
    return _execute_query(query, params, fetch_all=True)

def update_medication(medication_id, name, description, default_price, is_active):
    """Updates a medication. Returns True/False/None."""
    query = """
        UPDATE medications
        SET name = ?, description = ?, default_price = ?, is_active = ?, last_updated = CURRENT_TIMESTAMP
        WHERE medication_id = ?
    """
    params = (name, description, default_price if default_price is not None else 0.0, 1 if is_active else 0, medication_id)
    return _execute_query(query, params, commit=True)

def delete_medication(medication_id):
    """Deletes a medication (if not in use). Returns True/False/None."""
    query = "DELETE FROM medications WHERE medication_id = ?"
    return _execute_query(query, (medication_id,), commit=True)


# --- Visit Management ---
def add_visit(patient_id, visit_date, notes="", lab_results=""):
    """Adds a new visit. Returns visit_id or None/False."""
    # Calculate the visit number
    visit_number = calculate_visit_number(patient_id, visit_date) + 1

    query = """
        INSERT INTO visits (patient_id, visit_date, visit_number, notes, lab_results, total_amount, paid_amount, due_amount)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0)
    """
    date_str = visit_date.strftime('%Y-%m-%d') if isinstance(visit_date, (date, datetime)) else visit_date
    params = (patient_id, date_str, visit_number, notes, lab_results)
    result = _execute_query(query, params, commit=True)
    return result if isinstance(result, int) else None

def calculate_visit_number(patient_id, visit_date):
    """Calculate the visit number for a patient based on the visit date."""
    query = """
    SELECT COUNT(*)
    FROM visits v
    WHERE v.patient_id = ? AND v.visit_date <= ?
    """
    result = _execute_query(query, (patient_id, visit_date), fetch_one=True)
    return result.get('COUNT(*)', 0) if result else 0

def get_visit_by_id(visit_id):
    """Gets a visit by ID, including the visit number specific to the patient. Returns dict or None."""
    query = """
    SELECT
        v.*,
        (SELECT COUNT(*)
         FROM visits v2
         WHERE v2.patient_id = v.patient_id AND v2.visit_date <= v.visit_date) AS visit_number
    FROM
        visits v
    WHERE
        v.visit_id = ?
    """
    return _execute_query(query, (visit_id,), fetch_one=True)


def get_patient_visits(patient_id):
    """Gets all visits for a patient. Returns list of dicts."""
    query = "SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC, visit_id DESC"
    return _execute_query(query, (patient_id,), fetch_all=True)

def update_visit_details(visit_id, visit_date, notes, lab_results):
    """Updates visit notes, date, lab results. Returns True/False/None."""
    query = """
        UPDATE visits
        SET visit_date = ?, notes = ?, lab_results = ?, last_updated = CURRENT_TIMESTAMP
        WHERE visit_id = ?
    """
    date_str = visit_date.strftime('%Y-%m-%d') if isinstance(visit_date, (date, datetime)) else visit_date
    params = (date_str, notes, lab_results, visit_id)
    return _execute_query(query, params, commit=True)

def update_visit_payment(visit_id, paid_amount):
    """Updates paid amount and recalculates due amount for a visit. Returns True/False/None."""
    visit = get_visit_by_id(visit_id)
    if not visit:
        print(f"Error: Visit {visit_id} not found for payment update.")
        return False

    total_amount = visit.get('total_amount', 0.0)
    try:
        new_paid_amount = float(paid_amount)
        if new_paid_amount < 0: raise ValueError("Paid amount cannot be negative.")
    except (ValueError, TypeError) as e:
        print(f"Invalid paid amount provided: {paid_amount}. Error: {e}")
        return False

    new_due_amount = max(0.0, total_amount - new_paid_amount)

    query = """
        UPDATE visits
        SET paid_amount = ?, due_amount = ?, last_updated = CURRENT_TIMESTAMP
        WHERE visit_id = ?
    """
    params = (new_paid_amount, new_due_amount, visit_id)
    return _execute_query(query, params, commit=True)

def _recalculate_visit_total(visit_id):
    """Internal: Recalculates total & due amount based on items. Returns True/False/None."""
    query_sum_services = "SELECT COALESCE(SUM(price_charged), 0) as total_s FROM visit_services WHERE visit_id = ?"
    query_sum_prescriptions = "SELECT COALESCE(SUM(price_charged), 0) as total_p FROM visit_prescriptions WHERE visit_id = ?"

    total_s_result = _execute_query(query_sum_services, (visit_id,), fetch_one=True)
    total_p_result = _execute_query(query_sum_prescriptions, (visit_id,), fetch_one=True)

    # Use .get with default 0.0 in case fetch fails (returns None)
    new_total = total_s_result.get('total_s', 0.0) + total_p_result.get('total_p', 0.0)

    visit = get_visit_by_id(visit_id)
    current_paid = visit.get('paid_amount', 0.0) if visit else 0.0
    new_due = max(0.0, new_total - current_paid)

    query_update = """
        UPDATE visits SET total_amount = ?, due_amount = ?, last_updated = CURRENT_TIMESTAMP
        WHERE visit_id = ?
    """
    return _execute_query(query_update, (new_total, new_due, visit_id), commit=True)


# --- Visit Items (Services & Prescriptions) ---

def add_service_to_visit(visit_id, service_id, tooth_number, price_charged, notes=""):
    """Adds a service to a visit, then recalculates total. Returns visit_service_id or None/False."""
    query = """
        INSERT INTO visit_services (visit_id, service_id, tooth_number, price_charged, notes)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (visit_id, service_id, tooth_number, price_charged, notes)
    result_id = _execute_query(query, params, commit=True)
    if isinstance(result_id, int):
        _recalculate_visit_total(visit_id)
        return result_id
    return None # Return None on failure (False could mean IntegrityError)

def get_services_for_visit(visit_id):
    """Gets all services linked to a visit. Returns list of dicts."""
    query = """
        SELECT vs.*, s.name as service_name, s.description as service_description
        FROM visit_services vs
        JOIN services s ON vs.service_id = s.service_id
        WHERE vs.visit_id = ?
        ORDER BY vs.visit_service_id
    """
    return _execute_query(query, (visit_id,), fetch_all=True)

def remove_service_from_visit(visit_service_id):
    """Removes a service from a visit, then recalculates total. Returns True/False/None."""
    query_get_visit_id = "SELECT visit_id FROM visit_services WHERE visit_service_id = ?"
    visit_info = _execute_query(query_get_visit_id, (visit_service_id,), fetch_one=True)

    if not visit_info: return False # Not found

    visit_id = visit_info['visit_id']
    query_delete = "DELETE FROM visit_services WHERE visit_service_id = ?"
    deleted = _execute_query(query_delete, (visit_service_id,), commit=True)

    if deleted is True: # Only recalc if delete succeeded
        _recalculate_visit_total(visit_id)
    return deleted # Return result of delete operation

def add_prescription_to_visit(visit_id, medication_id, quantity, price_charged, instructions=""):
    """Adds a prescription to a visit, then recalculates total. Returns visit_prescription_id or None/False."""
    query = """
        INSERT INTO visit_prescriptions (visit_id, medication_id, quantity, price_charged, instructions)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (visit_id, medication_id, quantity, price_charged, instructions)
    result_id = _execute_query(query, params, commit=True)
    if isinstance(result_id, int):
        _recalculate_visit_total(visit_id)
        return result_id
    return None

def get_prescriptions_for_visit(visit_id):
    """Gets all prescriptions for a visit. Returns list of dicts."""
    query = """
        SELECT vp.*, m.name as medication_name, m.description as medication_description
        FROM visit_prescriptions vp
        JOIN medications m ON vp.medication_id = m.medication_id
        WHERE vp.visit_id = ?
        ORDER BY vp.visit_prescription_id
    """
    return _execute_query(query, (visit_id,), fetch_all=True)

def remove_prescription_from_visit(visit_prescription_id):
    """Removes a prescription from a visit, then recalculates total. Returns True/False/None."""
    query_get_visit_id = "SELECT visit_id FROM visit_prescriptions WHERE visit_prescription_id = ?"
    visit_info = _execute_query(query_get_visit_id, (visit_prescription_id,), fetch_one=True)

    if not visit_info: return False # Not found

    visit_id = visit_info['visit_id']
    query_delete = "DELETE FROM visit_prescriptions WHERE visit_prescription_id = ?"
    deleted = _execute_query(query_delete, (visit_prescription_id,), commit=True)

    if deleted is True: # Only recalc if delete succeeded
        _recalculate_visit_total(visit_id)
    return deleted

# --- Debt Management ---

def get_patients_with_debt():
    """Retrieves patients with total outstanding debt > 0. Returns list of dicts."""
    query = """
        SELECT
            p.patient_id,
            p.name,
            p.phone_number,
            SUM(v.due_amount) as total_due
        FROM patients p
        JOIN visits v ON p.patient_id = v.patient_id
        WHERE v.due_amount > 0.001 -- Tolerance for floating point
        GROUP BY p.patient_id, p.name, p.phone_number
        HAVING SUM(v.due_amount) > 0.001
        ORDER BY total_due DESC;
    """
    return _execute_query(query, fetch_all=True)

# --- Dashboard Summary ---

def get_total_patients_count():
    """Gets the total number of patients. Returns int."""
    query = "SELECT COUNT(*) as count FROM patients"
    result = _execute_query(query, fetch_one=True)
    return result.get('count', 0) if result else 0

def get_todays_visits_count(visit_date=None):
    """Gets the number of visits for a specific date (default today). Returns int."""
    visit_date = visit_date or date.today()
    date_str = visit_date.strftime('%Y-%m-%d')
    query = "SELECT COUNT(*) as count FROM visits WHERE visit_date = ?"
    result = _execute_query(query, (date_str,), fetch_one=True)
    return result.get('count', 0) if result else 0

def get_total_revenue_today(visit_date=None):
    """Gets total paid amount for visits on a specific date (default today). Returns float."""
    visit_date = visit_date or date.today()
    date_str = visit_date.strftime('%Y-%m-%d')
    query = "SELECT COALESCE(SUM(paid_amount), 0) as total_paid FROM visits WHERE visit_date = ?"
    result = _execute_query(query, (date_str,), fetch_one=True)
    return result.get('total_paid', 0.0) if result else 0.0

def get_total_outstanding_debt():
    """Gets total outstanding debt across all visits. Returns float."""
    query = "SELECT COALESCE(SUM(due_amount), 0) as total_debt FROM visits WHERE due_amount > 0.001"
    result = _execute_query(query, fetch_one=True)
    return result.get('total_debt', 0.0) if result else 0.0


# --- Backup and Restore ---

def backup_database(backup_folder_path):
    """Copies the current database file to the backup folder. Returns (bool, str)."""
    db_path = DATABASE_PATH
    if not db_path or not db_path.exists():
        msg = f"Error: Source database file not found at {db_path}."
        print(msg)
        return False, msg

    backup_dir = Path(backup_folder_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file_name = f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    backup_file_path = backup_dir / backup_file_name

    try:
        shutil.copy2(db_path, backup_file_path) # copy2 preserves metadata
        msg = f"Database successfully backed up to: {backup_file_path}"
        print(msg)
        return True, str(backup_file_path)
    except Exception as e:
        msg = f"Error during database backup: {e}"
        print(msg)
        return False, msg

def restore_database(backup_file_path):
    """Replaces current DB with backup, checking schema after. Returns (bool, str)."""
    backup_path = Path(backup_file_path)
    db_path = DATABASE_PATH

    if not backup_path.exists():
        msg = f"Error: Selected backup file not found at {backup_path}."
        print(msg)
        return False, msg

    if not db_path:
        msg = "Error: DATABASE_PATH is not configured."
        print(msg)
        return False, msg

    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("Attempting to restore. Ensure the application handles connection closing properly.")

    try:
        # Optional: Backup current DB before overwriting
        pre_restore_backup_name = f"{db_path.stem}_pre-restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
        pre_restore_backup_path = db_path.parent / pre_restore_backup_name
        if db_path.exists():
            shutil.copy2(db_path, pre_restore_backup_path)
            print(f"Created pre-restore backup: {pre_restore_backup_path}")

        shutil.copy2(backup_path, db_path)
        print(f"Database successfully restored from: {backup_path} to {db_path}")

        print("Checking/Updating database schema after restore...")
        if initialize_database():
             print("Schema check/update successful.")
        else:
             print("Warning: Schema check/update after restore failed.")

        return True, str(db_path)
    except Exception as e:
        msg = f"Error during database restore: {e}"
        print(msg)
        # Consider restoring pre_restore_backup here if needed
        return False, msg

# --- Reporting ---

def get_patient_financial_summary(patient_id):
    """Calculates total billed, paid, and due for a patient. Returns dict or None."""
    query = """
        SELECT
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(paid_amount), 0) as total_paid,
            COALESCE(SUM(due_amount), 0) as total_due
        FROM visits
        WHERE patient_id = ?;
    """
    return _execute_query(query, (patient_id,), fetch_one=True)


# Example usage for testing (optional)
if __name__ == '__main__':
    print("Testing Data Manager (requires connection.py and schema.py)...")
    if initialize_database():
        print("\n--- Database Initialized ---")

        # Add Patient Example
        print("\n--- Testing Add Patient ---")
        new_id = add_patient("Bob The Builder", "Wendy", "Male", 35, "Fixit Town", "555-FIXIT", "Can fix anything")
        if new_id:
            print(f"Added patient with ID: {new_id}")
            patient = get_patient_by_id(new_id)
            print(f"Retrieved: {patient}")

            # Update Patient Example
            print("\n--- Testing Update Patient ---")
            updated = update_patient(new_id, "Bob The Great Builder", "Wendy", "Male", 36, "Fixit City", "555-BUILD", "Can build anything")
            if updated is True:
                print(f"Patient {new_id} updated successfully.")
                patient = get_patient_by_id(new_id)
                print(f"Updated Data: {patient}")
            else:
                print(f"Failed to update patient {new_id}. Result: {updated}")

            # Add Visit Example
            print("\n--- Testing Add Visit ---")
            visit_id = add_visit(new_id, date.today(), notes="Checkup")
            if visit_id:
                print(f"Added visit with ID: {visit_id} for patient {new_id}")
                visits = get_patient_visits(new_id)
                print(f"Patient Visits: {visits}")

                # Add Service/Prescription to Visit (requires services/meds to exist)
                # ... (add test services/meds first if needed) ...

            else:
                print("Failed to add visit.")

            # Financial Summary
            print("\n--- Testing Financial Summary ---")
            summary = get_patient_financial_summary(new_id)
            print(f"Financial Summary for patient {new_id}: {summary}")

        else:
            print("Failed to add patient.")

        print("\n--- Testing Dashboard Stats ---")
        print(f"Total Patients: {get_total_patients_count()}")
        print(f"Today's Visits: {get_todays_visits_count()}")
        print(f"Today's Revenue: {get_total_revenue_today():.2f}")
        print(f"Total Debt: {get_total_outstanding_debt():.2f}")

        print("\n--- Data Manager Test Complete ---")
    else:
        print("\n--- Database Initialization Failed - Cannot Run Tests ---")