# models/analysis_model.py
import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
# Assuming data_manager provides _execute_query and potentially other base functions
from database.data_manager import _execute_query # Make sure this import path is correct

# --- Helper Function ---
def _get_revenue_for_period(start_date, end_date):
    """Helper function to get total collected revenue between two dates (inclusive)."""
    query = """
        SELECT SUM(paid_amount) as total_collected
        FROM visits
        WHERE visit_date >= ? AND visit_date <= ?;
    """
    # Ensure dates are in 'YYYY-MM-DD' format string
    start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, (date, datetime)) else start_date
    end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, (date, datetime)) else end_date

    result = _execute_query(query, (start_str, end_str), fetch_one=True)
    return result['total_collected'] if result and result['total_collected'] is not None else 0

# --- KPI Functions ---
def get_revenue_today():
    """Returns total collected revenue for today."""
    today = date.today()
    return _get_revenue_for_period(today, today)

def get_revenue_this_week():
    """Returns total collected revenue from Monday of the current week until today."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) # weekday() is 0 for Monday
    return _get_revenue_for_period(start_of_week, today)

def get_revenue_this_month():
    """Returns total collected revenue from the 1st of the current month until today."""
    today = date.today()
    start_of_month = today.replace(day=1)
    return _get_revenue_for_period(start_of_month, today)

# --- Existing Analysis Functions (Keep As Is, ensure imports/calls are correct) ---

def get_patient_demographics():
    """Returns gender and age distribution of patients"""
    gender_query = "SELECT gender, COUNT(*) as count FROM patients GROUP BY gender ORDER BY count DESC"
    age_query = """
        SELECT
            CASE
                WHEN age < 18 THEN 'Under 18' WHEN age BETWEEN 18 AND 30 THEN '18-30'
                WHEN age BETWEEN 31 AND 45 THEN '31-45' WHEN age BETWEEN 46 AND 60 THEN '46-60'
                ELSE 'Over 60'
            END as age_group, COUNT(*) as count
        FROM patients GROUP BY age_group ORDER BY CASE age_group
            WHEN 'Under 18' THEN 1 WHEN '18-30' THEN 2 WHEN '31-45' THEN 3
            WHEN '46-60' THEN 4 WHEN 'Over 60' THEN 5 END
    """
    gender_data = _execute_query(gender_query, fetch_all=True)
    age_data = _execute_query(age_query, fetch_all=True)
    return {"gender": gender_data, "age": age_data}

def get_patient_visit_frequency():
    """Returns statistics about visit frequency per patient"""
    query = """
        SELECT p.patient_id, p.name, COUNT(v.visit_id) as visit_count,
               MIN(v.visit_date) as first_visit, MAX(v.visit_date) as last_visit,
               julianday(MAX(v.visit_date)) - julianday(MIN(v.visit_date)) as days_span
        FROM patients p LEFT JOIN visits v ON p.patient_id = v.patient_id
        GROUP BY p.patient_id, p.name ORDER BY visit_count DESC
    """
    data = _execute_query(query, fetch_all=True)
    today_str = date.today().strftime('%Y-%m-%d')

    # Use Pandas for vectorized calculation if data volume is large,
    # otherwise, loop is fine for typical clinic sizes.
    for entry in data:
        if entry['days_span'] and entry['days_span'] > 0 and entry['visit_count'] > 1:
            entry['avg_days_between_visits'] = round(entry['days_span'] / (entry['visit_count'] - 1))
        else:
            entry['avg_days_between_visits'] = None

        if entry['last_visit']:
             # Simpler calculation using datetime subtraction
             last_visit_date = datetime.strptime(entry['last_visit'], '%Y-%m-%d').date()
             entry['days_since_last_visit'] = (date.today() - last_visit_date).days
             # Alternative using SQL's julianday if preferred (as originally)
             # j_result = _execute_query("SELECT julianday(?) - julianday(?) as diff", (today_str, entry['last_visit']), fetch_one=True)
             # entry['days_since_last_visit'] = round(j_result['diff']) if j_result else None
        else:
            entry['days_since_last_visit'] = None
    return data


def get_inactive_patients(days=180):
    """Returns patients who haven't visited in the specified number of days"""
    cutoff_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    query = """
        SELECT p.patient_id, p.name, p.phone_number, MAX(v.visit_date) as last_visit,
               julianday(?) - julianday(MAX(v.visit_date)) as days_inactive
        FROM patients p JOIN visits v ON p.patient_id = v.patient_id
        GROUP BY p.patient_id, p.name, p.phone_number HAVING MAX(v.visit_date) < ?
        ORDER BY last_visit ASC
    """
    return _execute_query(query, (date.today().strftime('%Y-%m-%d'), cutoff_date), fetch_all=True)

