# dental_clinic/database/data_manager.py
import sqlite3
import shutil
import os
from datetime import date, datetime
from pathlib import Path
import sys

# Add project root to sys.path to allow absolute imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    # Use absolute import based on the adjusted sys.path
    from database.connection import get_db_connection, close_db_connection, DATABASE_PATH
    from database.schema import initialize_database # For restore and direct testing
except ImportError as e:
    print(f"Error importing modules in data_manager.py: {e}")
    # Attempt relative import as fallback (might work if run from specific locations)
    try:
        from .connection import get_db_connection, close_db_connection, DATABASE_PATH
        from .schema import initialize_database
    except ImportError:
         print("Could not import connection/schema using relative path either.")
         sys.exit(1) # Exit if essential modules can't be imported

# --- Helper Functions ---

def _execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False): # [cite: 94]
    """Helper function to execute SQL queries."""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return None # Indicate failure clearly
    result = None
    last_row_id = None
    try:
        # No need to set row_factory again if it's set in get_db_connection
        # conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch_one:
            result = cursor.fetchone() # [cite: 95]
        elif fetch_all:
            result = cursor.fetchall() # List of Row objects [cite: 95]

        if commit:
            conn.commit()
            last_row_id = cursor.lastrowid # Get ID for INSERT operations [cite: 95]
            # print(f"Query committed successfully: {query[:60]}...") # Reduce verbosity
        # else:
        #      print(f"Query executed successfully (no commit): {query[:60]}...") # Reduce verbosity

    except sqlite3.IntegrityError as e:
        print(f"Database Integrity Error: {e} executing query: {query}")
        if conn and commit: conn.rollback()
        result = False # Use False for specific integrity errors (like UNIQUE constraint)
    except sqlite3.Error as e:
        print(f"Database Error: {e} executing query: {query}") # [cite: 96]
        if conn and commit:
            conn.rollback() # Rollback on error during commit operations
        result = None # Indicate general failure
    except Exception as e:
       print(f"An unexpected error occurred: {e}") # [cite: 97]
       if conn and commit:
            conn.rollback() # [cite: 97]
       result = None # Indicate general failure
    finally:
        close_db_connection(conn)

    # Process results *after* closing connection
    if isinstance(result, list):
        # Convert Row objects to dictionaries
        return [dict(row) for row in result] if result else [] # [cite: 97]
    elif isinstance(result, sqlite3.Row):
        return dict(result) # [cite: 98]
    elif commit:
        # For successful commits:
        # If last_row_id has a value (INSERT), return it.
        # Otherwise (UPDATE/DELETE or INSERT without generated ID), return True.
        return last_row_id if last_row_id is not None and last_row_id > 0 else True # [cite: 98]
    elif result is False: # Specific case for IntegrityError handled above
        return False
    else:
        # For non-commit, non-fetch (should be rare) or if fetch returned None
        # Also catches general failures where result was set to None
        return result # Returns None for failures, or the fetched data if fetch=True but no commit

# --- Patient Management ---

def add_patient(name: str, father_name: str, gender: str, age: int, address: str, phone_number: str, medical_history: str): # [cite: 99]
    """Adds a new patient to the database."""
    query = """
        INSERT INTO patients (name, father_name, gender, age, address, phone_number, medical_history, first_visit_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (name, father_name, gender, age, address, phone_number, medical_history, date.today().strftime('%Y-%m-%d'))
    # Returns patient_id on success, None or False on failure
    result = _execute_query(query, params, commit=True) # [cite: 100]
    return result if isinstance(result, int) else None # Return ID only if it's an int

def get_patient_by_id(patient_id): # [cite: 100]
    """Retrieves a single patient by their ID."""
    query = "SELECT * FROM patients WHERE patient_id = ?"
    return _execute_query(query, (patient_id,), fetch_one=True)

def get_all_patients(search_term=""): # [cite: 100]
    """Retrieves all patients, optionally filtering by name or phone."""
    if search_term:
        query = "SELECT * FROM patients WHERE name LIKE ? OR phone_number LIKE ? ORDER BY name COLLATE NOCASE" # [cite: 101]
        params = (f'%{search_term}%', f'%{search_term}%')
    else:
        query = "SELECT * FROM patients ORDER BY name COLLATE NOCASE" # [cite: 101]
        params = ()
    return _execute_query(query, params, fetch_all=True)

def update_patient(patient_id: int, name: str, father_name: str, gender: str, age: int, address: str, phone_number: str, medical_history: str): # [cite: 101]
    """Updates an existing patient's details."""
    query = """
        UPDATE patients
        SET name = ?, father_name = ?, gender = ?, age = ?, address = ?,
            phone_number = ?, medical_history = ?, last_updated = CURRENT_TIMESTAMP
        WHERE patient_id = ?
    """ #
    params = (name, father_name, gender, age, address, phone_number, medical_history, patient_id)
    # Returns True on success, None or False on failure
    return _execute_query(query, params, commit=True) # [cite: 103]

