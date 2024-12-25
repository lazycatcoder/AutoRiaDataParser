import sqlite3 as sq
import csv
from datetime import datetime
import os


# Path to the database
DB_PATH = r'D:\AR_data.db'

def convert_db_to_csv():
    """Converting database contents to CSV file."""
    # Get the directory and database name
    db_directory = os.path.dirname(DB_PATH)
    db_name = os.path.basename(DB_PATH).split('.')[0]
    # Generate a CSV file name in the same directory
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    csv_filename = os.path.join(db_directory, f"{db_name}_{current_time}.csv")
    
    try:
        with sq.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Get all records from the `cars` table
            cursor.execute("SELECT * FROM cars")
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Write data to CSV
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                writer.writerows(rows)
            
            print(f"Data successfully exported to file: {csv_filename}")
    except Exception as e:
        print(f"Error while exporting data: {e}")

# Launch the converter
convert_db_to_csv()