def get_single_visit_patients():
    """Returns patients who have only visited once and never returned"""
    query = """
        SELECT p.patient_id, p.name, p.phone_number, v.visit_date as only_visit,
               julianday(?) - julianday(v.visit_date) as days_since_visit
        FROM patients p JOIN visits v ON p.patient_id = v.patient_id
        GROUP BY p.patient_id, p.name, p.phone_number HAVING COUNT(v.visit_id) = 1
        ORDER BY only_visit ASC
    """
    return _execute_query(query, (date.today().strftime('%Y-%m-%d'),), fetch_all=True)

def get_service_utilization():
    """Returns statistics about service usage including total revenue per service."""
    query = """
        SELECT
            s.name, COUNT(vs.visit_service_id) as usage_count,
            COALESCE(AVG(vs.price_charged), 0) as avg_price, -- Use COALESCE for services never used
            COALESCE(SUM(vs.price_charged), 0) as total_revenue
        FROM services s
        LEFT JOIN visit_services vs ON s.service_id = vs.service_id
        GROUP BY s.service_id, s.name ORDER BY usage_count DESC
    """
    return _execute_query(query, fetch_all=True)

def get_tooth_number_analysis():
    """Returns statistics about which teeth are treated most often"""
    query = """
        SELECT vs.tooth_number, COUNT(*) as treatment_count,
               GROUP_CONCAT(DISTINCT s.name) as common_treatments
        FROM visit_services vs JOIN services s ON vs.service_id = s.service_id
        WHERE vs.tooth_number IS NOT NULL GROUP BY vs.tooth_number ORDER BY treatment_count DESC
    """
    return _execute_query(query, fetch_all=True)

def get_service_trends(period='month'):
    """Returns service usage trends over time"""
    time_format = {'day': '%Y-%m-%d', 'week': '%Y-%W', 'month': '%Y-%m'}.get(period, '%Y-%m')
    query = f"""
        SELECT strftime('{time_format}', v.visit_date) as time_period, s.name as service_name,
               COUNT(vs.visit_service_id) as usage_count
        FROM visits v JOIN visit_services vs ON v.visit_id = vs.visit_id
        JOIN services s ON vs.service_id = s.service_id
        GROUP BY time_period, s.name ORDER BY time_period, usage_count DESC
    """
    return _execute_query(query, fetch_all=True)

def get_medication_utilization():
    """Returns statistics about medication usage"""
    query = """
        SELECT m.name, COUNT(vp.visit_prescription_id) as prescription_count,
               AVG(vp.quantity) as avg_quantity, AVG(vp.price_charged) as avg_price,
               SUM(vp.price_charged) as total_revenue
        FROM medications m LEFT JOIN visit_prescriptions vp ON m.medication_id = vp.medication_id
        GROUP BY m.medication_id, m.name ORDER BY prescription_count DESC
    """
    return _execute_query(query, fetch_all=True)

