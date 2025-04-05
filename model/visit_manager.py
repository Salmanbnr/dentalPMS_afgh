# model/visit_manager.py

from database.data_manager import (get_visit_by_id, add_visit, update_visit_details,
                                 get_patient_by_id, get_all_services, get_all_medications,
                                 add_service_to_visit, remove_service_from_visit,
                                 add_prescription_to_visit, remove_prescription_from_visit,
                                 get_services_for_visit, get_prescriptions_for_visit,
                                 update_visit_payment, calculate_visit_number)

def load_initial_data(patient_id, is_editing, visit_id=None):
    """Load patient, services, meds, and existing visit data if editing."""
    patient_data = get_patient_by_id(patient_id)
    if not patient_data:
        return False

    services = get_all_services(active_only=True)
    meds = get_all_medications(active_only=True)
    if services is None or meds is None:
        return False  # Check if DB query failed

    available_services = {s['name']: {'id': s['service_id'], 'price': s['default_price']} for s in services}
    available_medications = {m['name']: {'id': m['medication_id'], 'price': m.get('default_price', 0.0)} for m in meds}

    visit_data = None
    if is_editing:
        visit_data = get_visit_by_id(visit_id)
        if not visit_data:
            return False  # Editing non-existent visit

        # Ensure we use the correct patient_id from the visit data
        visit_patient_id = visit_data.get('patient_id')
        if visit_patient_id != patient_id:
            print(f"Warning: Visit {visit_id} belongs to patient {visit_patient_id}, not {patient_id}")

        # Calculate visit number using the visit's patient_id and date
        visit_date = visit_data.get('visit_date')
        if visit_date:
            visit_number = calculate_visit_number(visit_patient_id, visit_date)
            visit_data['visit_number'] = visit_number
        else:
            print(f"Warning: No visit_date found for visit {visit_id}")
            visit_data['visit_number'] = 'N/A'

    return patient_data, visit_data, available_services, available_medications

def save_visit_details(visit_id, visit_date, notes, lab_results, paid_amount):
    """Save the visit details and update payment information."""
    success_details = update_visit_details(visit_id, visit_date, notes, lab_results)
    if success_details is not True:
        return False

    success_payment = update_visit_payment(visit_id, paid_amount)
    if success_payment is not True:
        return False

    return True

def add_new_visit(patient_id, visit_date, notes, lab_results, services_table, prescriptions_table, paid_amount):
    """Add a new visit and its associated services and prescriptions."""
    new_visit_id = add_visit(patient_id, visit_date, notes, lab_results)
    if not new_visit_id:
        return None

    services_added_ok = add_visit_items(new_visit_id, services_table, is_service=True)
    prescriptions_added_ok = add_visit_items(new_visit_id, prescriptions_table, is_service=False)

    success_payment = update_visit_payment(new_visit_id, paid_amount)
    if success_payment is not True:
        return None

    if services_added_ok and prescriptions_added_ok:
        return new_visit_id
    else:
        return None

def add_visit_items(visit_id, table, is_service):
    """Add services or prescriptions to the visit from the table."""
    added_ok = True
    for row in range(table.rowCount()):
        item_id = int(table.item(row, 0).text())  # ID was stored in hidden col
        col2_val = table.item(row, 2).text()
        price = float(table.item(row, 3).text())
        notes = table.item(row, 4).text()

        if is_service:
            tooth_num = int(col2_val) if col2_val.isdigit() else None
            if not add_service_to_visit(visit_id, item_id, tooth_num, price, notes):
                added_ok = False
        else:
            qty = int(col2_val)
            if not add_prescription_to_visit(visit_id, item_id, qty, price, notes):
                added_ok = False

    return added_ok

def load_visit_data(visit_id):
    """Load all necessary data for the visit. Returns data if successful."""
    visit_data = get_visit_by_id(visit_id)
    if not visit_data:
        print(f"Error: Visit data not found for ID: {visit_id}")
        return None

    patient_id = visit_data.get('patient_id')
    if not patient_id:
        print(f"Error: Patient ID missing in visit data for visit ID: {visit_id}")
        return None

    patient_data = get_patient_by_id(patient_id)
    if not patient_data:
        print(f"Error: Patient data not found for ID: {patient_id}")
        return None

    services = get_services_for_visit(visit_id)
    prescriptions = get_prescriptions_for_visit(visit_id)

    return visit_data, patient_data, services, prescriptions


def _execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """Helper function to execute SQL queries."""
    from database.connection import get_db_connection, close_db_connection
    import sqlite3

    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed in _execute_query.")
        return None
    result = None
    last_row_id = None
    try:
        conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
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

    except sqlite3.IntegrityError as e:
        print(f"Database Integrity Error: {e} executing query: {query}")
        if conn and commit:
            conn.rollback()
        result = False  # Indicate specific failure type (e.g., UNIQUE constraint)
    except sqlite3.Error as e:
        print(f"Database Error: {e} executing query: {query}")
        if conn and commit:
            conn.rollback()
        result = None  # General failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn and commit:
            conn.rollback()
        result = None
    finally:
        close_db_connection(conn)

    if commit:
        return last_row_id if last_row_id is not None and last_row_id > 0 else True if result is None else result
    else:
        return result