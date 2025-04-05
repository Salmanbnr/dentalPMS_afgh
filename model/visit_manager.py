# models/visit_manager.py

from database.data_manager import (get_visit_by_id, add_visit, update_visit_details,
                                   get_patient_by_id, get_all_services, get_all_medications,
                                   add_service_to_visit, remove_service_from_visit,
                                   add_prescription_to_visit, remove_prescription_from_visit,
                                   get_services_for_visit, get_prescriptions_for_visit,
                                   update_visit_payment)

def load_initial_data(patient_id, is_editing, visit_id=None):
    """Load patient, services, meds, and existing visit data if editing."""
    patient_data = get_patient_by_id(patient_id)
    if not patient_data: return False

    services = get_all_services(active_only=True)
    meds = get_all_medications(active_only=True)
    if services is None or meds is None: return False # Check if DB query failed

    available_services = {s['name']: {'id': s['service_id'], 'price': s['default_price']} for s in services}
    available_medications = {m['name']: {'id': m['medication_id'], 'price': m.get('default_price', 0.0)} for m in meds} # Handle optional price

    visit_data = None
    if is_editing:
        visit_data = get_visit_by_id(visit_id)
        if not visit_data: return False # Editing non-existent visit

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
        item_id = int(table.item(row, 0).text()) # ID was stored in hidden col
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



from database.data_manager import (get_visit_by_id, get_services_for_visit,
                                   get_prescriptions_for_visit, get_patient_by_id)

# Existing functions...

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

