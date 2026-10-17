import unittest
from reader import sample


class ReaderTest(unittest.TestCase):
    def test_compatibility_fixture(self):
        self.assertEqual({"format": 2, "entries": []}, sample())
