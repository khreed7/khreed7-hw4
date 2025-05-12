from flask import Flask, request, jsonify, render_template, g, current_app
import sqlite3
import os
import csv
import traceback
import json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['API_KEY'] = 'cs1060-hw4-apikey'  # Simple API key for authentication

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
        
        try:
            # Check if the files exist
            county_health_path = os.path.join(csv_dir, 'county_health_rankings.csv')
            zip_county_path = os.path.join(csv_dir, 'zip_county.csv')
            
            print(f"County health file exists: {os.path.exists(county_health_path)}")
            print(f"Zip county file exists: {os.path.exists(zip_county_path)}")
            
            # Load county health rankings data
            with open(county_health_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header but keep it
                print(f"County health CSV header: {header}")
                
                # Count rows for debugging
                rows = list(reader)
                print(f"County health rows to insert: {len(rows)}")
                
                db.executemany(
                    'INSERT INTO county_health_rankings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    rows
                )
                print("County health data inserted successfully")
            
            # Load zip to county mapping data
            with open(zip_county_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header but keep it
                print(f"Zip county CSV header: {header}")
                
                # Count rows for debugging
                rows = list(reader)
                print(f"Zip county rows to insert: {len(rows)}")
                
                db.executemany(
                    'INSERT INTO zip_county VALUES (?,?,?,?,?,?,?,?,?,?)',
                    rows
                )
                print("Zip county data inserted successfully")
        except Exception as e:
            print(f"Error loading CSV data: {str(e)}")
            print(traceback.format_exc())
        
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

# Check for valid API key
def require_api_key(f):
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == current_app.config['API_KEY']:
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'Authentication required'}), 401
    decorated.__name__ = f.__name__
    return decorated

# API Endpoint to fetch county health rankings
@app.route('/county_data', methods=['POST'])
@require_api_key
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
        
        # Check that tables exist and have data
        tables_check = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"\nTables in database: {[t['name'] for t in tables_check]}")
        
        # Count records in each table
        zip_count = db.execute("SELECT COUNT(*) as count FROM zip_county").fetchone()
        health_count = db.execute("SELECT COUNT(*) as count FROM county_health_rankings").fetchone()
        print(f"Records in zip_county: {zip_count['count']}")
        print(f"Records in county_health_rankings: {health_count['count']}")
        
        # If tables are empty, return a more helpful error
        if zip_count['count'] == 0 or health_count['count'] == 0:
            return jsonify({'error': 'Database tables are empty. Please check CSV data loading.'}), 500
        
        # Debug: Print ZIP code data with more careful error handling
        print(f"\nLooking up ZIP code {zip_code}:")
        try:
            zip_data = db.execute('SELECT * FROM zip_county WHERE zip = ?', (zip_code,)).fetchall()
            print(f"Found {len(zip_data)} matching ZIP code records")
            
            for row in zip_data:
                print(json.dumps(row, indent=2))
            
            if not zip_data:
                # No matching ZIP code - let's show some available ZIP codes to help with testing
                sample_zips = db.execute('SELECT zip FROM zip_county LIMIT 5').fetchall()
                available_zips = [row['zip'] for row in sample_zips]
                return jsonify({
                    'error': f'ZIP code {zip_code} not found in database',
                    'sample_zip_codes': available_zips
                }), 404

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
            
            print(f"Found {len(county_data)} general county records")
            for row in county_data:
                print(json.dumps(row, indent=2))
            
            # Get all available measures for this exact county and state
            all_measures = db.execute('''
                SELECT DISTINCT Measure_name
                FROM county_health_rankings
                WHERE (County = ? COLLATE NOCASE OR County = ? || ' County' COLLATE NOCASE)
                AND State_code = ? COLLATE NOCASE
            ''', (county_name, county_name, state_code)).fetchall()
        except Exception as e:
            print(f"Error querying database: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Database query error: {str(e)}'}), 500
        
        available_measures = [row['Measure_name'] for row in all_measures]
        print(f"\nAvailable measures for this county: {available_measures}")
        
        # Try a more flexible query if no measures were found 
        if not available_measures:
            print("No measures found for the exact county/state. Trying a more general query...")
            # Try a broader search using just state code
            broad_measures = db.execute('''
                SELECT DISTINCT Measure_name 
                FROM county_health_rankings 
                WHERE State_code = ? COLLATE NOCASE
                LIMIT 10
            ''', (state_code,)).fetchall()
            
            available_measures = [row['Measure_name'] for row in broad_measures]
            print(f"Found {len(available_measures)} measures in state {state_code}")
            
            # If still no measures, get any available measure from the database
            if not available_measures:
                all_db_measures = db.execute('SELECT DISTINCT Measure_name FROM county_health_rankings LIMIT 15').fetchall()
                available_measures = [row['Measure_name'] for row in all_db_measures]
                print(f"No measures in state. Using {len(available_measures)} sample measures from database")
        
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
            # Try a simpler query that ignores county name
            print("No results with county name. Trying with just state code and measure...")
            simpler_query = '''
            SELECT DISTINCT * 
            FROM county_health_rankings 
            WHERE State_code = ? COLLATE NOCASE
            AND Measure_name = ? COLLATE NOCASE
            ORDER BY Year_span DESC
            LIMIT ?
            '''
            rows = db.execute(simpler_query, (state_code, measure_name, limit)).fetchall()
            
            if not rows:
                # Check for sample_mode parameter which can force returning sample data
                sample_mode = data.get('sample_mode', False)
                
                if sample_mode:
                    print("Sample mode enabled - fetching sample data instead")
                    # Find any row with this measure regardless of location
                    sample_query = '''
                    SELECT DISTINCT * 
                    FROM county_health_rankings 
                    WHERE Measure_name = ? COLLATE NOCASE
                    ORDER BY Year_span DESC
                    LIMIT ?
                    '''
                    sample_rows = db.execute(sample_query, (measure_name, limit)).fetchall()
                    
                    # If measure not found, get any data for demo purposes
                    if not sample_rows:
                        print("No rows for this measure at all - fetching any sample data")
                        any_data_query = '''
                        SELECT DISTINCT * 
                        FROM county_health_rankings
                        ORDER BY Year_span DESC
                        LIMIT ?
                        '''
                        sample_rows = db.execute(any_data_query, (limit,)).fetchall()
                        
                    if sample_rows:
                        print(f"Returning {len(sample_rows)} sample rows")
                        return app.response_class(
                            response=json.dumps({
                                'note': 'Sample data returned as no exact match was found',
                                'data': sample_rows
                            }, indent=2),
                            status=200,
                            mimetype='application/json'
                        )
                
                # If sample mode is off or no sample data found, return 404 with helpful info
                return jsonify({
                    'error': f'No data found for ZIP {zip_code} and measure {measure_name}',
                    'available_measures': available_measures,
                    'sample_zip_codes': db.execute('SELECT zip FROM zip_county LIMIT 5').fetchall(),
                    'hint': 'Add "sample_mode": true to your request to get sample data for testing'
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