def get_medication_trends(period='month'):
    """Returns medication usage trends over time"""
    time_format = {'day': '%Y-%m-%d', 'week': '%Y-%W', 'month': '%Y-%m'}.get(period, '%Y-%m')
    query = f"""
        SELECT strftime('{time_format}', v.visit_date) as time_period, m.name as medication_name,
               COUNT(vp.visit_prescription_id) as usage_count
        FROM visits v JOIN visit_prescriptions vp ON v.visit_id = vp.visit_id
        JOIN medications m ON vp.medication_id = m.medication_id
        GROUP BY time_period, m.name ORDER BY time_period, usage_count DESC
    """
    return _execute_query(query, fetch_all=True)

def get_revenue_analysis(period='month'):
    """Returns revenue analysis over time (Billed vs Collected)"""
    time_format = {'day': '%Y-%m-%d', 'week': '%Y-%W', 'month': '%Y-%m'}.get(period, '%Y-%m')
    query = f"""
        SELECT
            strftime('{time_format}', visit_date) as time_period,
            SUM(total_amount) as billed_amount,
            SUM(paid_amount) as collected_amount
            -- Removed other fields not used by the current chart for clarity
            -- SUM(due_amount) as outstanding_amount,
            -- COUNT(DISTINCT visit_id) as visit_count,
            -- CASE WHEN COUNT(DISTINCT visit_id) > 0 THEN SUM(paid_amount) * 1.0 / COUNT(DISTINCT visit_id) ELSE 0 END as avg_revenue_per_visit
        FROM visits
        GROUP BY time_period ORDER BY time_period
    """
    return _execute_query(query, fetch_all=True)

def get_price_deviation_analysis():
    """Analyzes where charged prices differ from default prices for services and meds."""
    # Query adjusted to handle potential division by zero or NULLs if needed,
    # and calculate deviation correctly. Using ABS might hide under/over charging.
    services_query = """
        SELECT
            s.name, s.default_price,
            AVG(vs.price_charged) as avg_charged,
            AVG(vs.price_charged) - s.default_price as avg_deviation, -- Signed deviation
            COUNT(*) as count
        FROM services s JOIN visit_services vs ON s.service_id = vs.service_id
        WHERE s.default_price IS NOT NULL -- Only compare if default price exists
        GROUP BY s.name, s.default_price
        -- Optional: Filter only where deviation exists: HAVING avg_deviation != 0
        ORDER BY ABS(avg_deviation) DESC -- Order by magnitude of deviation
    """
    medications_query = """
        SELECT
            m.name, m.default_price,
            AVG(vp.price_charged) as avg_charged,
            AVG(vp.price_charged) - m.default_price as avg_deviation, -- Signed deviation
            COUNT(*) as count
        FROM medications m JOIN visit_prescriptions vp ON m.medication_id = vp.medication_id
        WHERE m.default_price IS NOT NULL
        GROUP BY m.name, m.default_price
        -- Optional: Filter only where deviation exists: HAVING avg_deviation != 0
        ORDER BY ABS(avg_deviation) DESC -- Order by magnitude of deviation
    """
    return {
        "services": _execute_query(services_query, fetch_all=True),
        "medications": _execute_query(medications_query, fetch_all=True)
    }

def get_clinic_load_analysis():
    """Analyzes clinic load by day of week, month, etc."""
    day_of_week_query = """
        SELECT strftime('%w', visit_date) as day_of_week,
               CASE strftime('%w', visit_date)
                   WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
                   WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
                   WHEN '6' THEN 'Saturday' END as day_name,
               COUNT(*) as visit_count, AVG(total_amount) as avg_revenue
        FROM visits GROUP BY day_of_week, day_name ORDER BY day_of_week
    """
    month_query = """
        SELECT strftime('%m', visit_date) as month_num,
               CASE strftime('%m', visit_date)
                   WHEN '01' THEN 'Jan' WHEN '02' THEN 'Feb' WHEN '03' THEN 'Mar' WHEN '04' THEN 'Apr'
                   WHEN '05' THEN 'May' WHEN '06' THEN 'Jun' WHEN '07' THEN 'Jul' WHEN '08' THEN 'Aug'
                   WHEN '09' THEN 'Sep' WHEN '10' THEN 'Oct' WHEN '11' THEN 'Nov' WHEN '12' THEN 'Dec' END as month_name,
               COUNT(*) as visit_count, AVG(total_amount) as avg_revenue
        FROM visits GROUP BY month_num, month_name ORDER BY month_num
    """
    return {
        "day_of_week": _execute_query(day_of_week_query, fetch_all=True),
        "month": _execute_query(month_query, fetch_all=True)
    }

