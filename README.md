# County Health Rankings API

A Flask-based REST API that provides access to county health rankings data based on ZIP codes and health measures.

## Live Demo
The API is deployed and accessible at:
https://khreed7-hw4-nqq7wbmcn-kai-reeds-projects.vercel.app/county_data

## Features

- Query county health data by ZIP code and measure name
- Support for multiple health measures including:
  - Violent crime rate
  - Unemployment
  - Children in poverty
  - Diabetic screening
  - Mammography screening
  - Preventable hospital stays
  - Uninsured
  - Sexually transmitted infections
  - Physical inactivity
  - Adult obesity
  - Premature Death
  - Daily fine particulate matter
- Results ordered by most recent year
- Pretty-printed JSON responses
- Web interface for easy testing
- Easter egg: HTTP 418 "I'm a teapot" response

## API Usage

### Endpoint
`POST /county_data`

### Request Format
```json
{
  "zip": "12345",
  "measure_name": "Children in poverty",
  "limit": 10
}
```

### Parameters
- `zip` (required): 5-digit ZIP code
- `measure_name` (required): One of the supported health measures
- `limit` (optional): Maximum number of results to return (default: 10)

### Response Format
```json
[
  {
    "state": "State Name",
    "county": "County Name",
    "state_code": "State Code",
    "county_code": "County Code",
    "year_span": "Year",
    "measure_name": "Measure Name",
    "measure_id": "ID",
    "numerator": "Numerator",
    "denominator": "Denominator",
    "raw_value": "Value",
    "confidence_interval_lower_bound": "Lower Bound",
    "confidence_interval_upper_bound": "Upper Bound",
    "data_release_year": "Release Year",
    "fipscode": "FIPS Code"
  }
]
```

## Data Sources
- County Health Rankings dataset
- ZIP Code to County mapping dataset

## Technical Details
- Built with Flask (Python web framework)
- Uses SQLite for data storage
- Deployed on Vercel
- Data loaded from CSV files into in-memory database at startup
