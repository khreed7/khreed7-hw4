from flask import Flask, request, jsonify, render_template, g
import sqlite3
import os
import csv
import traceback
import json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # Enable pretty printing of JSON

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

def init_db():
    """Initialize the in-memory database and load data."""
    try:
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        
        # Create tables
        db.execute('''
            CREATE TABLE IF NOT EXISTS county_health_rankings (
                State TEXT,
                County TEXT,
                State_code TEXT,
                County_code TEXT,
                Year_span TEXT,
                Measure_name TEXT,
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
                default_state TEXT,
                county TEXT,
                county_state TEXT,
                state_abbreviation TEXT,
                county_code TEXT,
                zip_pop TEXT,
                zip_pop_in_county TEXT,
                n_counties TEXT,
                default_city TEXT
            )
        ''')
        
        # Load data from CSV files
        csv_dir = os.path.join(os.path.dirname(__file__), '..', 'csv_data')
        
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
        query = '''
        SELECT DISTINCT chr.* 
        FROM county_health_rankings chr
        JOIN zip_county zc ON chr.County = TRIM(REPLACE(zc.county, ' County', '')) || ' County'
            AND chr.State = zc.county_state
        WHERE chr.Measure_name = ?
            AND zc.zip = ?
        ORDER BY chr.Year_span DESC
        LIMIT ?
        '''
        rows = db.execute(query, (measure_name, zip_code, limit)).fetchall()

        # If no data is found
        if not rows:
            return jsonify({'error': f'No data found for ZIP {zip_code} and measure {measure_name}'}), 404

        # Convert results into a list of dictionaries
        column_names = [
            "state", "county", "state_code", "county_code", "year_span",
            "measure_name", "measure_id", "numerator", "denominator",
            "raw_value", "confidence_interval_lower_bound",
            "confidence_interval_upper_bound", "data_release_year",
            "fipscode"
        ]
        results = []
        for row in rows:
            results.append(dict(zip(column_names, row)))

        # Return formatted JSON response
        return app.response_class(
            response=json.dumps(results, indent=2),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        print(f"Error in county_data: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True)
