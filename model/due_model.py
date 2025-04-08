# model/due_model.py

# Use absolute/relative imports based on your project structure
try:
    # Assumes 'database' and 'model' are siblings in the project root
    from database import data_manager
except ImportError:
    # Fallback if the structure is different or running directly
    # This might require adjusting sys.path if run standalone
    import sys
    from pathlib import Path
    # Add project root to path - Adjust level as needed (../..)
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    from database import data_manager

def get_due_patients_details(search_term=""):
    """
    Fetches detailed information about patients with outstanding debt.

    Args:
        search_term (str): Optional term to filter patients by ID, name, or phone.

    Returns:
        list: A list of dictionaries, each containing details of a patient with debt,
              or None if an error occurs during fetching.
              Returns an empty list if no patients match or have debt.
    """
    try:
        patients = data_manager.get_patients_with_debt(search_term)
        # data_manager._execute_query already returns [] if no results
        return patients
    except Exception as e:
        print(f"Error fetching due patient details in due_model: {e}")
        return None # Indicate an error occurred

# You could add more model-specific logic here if needed in the future,
# e.g., calculating statistics on the due amounts.

if __name__ == '__main__':
    # Example usage for testing the model function
    print("Testing due_model...")
    all_debtors = get_due_patients_details()
    if all_debtors is not None:
        print(f"Found {len(all_debtors)} patients with debt (all).")
        # print(all_debtors)
    else:
        print("Error fetching all debtors.")

    search_query = "1" # Example: search for patient ID or part of name/phone
    searched_debtors = get_due_patients_details(search_term=search_query)
    if searched_debtors is not None:
        print(f"\nFound {len(searched_debtors)} patients matching '{search_query}'.")
        # print(searched_debtors)
    else:
        print(f"Error fetching debtors matching '{search_query}'.")