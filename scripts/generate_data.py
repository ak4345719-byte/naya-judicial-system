import csv
import json
import random
import os
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, "..")
CSV_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "dataset", "court_cases.csv")
JSON_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "app", "cases.json")


CASE_TYPES = ["Civil", "Criminal", "Family", "Commercial", "Constitutional", "Appellate"]
COMPLEXITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "Hearing Scheduled", "Evidence Stage", "Judgment Reserved", "Closed"]
CITIES = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad"]
COURTS = ["Supreme Court", "High Court", "District Court", "Session Court"]

NAMES_FIRST = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Diya", "Saanvi", "Ananya", "Aadhya", "Pari", "Anika", "Navya", "Angel", "Myra", "Riya"]
NAMES_LAST = ["Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Singh", "Das", "Patel", "Joshi", "Reddy", "Nair", "Iyer"]

def generate_parties():
    p1 = f"{random.choice(NAMES_FIRST)} {random.choice(NAMES_LAST)}"
    p2 = f"{random.choice(NAMES_FIRST)} {random.choice(NAMES_LAST)}"
    
    if random.random() < 0.2:
        p2 = f"State of {random.choice(CITIES)}"
    return f"{p1} vs. {p2}"

def generate_csv_data(num_rows=1000):
    """
    Generates data for ML model training (dataset/court_cases.csv)
    Columns: case_type, number_of_witnesses, advocate_count, previous_hearings, case_complexity, hearing_duration_minutes
    """
    data = []
    headers = ["case_type", "number_of_witnesses", "advocate_count", "previous_hearings", "case_complexity", "hearing_duration_minutes"]
    
    for _ in range(num_rows):
        c_type = random.choice(CASE_TYPES)
        complexity = random.choice(COMPLEXITIES)
        
        
        if complexity == "High":
            witnesses = random.randint(5, 20)
            advocates = random.randint(3, 10)
            prev_hearings = random.randint(5, 50)
            base_duration = 60
        elif complexity == "Medium":
            witnesses = random.randint(2, 8)
            advocates = random.randint(2, 5)
            prev_hearings = random.randint(2, 15)
            base_duration = 30
        else:
            witnesses = random.randint(0, 3)
            advocates = random.randint(1, 2)
            prev_hearings = random.randint(0, 5)
            base_duration = 10
            
        
        duration = base_duration + (witnesses * 2) + (advocates * 1.5) + random.randint(-5, 15)
        duration = max(5, int(duration))
        
        data.append([c_type, witnesses, advocates, prev_hearings, complexity, duration])
        
    return headers, data

def generate_json_data(num_cases=50):
    """
    Generates data for Application Dashboard (app/cases.json)
    """
    data = []
    current_year = datetime.now().year
    
    for i in range(num_cases):
        c_type = random.choice(CASE_TYPES)
        status = random.choice(STATUSES)
        
        
        year = random.randint(2018, current_year)
        seq = str(random.randint(1, 9999)).zfill(4)
        case_num = f"{c_type[:3].upper()}-{year}-{seq}"
        
        
        filing_date = datetime(year, random.randint(1, 12), random.randint(1, 28))
        if status == "Closed":
            closed_date = filing_date + timedelta(days=random.randint(30, 1000))
            closed_date_str = closed_date.strftime("%Y-%m-%d")
            hearing_date_str = None
        else:
            closed_date_str = None
            future_days = random.randint(1, 60)
            hearing_date = datetime.now() + timedelta(days=future_days)
            hearing_date_str = hearing_date.strftime("%Y-%m-%d")

        case_obj = {
            "caseNumber": case_num,
            "title": generate_parties(),
            "caseType": c_type,
            "status": status,
            "filingDate": filing_date.strftime("%Y-%m-%d"),
            "hearingDate": hearing_date_str,
            "closedDate": closed_date_str,
            "court": f"{random.choice(COURTS)}, {random.choice(CITIES)}",
            "judge": f"Hon. Justice {random.choice(NAMES_LAST)}",
            "advocates": random.randint(1, 5),
            "witnesses": random.randint(0, 10),
            "previous_hearings": random.randint(0, 20),
            "complexity": random.choice(COMPLEXITIES),
            "description": f"A {c_type.lower()} dispute involving {random.choice(['property', 'contract breach', 'family matters', 'public interest'])}."
        }
        
        
        case_obj = {k: v for k, v in case_obj.items() if v is not None}
        data.append(case_obj)
        
    return data

def main():
    print("Welcome to Naya Judicial System Data Generator")
    print("1. Generate Synthetic Data (Fast, Random)")
    print("2. Import Real High Court Data (Slower, Realistic)")
    
    choice = input("Select option (1/2): ").strip()
    
    if choice == "2":
        try:
            import import_real_data
            import_real_data.main()
        except ImportError:
            print("❌ import_real_data.py not found in scripts folder.")
        except Exception as e:
            print(f"❌ Error importing real data: {e}")
        return

    
    os.makedirs(os.path.dirname(CSV_OUTPUT_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)

    
    print(f"Generating {CSV_OUTPUT_PATH}...")
    headers, rows = generate_csv_data(1000)
    with open(CSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print("✅ CSV Generated.")

    
    print(f"Generating {JSON_OUTPUT_PATH}...")
    json_data = generate_json_data(200) 
    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print("✅ JSON Generated.")
    print("\nℹ️  To load this data into MongoDB, restart the Flask app or run 'python scripts/reset_db.py' if configured.")

if __name__ == "__main__":
    main()
