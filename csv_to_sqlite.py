#!/usr/bin/env python3

import csv
import sqlite3
import sys

def csv_to_sqlite(db_name, csv_file):
    # Connect to SQLite database (create if not exists)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Read CSV file
    with open(csv_file, 'r') as f:
        csv_reader = csv.reader(f)
        
        # Get headers from first row
        headers = next(csv_reader)
        
        # Create table name from CSV filename (remove .csv extension)
        table_name = csv_file.rsplit('.', 1)[0]
        
        # Create columns string for CREATE TABLE
        columns = ', '.join([f'{header} TEXT' for header in headers])
        
        # Create table
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns})')
        
        # Create parameterized query for INSERT
        placeholders = ','.join(['?' for _ in headers])
        insert_query = f'INSERT INTO {table_name} VALUES ({placeholders})'
        
        # Insert data rows
        cursor.executemany(insert_query, csv_reader)
        
        # Commit changes and close connection
        conn.commit()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_sqlite.py <database_name> <csv_file>")
        sys.exit(1)
        
    db_name = sys.argv[1]
    csv_file = sys.argv[2]
    
    try:
        csv_to_sqlite(db_name, csv_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