def delete_patient(patient_id): # [cite: 103]
    """Deletes a patient and their associated visits (due to CASCADE)."""
    query = "DELETE FROM patients WHERE patient_id = ?"
    return _execute_query(query, (patient_id,), commit=True)

# --- Service Management ---
def add_service(name, description, default_price): # [cite: 103]
    query = "INSERT INTO services (name, description, default_price) VALUES (?, ?, ?)"
    params = (name, description, default_price)
    result = _execute_query(query, params, commit=True) # [cite: 104]
    return result if isinstance(result, int) else None

def get_service_by_id(service_id): # [cite: 104]
    query = "SELECT * FROM services WHERE service_id = ?"
    return _execute_query(query, (service_id,), fetch_one=True)

def get_all_services(active_only=True): # [cite: 104]
    query = "SELECT * FROM services"
    params = ()
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name COLLATE NOCASE" # [cite: 105]
    return _execute_query(query, params, fetch_all=True)

def update_service(service_id, name, description, default_price, is_active): # [cite: 105]
    query = """
        UPDATE services
        SET name = ?, description = ?, default_price = ?, is_active = ?, last_updated = CURRENT_TIMESTAMP
        WHERE service_id = ?
    """ #[cite: 105]
    params = (name, description, default_price, 1 if is_active else 0, service_id) # [cite: 106]
    return _execute_query(query, params, commit=True)

def delete_service(service_id): # [cite: 106]
    """Deletes a service. Returns False if restricted by foreign key."""
    query = "DELETE FROM services WHERE service_id = ?"
    return _execute_query(query, (service_id,), commit=True)


# --- Medication Management ---
def add_medication(name, description, default_price): # [cite: 106]
    query = "INSERT INTO medications (name, description, default_price) VALUES (?, ?, ?)"
    params = (name, description, default_price if default_price is not None else 0.0) # [cite: 107]
    result = _execute_query(query, params, commit=True) # [cite: 107]
    return result if isinstance(result, int) else None

def get_medication_by_id(medication_id): # [cite: 107]
    query = "SELECT * FROM medications WHERE medication_id = ?"
    return _execute_query(query, (medication_id,), fetch_one=True)

def get_all_medications(active_only=True): # [cite: 107]
    query = "SELECT * FROM medications"
    params=()
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name COLLATE NOCASE"
    return _execute_query(query, params, fetch_all=True) # [cite: 108]

def update_medication(medication_id, name, description, default_price, is_active): # [cite: 108]
    query = """
        UPDATE medications
        SET name = ?, description = ?, default_price = ?, is_active = ?, last_updated = CURRENT_TIMESTAMP
        WHERE medication_id = ?
    """ #[cite: 108]
    params = (name, description, default_price if default_price is not None else 0.0, 1 if is_active else 0, medication_id) # [cite: 109]
    return _execute_query(query, params, commit=True)

def delete_medication(medication_id): # [cite: 109]
    """Deletes a medication. Returns False if restricted by foreign key."""
    query = "DELETE FROM medications WHERE medication_id = ?"
    return _execute_query(query, (medication_id,), commit=True)


