import unittest

from app.app import lambda_handler


class TestApp(unittest.TestCase):
    def test_lambda_handler(self):
        event = {'multiValueQueryStringParameters': {'Title': ['action romance'], 'UserId': ['500']}}
        lambda_response = lambda_handler(event, None)
        print(f'lambda_response={lambda_response}')
        self.assertEqual(True, len(lambda_response) > 0)  # add assertion here


if __name__ == '__main__':
    unittest.main()