def get_visit_trends(period='month', start_date=None, end_date=None):
    """Returns visit trends over time with optional date filtering"""
    time_format = {'day': '%Y-%m-%d', 'week': '%Y-%W', 'month': '%Y-%m'}.get(period, '%Y-%m')
    query_parts = [f"SELECT strftime('{time_format}', visit_date) as time_period, COUNT(*) as visit_count, SUM(total_amount) as total_billed, SUM(paid_amount) as total_collected, AVG(total_amount) as avg_bill_amount FROM visits"]
    params = []
    conditions = []
    if start_date: conditions.append("visit_date >= ?"); params.append(start_date)
    if end_date: conditions.append("visit_date <= ?"); params.append(end_date)
    if conditions: query_parts.append("WHERE " + " AND ".join(conditions))
    query_parts.append("GROUP BY time_period ORDER BY time_period")
    query = " ".join(query_parts)
    return _execute_query(query, tuple(params), fetch_all=True)

def get_data_quality_issues():
    """Returns various data quality issues in the database"""
    duplicate_patients_query = """
        SELECT p.* FROM patients p JOIN (
            SELECT name, phone_number, COUNT(*) as count FROM patients GROUP BY name, phone_number HAVING COUNT(*) > 1
        ) d ON p.name = d.name AND p.phone_number = d.phone_number ORDER BY p.name, p.patient_id
    """
    visits_without_items_query = """
        SELECT v.*, p.name as patient_name FROM visits v
        JOIN patients p ON v.patient_id = p.patient_id
        LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id LEFT JOIN visit_prescriptions vp ON v.visit_id = vp.visit_id
        WHERE vs.visit_service_id IS NULL AND vp.visit_prescription_id IS NULL ORDER BY v.visit_date DESC
    """
    inactive_services_used_query = """
        SELECT s.service_id, s.name, COUNT(vs.visit_service_id) as usage_count FROM services s
        JOIN visit_services vs ON s.service_id = vs.service_id WHERE s.is_active = 0
        GROUP BY s.service_id, s.name ORDER BY usage_count DESC
    """
    inactive_medications_used_query = """
        SELECT m.medication_id, m.name, COUNT(vp.visit_prescription_id) as usage_count FROM medications m
        JOIN visit_prescriptions vp ON m.medication_id = vp.medication_id WHERE m.is_active = 0
        GROUP BY m.medication_id, m.name ORDER BY usage_count DESC
    """
    return {
        "duplicate_patients": _execute_query(duplicate_patients_query, fetch_all=True),
        "visits_without_items": _execute_query(visits_without_items_query, fetch_all=True),
        "inactive_services_used": _execute_query(inactive_services_used_query, fetch_all=True),
        "inactive_medications_used": _execute_query(inactive_medications_used_query, fetch_all=True)
    }

# You can add more specific financial functions here, e.g.:
def get_revenue_by_service(limit=10):
     """Gets total collected revenue per service for top services."""
     # Note: This requires joining visits -> visit_services -> services
     # Summing price_charged from visit_services might approximate collected revenue per service,
     # but doesn't directly link to actual payments made in the visits table.
     # A more accurate approach might involve complex allocation logic if payments aren't itemized.
     # Let's use the simpler approach from get_service_utilization which sums price_charged.
     query = """
         SELECT
             s.name,
             COALESCE(SUM(vs.price_charged), 0) as total_revenue
         FROM services s
         LEFT JOIN visit_services vs ON s.service_id = vs.service_id
         GROUP BY s.service_id, s.name
         ORDER BY total_revenue DESC
         LIMIT ?
     """
     return _execute_query(query, (limit,), fetch_all=True)