# Numeric Converter

A web-based application that converts numbers between different formats including:
- English text (e.g., "one hundred twenty-three")
- Binary
- Octal
- Decimal
- Hexadecimal
- Base64

## Vercel Setup

1. Use the green "Use this template" button in https://github.com/cs1060/cat-hw2-vercel/ to make a new repo based off of this. Be sure to use your user and not the cs1060 organization as the owner.

2. In your Vercel dashboard, use "Add New..." then select Project to "Import Github Repository."
   
3. Search or find the new repository you created, then click "Import."
   
4. Click "Deploy" at the bottom. The default settings should work. You should see the "Numeric converter" app in a preview.


## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python api/index.py
```

3. Open your web browser and navigate to `http://localhost:5000`

## Running the tests

```bash
PYTHONPATH=/Users/cat/CascadeProjects/cat-hw2-vercel python3 -m unittest api/test_convert.py -vv
```

Note: the tests don't test capital letters (they probably should). They also don't test negative numbers in base64, since without knowing the encoding (e.g. two's complement) it is undefined. The test going from text to 999999 should fail because the library has a bug.

## Usage

1. Enter your input value in the text box
2. Select the input format from the dropdown menu
3. Select the desired output format from the second dropdown menu
4. Click "Convert" to see the result

## Examples

- Convert decimal to binary: Input "42" with input type "decimal" and output type "binary"
- Convert text to decimal: Input "forty two" with input type "text" and output type "decimal"
- Convert hexadecimal to text: Input "2a" with input type "hexadecimal" and output type "text"

