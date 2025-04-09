import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker with a locale for Pakistan
fake = Faker('en_PK')

# Database connection setup
DATABASE_PATH = 'database/dental_clinic.db'  # Replace with your actual database path

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def close_db_connection(conn):
    if conn:
        conn.close()

def insert_data():
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Insert Services
        services = [
            ("Teeth Cleaning", "Regular dental cleaning", 1500.0),
            ("Root Canal", "Root canal treatment", 5000.0),
            ("Filling", "Tooth filling procedure", 2000.0),
            ("Extraction", "Tooth extraction procedure", 3000.0),
            ("Crown", "Dental crown placement", 7000.0)
        ]

        for name, description, price in services:
            cursor.execute("""
                INSERT INTO services (name, description, default_price)
                VALUES (?, ?, ?)
            """, (name, description, price))

        # Insert Medications
        medications = [
            ("Paracetamol", "Pain reliever", 50.0),
            ("Amoxicillin", "Antibiotic", 150.0),
            ("Ibuprofen", "Anti-inflammatory", 70.0),
            ("Metronidazole", "Antibiotic", 200.0)
        ]

        for name, description, price in medications:
            cursor.execute("""
                INSERT INTO medications (name, description, default_price)
                VALUES (?, ?, ?)
            """, (name, description, price))

        # Insert Patients and related Visits, Visit Services, and Visit Prescriptions
        for _ in range(150):
            name = fake.name()
            father_name = fake.first_name_male() if random.choice([True, False]) else fake.first_name_female()
            gender = random.choice(['Male', 'Female', 'Other'])
            age = random.randint(18, 80)
            address = fake.address()
            phone_number = fake.phone_number()
            medical_history = fake.text(max_nb_chars=50)
            first_visit_date = fake.date_between(start_date='-5y', end_date='today')
            last_updated = datetime.now()

            cursor.execute("""
                INSERT INTO patients (name, father_name, gender, age, address, phone_number, medical_history, first_visit_date, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, father_name, gender, age, address, phone_number, medical_history, first_visit_date, last_updated))

            patient_id = cursor.lastrowid

            # Insert Visits for the patient
            for _ in range(random.randint(1, 5)):
                visit_date = fake.date_between(start_date='-5y', end_date='today')
                visit_number = random.randint(1, 10)
                notes = fake.sentence()
                lab_results = fake.paragraph() if random.choice([True, False]) else None
                total_amount = round(random.uniform(1000.0, 10000.0), 2)
                paid_amount = round(random.uniform(0.0, total_amount), 2)
                due_amount = total_amount - paid_amount

                cursor.execute("""
                    INSERT INTO visits (patient_id, visit_date, visit_number, notes, lab_results, total_amount, paid_amount, due_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (patient_id, visit_date, visit_number, notes, lab_results, total_amount, paid_amount, due_amount))

                visit_id = cursor.lastrowid

                # Insert Visit Services
                for service_id in range(1, random.randint(2, 6)):
                    tooth_number = random.randint(1, 32) if random.choice([True, False]) else None
                    price_charged = round(random.uniform(500.0, 5000.0), 2)
                    service_notes = fake.sentence()

                    cursor.execute("""
                        INSERT INTO visit_services (visit_id, service_id, tooth_number, price_charged, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (visit_id, service_id, tooth_number, price_charged, service_notes))

                # Insert Visit Prescriptions
                for medication_id in range(1, random.randint(2, 5)):
                    quantity = random.randint(1, 3)
                    price_charged = round(random.uniform(50.0, 500.0), 2)
                    instructions = fake.sentence()

                    cursor.execute("""
                        INSERT INTO visit_prescriptions (visit_id, medication_id, quantity, price_charged, instructions)
                        VALUES (?, ?, ?, ?, ?)
                    """, (visit_id, medication_id, quantity, price_charged, instructions))

        conn.commit()
        print("Data inserted successfully across all tables.")

    except sqlite3.Error as e:
        print(f"Database Error during data insertion: {e}")
        conn.rollback()
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
    insert_data()
