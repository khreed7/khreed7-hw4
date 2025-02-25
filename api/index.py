from flask import Flask, request, jsonify, render_template, g
import sqlite3
import os
import csv
import traceback
import json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Allowed measures
ALLOWED_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter"
}

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def init_db():
    """Initialize the in-memory database and load data."""
    try:
        db = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = dict_factory
        
        # Create tables with case-insensitive collation
        db.execute('''
            CREATE TABLE IF NOT EXISTS county_health_rankings (
                State TEXT COLLATE NOCASE,
                County TEXT COLLATE NOCASE,
                State_code TEXT COLLATE NOCASE,
                County_code TEXT,
                Year_span TEXT,
                Measure_name TEXT COLLATE NOCASE,
                Measure_id TEXT,
                Numerator TEXT,
                Denominator TEXT,
                Raw_value TEXT,
                Confidence_Interval_Lower_Bound TEXT,
                Confidence_Interval_Upper_Bound TEXT,
                Data_Release_Year TEXT,
                fipscode TEXT
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS zip_county (
                zip TEXT,
                default_state TEXT COLLATE NOCASE,
                county TEXT COLLATE NOCASE,
                county_state TEXT COLLATE NOCASE,
                state_abbreviation TEXT COLLATE NOCASE,
                county_code TEXT,
                zip_pop TEXT,
                zip_pop_in_county TEXT,
                n_counties TEXT,
                default_city TEXT
            )
        ''')
        
        # Load data from CSV files
        csv_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data')
        print(f"Loading data from {csv_dir}")
        
        with open(os.path.join(csv_dir, 'county_health_rankings.csv'), 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            db.executemany(
                'INSERT INTO county_health_rankings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                reader
            )
        
        with open(os.path.join(csv_dir, 'zip_county.csv'), 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            db.executemany(
                'INSERT INTO zip_county VALUES (?,?,?,?,?,?,?,?,?,?)',
                reader
            )
        
        db.commit()
        
        # Debug: Print some sample data
        print("\nSample data from zip_county:")
        cursor = db.execute('SELECT * FROM zip_county LIMIT 5')
        for row in cursor:
            print(json.dumps(row, indent=2))
            
        print("\nSample data from county_health_rankings:")
        cursor = db.execute('SELECT * FROM county_health_rankings LIMIT 5')
        for row in cursor:
            print(json.dumps(row, indent=2))
            
        return db
        
    except Exception as e:
        print(f"Error in init_db: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise

def get_db():
    """Get database connection."""
    if not hasattr(g, 'db'):
        g.db = init_db()
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Page for manual county data entry
@app.route('/county_data', methods=['GET'])
def county_data_page():
    return render_template('index.html')

# API Endpoint to fetch county health rankings
@app.route('/county_data', methods=['POST'])
def county_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Easter egg for teapot status
        if data.get('coffee') == 'teapot':
            return "I'm a teapot", 418

        # Extract parameters
        zip_code = data.get('zip')
        measure_name = data.get('measure_name')
        limit = data.get('limit', 10)  # Default to 10

        # Validate inputs
        if not zip_code or not measure_name:
            return jsonify({'error': 'Missing required parameters'}), 400

        if not (isinstance(zip_code, str) and zip_code.isdigit() and len(zip_code) == 5):
            return jsonify({'error': 'Invalid ZIP code format'}), 400

        if measure_name not in ALLOWED_MEASURES:
            return jsonify({'error': 'Invalid measure_name'}), 400

        if not isinstance(limit, int) or limit < 1:
            return jsonify({'error': 'Invalid limit parameter'}), 400

        # Execute SQL query
        db = get_db()
        
        # Debug: Print ZIP code data
        print(f"\nLooking up ZIP code {zip_code}:")
        zip_data = db.execute('SELECT * FROM zip_county WHERE zip = ?', (zip_code,)).fetchall()
        for row in zip_data:
            print(json.dumps(row, indent=2))
        
        if not zip_data:
            return jsonify({'error': f'ZIP code {zip_code} not found in database'}), 404

        # Get county and state info
        county_name = zip_data[0]['county'].replace(' County', '')
        state_name = zip_data[0]['county_state']
        state_code = zip_data[0]['state_abbreviation']
        
        print(f"\nLooking for data with:")
        print(f"County: {county_name} or {county_name} County")
        print(f"State: {state_name} ({state_code})")
        
        # Debug: Show all records for this exact county and state
        print("\nAll records for this exact county and state:")
        county_data = db.execute('''
            SELECT DISTINCT *
            FROM county_health_rankings
            WHERE (County = ? COLLATE NOCASE OR County = ? || ' County' COLLATE NOCASE)
            AND State_code = ? COLLATE NOCASE
            LIMIT 5
        ''', (county_name, county_name, state_code)).fetchall()
        
        for row in county_data:
            print(json.dumps(row, indent=2))
        
        # Get all available measures for this exact county and state
        all_measures = db.execute('''
            SELECT DISTINCT Measure_name
            FROM county_health_rankings
            WHERE (County = ? COLLATE NOCASE OR County = ? || ' County' COLLATE NOCASE)
            AND State_code = ? COLLATE NOCASE
        ''', (county_name, county_name, state_code)).fetchall()
        
        available_measures = [row['Measure_name'] for row in all_measures]
        print(f"\nAvailable measures for this county: {available_measures}")
        
        # Modified query to be more explicit about state matching and case-insensitive
        query = '''
        SELECT DISTINCT chr.* 
        FROM county_health_rankings chr
        WHERE (chr.County = ? COLLATE NOCASE OR chr.County = ? || ' County' COLLATE NOCASE)
        AND chr.State_code = ? COLLATE NOCASE
        AND chr.Measure_name = ? COLLATE NOCASE
        ORDER BY chr.Year_span DESC
        LIMIT ?
        '''
        
        print(f"\nExecuting query for measure '{measure_name}'")
        rows = db.execute(query, (county_name, county_name, state_code, measure_name, limit)).fetchall()
        
        # If no data is found
        if not rows:
            return jsonify({
                'error': f'No data found for ZIP {zip_code} and measure {measure_name}',
                'available_measures': available_measures
            }), 404

        # Return formatted JSON response
        return app.response_class(
            response=json.dumps(rows, indent=2),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        print(f"Error in county_data: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
