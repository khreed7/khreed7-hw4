import unittest
from api.index import app
import json

class TestConvert(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_decimal_conversions(self):
        """Test conversions from decimal to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('42', 'decimal', 'binary', '101010'),
            ('42', 'decimal', 'octal', '52'),
            ('42', 'decimal', 'decimal', '42'),
            ('-42', 'decimal', 'hexadecimal', '-2a'),
            ('42', 'decimal', 'hexadecimal', '2a'),
            ('42', 'decimal', 'base64', 'Kg=='),
            ('0', 'decimal', 'base64', 'AA=='),
            ('-8', 'decimal', 'octal', '-10'),
            ('42', 'decimal', 'text', 'forty-two'),
            ('4294967295', 'decimal', 'hexadecimal', 'ffffffff')
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed decimal input
        malformed_cases = [
            '2a',  # hexadecimal input passed as decimal
            'abc',  # non-numeric input
            '42.5'  # floating point input
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'decimal', 'outputType': 'text'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")

    def test_text_conversions(self):
        """Test conversions from text to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('five', 'text', 'decimal', '5'),
            ('minus five', 'text', 'decimal', '-5'),
            ('negative seven', 'text', 'decimal', '-7'),
            ('seven', 'text', 'binary', '111'),
            ('ten', 'text', 'octal', '12'),
            ('ten', 'text', 'octal', '12'),
            ('forty-two', 'text', 'base64', 'Kg=='),
            ('zero', 'text', 'decimal', '0'),
            ('zero', 'text', 'base64', 'AA=='),
            ('thirty-one', 'text', 'hexadecimal', '1f'),
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed text input
        malformed_cases = [
            'cs1060',  # garbage
            '0',  # numeric input
            'fourty-two'  # misspelled
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'text', 'outputType': 'decimal'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")


    def test_broken_text_conversions(self):
        """Test broken conversions from text to decimal"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('nine hundred ninety-nine thousand nine hundred ninety-nine', 'text', 'decimal', '999999'),
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

    def test_binary_conversions(self):
        """Test conversions from binary to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('1010', 'binary', 'decimal', '10'),
            ('1010', 'binary', 'text', 'ten'),
            ('1010', 'binary', 'octal', '12'),
            ('-1010', 'binary', 'octal', '-12'),
            ('1010', 'binary', 'hexadecimal', 'a'),
            ('0', 'binary', 'base64', 'AA=='),
            ('101010', 'binary', 'base64', 'Kg=='),
            ('1010', 'binary', 'binary', '1010'),
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed text input
        malformed_cases = [
            '102',  # exceeds binary range
            'fourty-two'  # misspelled text
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'text', 'outputType': 'decimal'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")


    def test_octal_conversions(self):
        """Test conversions from octal to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('52', 'octal', 'binary', '101010'),
            ('42', 'octal', 'octal', '42'),
            ('42', 'octal', 'decimal', '34'),
            ('-42', 'octal', 'hexadecimal', '-22'),
            ('42', 'octal', 'hexadecimal', '22'),
            ('52', 'octal', 'base64', 'Kg=='),
            ('0', 'octal', 'base64', 'AA=='),
            ('-10', 'octal', 'octal', '-10'),
            ('10', 'octal', 'octal', '10'),
            ('52', 'octal', 'text', 'forty-two'),
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed text input
        malformed_cases = [
            '109',  # exceeds octal range
            'fourty-two'  # misspelled text
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'text', 'outputType': 'decimal'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")

    def test_hexadecimal_conversions(self):
        """Test conversions from hexadecimal to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('2a', 'hexadecimal', 'decimal', '42'),
            ('2a', 'hexadecimal', 'text', 'forty-two'),
            ('2a', 'hexadecimal', 'octal', '52'),
            ('-2a', 'hexadecimal', 'octal', '-52'),
            ('2a', 'hexadecimal', 'hexadecimal', '2a'),
            ('0', 'hexadecimal', 'base64', 'AA=='),
            ('2a', 'hexadecimal', 'base64', 'Kg=='),
            ('2a', 'hexadecimal', 'binary', '101010'),
            ('ffffffff', 'hexadecimal', 'decimal', '4294967295'),
        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed text input
        malformed_cases = [
            'deadbeefs',  # exceeds hexadecimal range
            'fourty-two'  # misspelled text
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'text', 'outputType': 'decimal'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")

    def test_base64_conversions(self):
        """Test conversions from base64 to various formats"""
        test_cases = [
            # input_value, input_type, output_type, expected_result
            ('AA==', 'base64', 'decimal', '0'),
            ('Kg==', 'base64', 'text', 'forty-two'),
            ('AQ==', 'base64', 'octal', '1'),
            ('Kg==', 'base64', 'hexadecimal', '2a'),
            ('Kg==', 'base64', 'base64', 'Kg=='),
            ('Kg==', 'base64', 'binary', '101010'),
            ('/////w==', 'base64', 'decimal', '4294967295'),
            ('/////w==', 'base64', 'hexadecimal', 'ffffffff'),

        ]
        
        for input_value, input_type, output_type, expected in test_cases:
            response = self.app.post('/convert',
                json={'input': input_value, 'inputType': input_type, 'outputType': output_type})
            data = json.loads(response.data)
            self.assertIsNone(data['error'])
            self.assertEqual(data['result'], expected)

        # Test malformed text input
        malformed_cases = [
            'de@dbeef',  # exceeds hexadecimal range
            'A='  # invalid input
        ]
        
        for malformed_input in malformed_cases:
            response = self.app.post('/convert',
                json={'input': malformed_input, 'inputType': 'text', 'outputType': 'decimal'})
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'], f"Expected error for input: {malformed_input}")
            self.assertIsNone(data['result'], f"Expected no result for input: {malformed_input}")

    def test_error_cases(self):
        """Test various error cases"""
        error_cases = [
            # Invalid input type
            {
                'input': '42',
                'inputType': 'invalid',
                'outputType': 'decimal'
            },
            # Invalid output type
            {
                'input': '42',
                'inputType': 'decimal',
                'outputType': 'invalid'
            },
            # Invalid text input
            {
                'input': 'invalid_number',
                'inputType': 'text',
                'outputType': 'decimal'
            },
            # Invalid binary input
            {
                'input': '102',
                'inputType': 'binary',
                'outputType': 'decimal'
            },
        ]
        
        for test_case in error_cases:
            response = self.app.post('/convert', json=test_case)
            data = json.loads(response.data)
            self.assertIsNotNone(data['error'])
            self.assertIsNone(data['result'])

if __name__ == '__main__':
    unittest.main()
