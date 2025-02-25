from flask import Flask, request, jsonify, render_template, g
import sqlite3
import os

app = Flask(__name__)

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

# Database connection helper
DATABASE_PATH = 'data.db'

def get_db():
    """Get a database connection."""
    if not hasattr(g, 'db_conn'):
        g.db_conn = sqlite3.connect(DATABASE_PATH)
        g.db_conn.row_factory = sqlite3.Row
    return g.db_conn

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at the end of the request."""
    db = g.pop('db_conn', None)
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
        SELECT DISTINCT chr.State, chr.County, chr.State_code, chr.County_code, 
               chr.Year_span, chr.Measure_name, chr.Measure_id, chr.Numerator, 
               chr.Denominator, chr.Raw_value, chr.Confidence_Interval_Lower_Bound,
               chr.Confidence_Interval_Upper_Bound, chr.Data_Release_Year,
               chr.fipscode
        FROM county_health_rankings chr
        JOIN zip_county zc ON TRIM(chr.County) = TRIM(REPLACE(zc.county, ' County', ''))
            AND TRIM(chr.State) = TRIM(zc.county_state)
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

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
