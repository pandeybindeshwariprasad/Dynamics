import unittest
from django.test import TestCase
from main.assets.helpers.calculation_parser import calculate_strings
from main.assets.helpers.file_check import check_for_file

class FakeRequest:
    def __init__(self, get=None, post=None, session=None):
        self.POST = post
        if not self.POST:
            self.POST = {}
        self.GET = get
        if not self.GET:
            self.GET = {}
        self.session = session
        if not self.session:
            self.session = {}


class CalculateStringsTest(TestCase):
    def test_calculate_strings(self):
        calculations = ['(38*26)/8', '(4+7-2)/3', '3*(4+7)', '18-1*11',
                        '63+5*5', '23+90/2-3*2']
        expected = [123.5, 3, 33, 7, 88, 62]
        output = list(map(calculate_strings, calculations))

        print(expected)
        print(output)

        self.assertEqual(expected, output)


class FileCheckTest(TestCase):
    def test_check_for_file_in_get(self):
        mock_request = FakeRequest(get={
            'file': 'sample.pdf',
            'not_file': 'not a file',
        })
        output = check_for_file(mock_request)
        self.assertEqual("sample.pdf", output)

    def test_check_for_file_in_session(self):
        mock_request = FakeRequest(session={
            'file': 'sample.pdf',
            'not_file': 'not a file',
        })
        output = check_for_file(mock_request)
        self.assertEqual("sample.pdf", output)

    def test_check_for_file_no_file(self):
        mock_request = FakeRequest(get={
            'not_a_file': 'sample.pdf',
            'not_file': 'not a file',
        })
        output = check_for_file(mock_request)
        self.assertEqual(None, output)


if __name__ == '__main__':
    unittest.main()