# --- Visit Management ---
def add_visit(patient_id, visit_date, notes="", lab_results=""): # [cite: 109]
    query = """
        INSERT INTO visits (patient_id, visit_date, notes, lab_results, total_amount, paid_amount, due_amount)
        VALUES (?, ?, ?, ?, 0, 0, 0)
    """ #
    # Ensure visit_date is a string in 'YYYY-MM-DD' format
    if isinstance(visit_date, (date, datetime)):
        date_str = visit_date.strftime('%Y-%m-%d')
    elif isinstance(visit_date, str):
        # Basic validation or attempt conversion if needed, assume correct format for now
        date_str = visit_date
    else:
        print(f"Warning: Invalid visit_date type: {type(visit_date)}. Using today.")
        date_str = date.today().strftime('%Y-%m-%d')

    params = (patient_id, date_str, notes, lab_results)
    result = _execute_query(query, params, commit=True) # [cite: 110]
    return result if isinstance(result, int) else None

def get_visit_by_id(visit_id): # [cite: 110]
    query = "SELECT * FROM visits WHERE visit_id = ?"
    return _execute_query(query, (visit_id,), fetch_one=True)

def get_patient_visits(patient_id): # [cite: 110]
    query = "SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC" # [cite: 111]
    return _execute_query(query, (patient_id,), fetch_all=True)

def update_visit_details(visit_id, visit_date, notes, lab_results): # [cite: 111]
     query = """
         UPDATE visits
         SET visit_date = ?, notes = ?, lab_results = ?, last_updated = CURRENT_TIMESTAMP
         WHERE visit_id = ?
     """ #[cite: 111]
     # Ensure visit_date is a string
     if isinstance(visit_date, (date, datetime)):
         date_str = visit_date.strftime('%Y-%m-%d')
     elif isinstance(visit_date, str):
         date_str = visit_date
     else:
         print(f"Warning: Invalid visit_date type for update: {type(visit_date)}. Update might fail.")
         return False # Or handle appropriately

     params = (date_str, notes, lab_results, visit_id) # [cite: 112]
     return _execute_query(query, params, commit=True)

def update_visit_payment(visit_id, paid_amount): # [cite: 112]
    visit = get_visit_by_id(visit_id)
    if not visit:
        print(f"Error: Visit with ID {visit_id} not found for payment update.")
        return False

    total_amount = visit.get('total_amount', 0.0) # Use .get for safety
    try:
        # Ensure paid_amount is a float
        new_paid_amount = float(paid_amount)
        if new_paid_amount < 0:
             print("Error: Paid amount cannot be negative.")
             return False
    except (ValueError, TypeError):
        print(f"Invalid paid amount provided: {paid_amount}") # [cite: 112]
        return False

    # Paid amount should not exceed total amount if you enforce strict payment rules
    # If overpayment is allowed, this check can be removed/modified.
    # if new_paid_amount > total_amount:
    #     print(f"Warning: Paid amount ({new_paid_amount}) exceeds total amount ({total_amount}). Adjusting.")
    #     new_paid_amount = total_amount # Or handle as overpayment credit

    new_due_amount = max(0.0, total_amount - new_paid_amount) # Ensure due amount is not negative [cite: 113]

    query = """
        UPDATE visits
        SET paid_amount = ?, due_amount = ?, last_updated = CURRENT_TIMESTAMP
        WHERE visit_id = ?
    """ #[cite: 113]
    params = (new_paid_amount, new_due_amount, visit_id) # [cite: 114]
    return _execute_query(query, params, commit=True)

