# model/visit_detail_window_model.py

# --- Database/Model Imports (Keep your existing imports) ---
# Mock functions for standalone testing if needed
try:
    # Assume these exist in your project structure
    from database.data_manager import (get_patient_by_id, get_service_by_id, get_visit_by_id, get_services_for_visit,
                                       get_prescriptions_for_visit, update_visit_details,
                                       update_visit_payment, add_service_to_visit, remove_service_from_visit,
                                       add_prescription_to_visit, remove_prescription_from_visit)
    from model.visit_manager import load_visit_data, get_all_services, get_all_medications
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Warning: Database modules not found. Using placeholder data.")
    # --- Placeholder Functions (for running standalone without full DB setup) ---
    def get_patient_by_id(id): return {'patient_id': id, 'name': f"Test Patient {id}"} if id == 4 else None
    def get_service_by_id(id): return {'service_id': id, 'name': 'Cleaning', 'default_price': 50.0} if id == 1 else None
    def get_visit_by_id(id): return {'visit_id': id, 'patient_id': 4, 'visit_date': '2023-04-05', 'notes': 'Initial checkup', 'lab_results': '', 'total_amount': 50.0, 'paid_amount': 20.0, 'due_amount': 30.0, 'visit_number': 101} if id == 9 else None
    def get_services_for_visit(id): return [{'visit_service_id': 10, 'service_id': 1, 'service_name': 'Cleaning', 'tooth_number': None, 'price_charged': 50.0, 'notes': 'Routine cleaning'}] if id == 9 else []
    def get_prescriptions_for_visit(id): return []
    def update_visit_details(vid, date, notes, lab): print(f"Mock Update Visit {vid}: {date}, {notes}, {lab}"); return True
    def update_visit_payment(vid, paid): print(f"Mock Update Payment {vid}: {paid}"); return True
    def add_service_to_visit(vid, sid, tooth, price, notes): print(f"Mock Add Service {vid}: {sid}, {tooth}, {price}, {notes}"); return 11 # Return dummy ID
    def remove_service_from_visit(vsid): print(f"Mock Remove Service {vsid}"); return True
    def add_prescription_to_visit(vid, mid, qty, price, instr): print(f"Mock Add Prescription {vid}: {mid}, {qty}, {price}, {instr}"); return 21 # Return dummy ID
    def remove_prescription_from_visit(vpid): print(f"Mock Remove Prescription {vpid}"); return True
    def load_visit_data(vid):
        visit = get_visit_by_id(vid)
        if not visit: return None
        patient = get_patient_by_id(visit['patient_id'])
        services = get_services_for_visit(vid)
        prescriptions = get_prescriptions_for_visit(vid)
        return visit, patient, services, prescriptions
    def get_all_services(active_only=True): return [{'service_id': 1, 'name': 'Cleaning', 'default_price': 50.0}, {'service_id': 2, 'name': 'Filling', 'default_price': 120.0}]
    def get_all_medications(active_only=True): return [{'medication_id': 101, 'name': 'Painkiller A', 'default_price': 5.0}, {'medication_id': 102, 'name': 'Antibiotic B', 'default_price': 15.0}]
# --- End Placeholder Functions ---

class VisitDetailModel:
    def __init__(self, visit_id, patient_id=None):
        self.visit_id = visit_id
        self.patient_id = patient_id
        self.visit_data = None
        self.patient_data = None
        self.services = []
        self.prescriptions = []
        self.new_services = []
        self.new_prescriptions = []
        self.available_services = {}
        self.available_medications = {}

        self._load_initial_data()

    def _load_initial_data(self):
        """Load all necessary data for the visit."""
        try:
            data = load_visit_data(self.visit_id)
            if not data:
                raise ValueError(f"Could not load data for visit ID: {self.visit_id}.")
            self.visit_data, self.patient_data, self.services, self.prescriptions = data

            # Ensure patient_id is set, using visit_data if needed
            if self.patient_id is None and self.patient_data:
                self.patient_id = self.patient_data.get('patient_id')
            elif self.patient_id is None and self.visit_data:
                self.patient_id = self.visit_data.get('patient_id')

            if not self.patient_data and self.patient_id: # Try loading patient data if missing
                self.patient_data = get_patient_by_id(self.patient_id) or {}

            # Load available services and medications
            svcs = get_all_services(active_only=True) or []
            self.available_services = {s['name']: {'id': s['service_id'], 'price': s['default_price']} for s in svcs}
            meds = get_all_medications(active_only=True) or []
            self.available_medications = {m['name']: {'id': m['medication_id'], 'price': m.get('default_price', 0.0)} for m in meds}

            self.new_services.clear()
            self.new_prescriptions.clear()
            return True
        except Exception as e:
            raise ValueError(f"An error occurred while loading data: {e}")

    def update_visit_details(self, date, notes, lab):
        """Update visit details in the database."""
        return update_visit_details(self.visit_id, date, notes, lab)

    def update_visit_payment(self, paid_amount):
        """Update visit payment information in the database."""
        return update_visit_payment(self.visit_id, paid_amount)

    def add_service_to_visit(self, service_id, tooth, price, notes):
        """Add a service to the visit."""
        return add_service_to_visit(self.visit_id, service_id, tooth, price, notes)

    def remove_service_from_visit(self, service_id):
        """Remove a service from the visit."""
        return remove_service_from_visit(service_id)

    def add_prescription_to_visit(self, medication_id, qty, price, instructions):
        """Add a prescription to the visit."""
        return add_prescription_to_visit(self.visit_id, medication_id, qty, price, instructions)

    def remove_prescription_from_visit(self, prescription_id):
        """Remove a prescription from the visit."""
        return remove_prescription_from_visit(prescription_id)