def _recalculate_visit_total(visit_id): # [cite: 114]
    """Internal function to recalculate visit total based on items and update DB."""
    query_sum_services = "SELECT COALESCE(SUM(price_charged), 0) as total_s FROM visit_services WHERE visit_id = ?"
    query_sum_prescriptions = "SELECT COALESCE(SUM(price_charged), 0) as total_p FROM visit_prescriptions WHERE visit_id = ?"

    # Need to execute these potentially within a single transaction or carefully
    # Using _execute_query re-opens/closes connection each time, less efficient
    # For simplicity here, we accept the overhead. For performance, refactor needed.
    total_s_result = _execute_query(query_sum_services, (visit_id,), fetch_one=True)
    total_p_result = _execute_query(query_sum_prescriptions, (visit_id,), fetch_one=True)

    total_s = total_s_result.get('total_s', 0.0) if total_s_result else 0.0
    total_p = total_p_result.get('total_p', 0.0) if total_p_result else 0.0
    new_total = total_s + total_p # [cite: 115]

    # Fetch current paid amount to calculate new due amount
    visit = get_visit_by_id(visit_id) # Another connection open/close
    if not visit:
        print(f"Error recalculating total: Visit {visit_id} not found.")
        return False
    current_paid = visit.get('paid_amount', 0.0) # [cite: 115]
    new_due = max(0.0, new_total - current_paid) # [cite: 115]

    query_update = """
        UPDATE visits SET total_amount = ?, due_amount = ?, last_updated = CURRENT_TIMESTAMP
        WHERE visit_id = ?
    """ #[cite: 115]
    return _execute_query(query_update, (new_total, new_due, visit_id), commit=True) # [cite: 116]


# --- Visit Items (Services & Prescriptions) ---

def add_service_to_visit(visit_id, service_id, tooth_number, price_charged, notes=""): # [cite: 116]
    """Adds a service to a visit and recalculates total. Returns visit_service_id."""
    query = """
        INSERT INTO visit_services (visit_id, service_id, tooth_number, price_charged, notes)
        VALUES (?, ?, ?, ?, ?)
    """
    # Ensure price is float
    try:
        price_f = float(price_charged)
    except (ValueError, TypeError):
        print(f"Invalid price for service: {price_charged}")
        return None

    params = (visit_id, service_id, tooth_number, price_f, notes)
    result_id = _execute_query(query, params, commit=True) # Returns visit_service_id or True/None/False

    if isinstance(result_id, int):
        _recalculate_visit_total(visit_id) # Update visit total [cite: 116]
        return result_id # Return visit_service_id [cite: 117]
    elif result_id is True: # INSERT succeeded but no ID returned (shouldn't happen for AUTOINCREMENT)
         _recalculate_visit_total(visit_id)
         print("Warning: Service added but could not confirm ID.")
         return True # Indicate success
    else: # Failed (None or False)
        return None

def get_services_for_visit(visit_id): # [cite: 117]
    """Retrieves all services linked to a specific visit, including service name."""
    query = """
        SELECT vs.*, s.name as service_name
        FROM visit_services vs
        JOIN services s ON vs.service_id = s.service_id
        WHERE vs.visit_id = ?
        ORDER BY vs.visit_service_id
    """ #
    return _execute_query(query, (visit_id,), fetch_all=True)

def remove_service_from_visit(visit_service_id): # [cite: 118]
    """Removes a service from a visit and recalculates total."""
    # First, get the visit_id to recalculate later
    query_get_visit_id = "SELECT visit_id FROM visit_services WHERE visit_service_id = ?"
    visit_info = _execute_query(query_get_visit_id, (visit_service_id,), fetch_one=True)

    if not visit_info:
        print(f"Error: Visit service item with ID {visit_service_id} not found.")
        return False # Service not found

    visit_id = visit_info.get('visit_id')
    if visit_id is None:
        print("Error: Could not retrieve visit_id for the service item.")
        return False

    # Now, delete the item
    query_delete = "DELETE FROM visit_services WHERE visit_service_id = ?"
    deleted = _execute_query(query_delete, (visit_service_id,), commit=True) # [cite: 118]

    if deleted is True: # Check if delete was successful (returned True)
        _recalculate_visit_total(visit_id) # Update visit total [cite: 119]
        return True
    else:
        print(f"Failed to delete visit service item {visit_service_id}.")
        # Attempt recalculation anyway? Maybe not, state might be inconsistent.
        return False

def add_prescription_to_visit(visit_id, medication_id, quantity, price_charged, instructions=""): # [cite: 119]
    """Adds a prescription to a visit and recalculates total. Returns visit_prescription_id."""
    query = """
        INSERT INTO visit_prescriptions (visit_id, medication_id, quantity, price_charged, instructions)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        qty_int = int(quantity)
        price_f = float(price_charged)
        if qty_int <= 0:
            print("Error: Quantity must be positive.")
            return None
    except (ValueError, TypeError):
        print(f"Invalid quantity or price: {quantity}, {price_charged}")
        return None

    params = (visit_id, medication_id, qty_int, price_f, instructions)
    result_id = _execute_query(query, params, commit=True) # Returns ID or True/None/False [cite: 119]

    if isinstance(result_id, int):
        _recalculate_visit_total(visit_id) # Update visit total
        return result_id # Return visit_prescription_id [cite: 120]
    elif result_id is True:
         _recalculate_visit_total(visit_id)
         print("Warning: Prescription added but could not confirm ID.")
         return True
    else:
        return None

def get_prescriptions_for_visit(visit_id): # [cite: 120]
    """Retrieves all prescriptions for a specific visit, including medication name."""
    query = """
        SELECT vp.*, m.name as medication_name
        FROM visit_prescriptions vp
        JOIN medications m ON vp.medication_id = m.medication_id
        WHERE vp.visit_id = ?
        ORDER BY vp.visit_prescription_id
    """ #
    return _execute_query(query, (visit_id,), fetch_all=True)

def remove_prescription_from_visit(visit_prescription_id): # [cite: 121]
    """Removes a prescription from a visit and recalculates total."""
    query_get_visit_id = "SELECT visit_id FROM visit_prescriptions WHERE visit_prescription_id = ?"
    visit_info = _execute_query(query_get_visit_id, (visit_prescription_id,), fetch_one=True)

    if not visit_info:
        print(f"Error: Visit prescription item with ID {visit_prescription_id} not found.")
        return False

    visit_id = visit_info.get('visit_id')
    if visit_id is None:
         print("Error: Could not retrieve visit_id for the prescription item.")
         return False

    query_delete = "DELETE FROM visit_prescriptions WHERE visit_prescription_id = ?"
    deleted = _execute_query(query_delete, (visit_prescription_id,), commit=True) # [cite: 121]

    if deleted is True:
        _recalculate_visit_total(visit_id) # [cite: 121]
        return True
    else:
        print(f"Failed to delete visit prescription item {visit_prescription_id}.")
        return False

# --- Debt Management ---

def get_patients_with_debt(): # [cite: 121]
    """Retrieves patient information for those with outstanding balances across all visits."""
    query = """
        SELECT
            p.patient_id,
            p.name,
            p.phone_number,
            p.address, -- Added address here
            SUM(v.due_amount) as total_due
        FROM patients p
        JOIN visits v ON p.patient_id = v.patient_id -- [cite: 123]
        WHERE v.due_amount > 0.001 -- Use a small tolerance for floating point [cite: 123]
        GROUP BY p.patient_id -- Group by unique patient ID
        -- HAVING SUM(v.due_amount) > 0.001 -- Redundant with WHERE clause filtering visits
        ORDER BY total_due DESC;
    """ #
    # Need columns from p in GROUP BY if not using aggregate function on them (SQLite specific behavior might vary)
    # Standard SQL requires all non-aggregated SELECT columns in GROUP BY
    # Let's rewrite GROUP BY for broader compatibility and clarity:
    query_corrected = """
        SELECT
            p.patient_id,
            p.name,
            p.phone_number,
            p.address,
            SUM(v.due_amount) as total_due
        FROM patients p
        JOIN visits v ON p.patient_id = v.patient_id
        WHERE v.due_amount > 0.001
        GROUP BY p.patient_id, p.name, p.phone_number, p.address
        ORDER BY total_due DESC;
    """
    return _execute_query(query_corrected, fetch_all=True) # [cite: 124]

# --- Dashboard Summary ---

def get_total_patients_count(): # [cite: 124]
    """Gets the total number of patients."""
    query = "SELECT COUNT(*) as count FROM patients"
    result = _execute_query(query, fetch_one=True)
    return result['count'] if result and 'count' in result else 0

def get_todays_visits_count(visit_date=None): # [cite: 124]
    """Gets the number of visits scheduled for today (or a specific date)."""
    if visit_date is None:
        visit_date = date.today()
    date_str = visit_date.strftime('%Y-%m-%d')
    # This assumes visit_date column stores the date accurately
    # If appointments are scheduled ahead, you might need an 'appointment_date' column
    query = "SELECT COUNT(*) as count FROM visits WHERE visit_date = ?" # [cite: 125]
    result = _execute_query(query, (date_str,), fetch_one=True)
    return result['count'] if result and 'count' in result else 0

def get_total_revenue_today(visit_date=None): # [cite: 125]
    """Gets the total revenue (paid amount) for visits today."""
    if visit_date is None:
        visit_date = date.today()
    date_str = visit_date.strftime('%Y-%m-%d')
    query = "SELECT COALESCE(SUM(paid_amount), 0) as total_paid FROM visits WHERE visit_date = ?"
    result = _execute_query(query, (date_str,), fetch_one=True) # [cite: 126]
    return result['total_paid'] if result and 'total_paid' in result else 0.0

def get_total_outstanding_debt(): # [cite: 126]
    """Gets the total outstanding debt across all patients."""
    query = "SELECT COALESCE(SUM(due_amount), 0) as total_debt FROM visits WHERE due_amount > 0.001"
    result = _execute_query(query, fetch_one=True)
    return result['total_debt'] if result and 'total_debt' in result else 0.0


# --- Backup and Restore ---

def backup_database(backup_folder_path): # [cite: 126]
    """Copies the current database file to the specified backup folder."""
    db_path = DATABASE_PATH
    if not db_path or not db_path.exists():
       print(f"Error: Source database file not found at {db_path}.") # [cite: 127]
       return False, "Source database file not found."

    backup_dir = Path(backup_folder_path)
    try:
        backup_dir.mkdir(parents=True, exist_ok=True) # Ensure backup directory exists [cite: 127]
    except OSError as e:
        print(f"Error creating backup directory {backup_dir}: {e}")
        return False, f"Could not create backup directory: {e}"


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Ensure db_path.stem and db_path.suffix work correctly
    db_filename = db_path.name if db_path else "database_backup"
    backup_file_name = f"{Path(db_filename).stem}_backup_{timestamp}{Path(db_filename).suffix}"
    backup_file_path = backup_dir / backup_file_name

    try:
        shutil.copy2(db_path, backup_file_path) # copy2 preserves metadata [cite: 127]
        print(f"Database successfully backed up to: {backup_file_path}")
        return True, str(backup_file_path) # [cite: 128]
    except Exception as e:
        print(f"Error during database backup: {e}") # [cite: 128]
        return False, str(e)

def restore_database(backup_file_path): # [cite: 128]
    """Replaces the current database file with the selected backup file."""
    backup_path = Path(backup_file_path)
    db_path = DATABASE_PATH

    if not backup_path.exists():
        print(f"Error: Selected backup file not found at {backup_path}.") # [cite: 128]
        return False, "Selected backup file not found."

    if not db_path:
        print("Error: DATABASE_PATH is not configured.") # [cite: 129]
        return False, "Database path configuration error." # [cite: 129]

    # Ensure target directory exists
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True) # [cite: 129]
    except OSError as e:
        print(f"Error creating database directory {db_path.parent}: {e}")
        return False, f"Could not create database directory: {e}"

    # CRUCIAL: Add mechanism to ensure no active connections if possible
    print("Attempting to restore. Ensure the application is fully closed or handles connection closing properly.") # [cite: 130]

    try:
        # Optional: Backup current DB before overwriting
        pre_restore_backup_name = f"{db_path.stem}_pre-restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
        pre_restore_backup_path = db_path.parent / pre_restore_backup_name
        if db_path.exists():
             shutil.copy2(db_path, pre_restore_backup_path)
             print(f"Created pre-restore backup: {pre_restore_backup_path}") #

        shutil.copy2(backup_path, db_path) # [cite: 131]
        print(f"Database successfully restored from: {backup_path} to {db_path}") # [cite: 131]

        # Re-initialize schema to apply any migrations or ensure consistency
        print("Checking/Updating database schema after restore...") # [cite: 131]
        if initialize_database(): # Ensure initialize_database is available
             print("Schema check/update successful.") # [cite: 131]
        else:
             print("Warning: Schema check/update after restore failed.") # [cite: 132]
             # This might indicate issues with the restored DB or schema definitions

        return True, str(db_path) # [cite: 132]
    except Exception as e:
        print(f"Error during database restore: {e}") # [cite: 132]
        # Optional: Restore the pre-restore backup if restore fails midway? Complex. [cite: 133]
        return False, str(e) # [cite: 133]

# --- Reporting ---

def get_patient_financial_summary(patient_id): # [cite: 133]
    """Calculates total billed, paid, and due for a specific patient."""
    query = """
        SELECT
            COALESCE(SUM(total_amount), 0) as total_billed,
            COALESCE(SUM(paid_amount), 0) as total_paid,
            COALESCE(SUM(due_amount), 0) as total_due
        FROM visits
        WHERE patient_id = ?;
    """ #
    return _execute_query(query, (patient_id,), fetch_one=True)


if __name__ == '__main__':
    print("Testing Data Manager (requires connection.py and schema.py)...") # [cite: 134]
    # Ensure DB exists and is initialized first
    if initialize_database(): # [cite: 136]
        print("\n--- Database Initialized/Verified ---")

        # Add Patient Example
        print("\n--- Testing Add Patient ---") # [cite: 136]
        new_id = add_patient( # [cite: 137]
            name="Alice Wonderland",
            father_name="Cheshire Cat", # Added field
            gender="Female",
            age=25,                   # Using age now
            address="123 Rabbit Hole Ln", # Added field [cite: 137]
            phone_number="555-1234",
            medical_history="Curious condition" # [cite: 138]
        )
        if new_id:
            print(f"Added patient with ID: {new_id}") # [cite: 138]
            patient = get_patient_by_id(new_id)
            print(f"Retrieved: {patient}") # [cite: 138]

            # Update Patient Example
            print("\n--- Testing Update Patient ---") # [cite: 139]
            updated = update_patient( # [cite: 139]
                 new_id,
                 name="Alice Kingsleigh", # Changed name
                 father_name="Charles Kingsleigh", # Changed father's name
                 gender="Female", # [cite: 140]
                 age=26, # Updated age [cite: 140]
                 address="456 Looking Glass Ave", # Updated address [cite: 140]
                 phone_number="555-5678", # Updated phone [cite: 140]
                 medical_history="Growing/shrinking syndrome" # Updated history [cite: 140]
             )
            if updated:
                 print(f"Patient {new_id} updated successfully.") # [cite: 141]
                 patient = get_patient_by_id(new_id)
                 print(f"Updated Data: {patient}") # [cite: 141]
            else:
                 print(f"Failed to update patient {new_id}.") # [cite: 142]

            # Test Deleting the patient
            # print("\n--- Testing Delete Patient ---")
            # deleted = delete_patient(new_id)
            # if deleted:
            #     print(f"Patient {new_id} deleted successfully.")
            #     patient_after_delete = get_patient_by_id(new_id)
            #     print(f"Patient after delete attempt: {patient_after_delete}") # Should be None
            # else:
            #      print(f"Failed to delete patient {new_id}.")

        else:
            print("Failed to add patient.") # [cite: 142]

        print("\n--- Testing Get All Patients ---")
        all_patients = get_all_patients()
        print(f"Found {len(all_patients)} patients.")
        # for p in all_patients: print(p)


        print("\n--- Testing Dashboard Stats ---") # [cite: 142]
        print(f"Total Patients: {get_total_patients_count()}")
        print(f"Today's Visits: {get_todays_visits_count()}")
        print(f"Today's Revenue: {get_total_revenue_today():.2f}")
        print(f"Total Debt: {get_total_outstanding_debt():.2f}")

        print("\n--- Data Manager Test Complete ---") # [cite: 142]
    else:
        print("\n--- Database Initialization Failed - Cannot Run Tests ---") # [cite: 143]