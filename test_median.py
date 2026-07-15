import unittest
from find_median import find_median

class TestFindMedian(unittest.TestCase):
    def test_empty_list(self):
        with self.assertRaises(ValueError):
            find_median([])

    def test_single_element(self):
        self.assertEqual(find_median([5]), 5)

    def test_even_length(self):
        self.assertAlmostEqual(find_median([1, 3, 5, 7]), 4)
        self.assertAlmostEqual(find_median([-2, 0, 2, 4]), 1)

    def test_odd_length(self):
        self.assertEqual(find_median([1, 3, 5, 7, 9]), 5)

if __name__ == '__main__':
    unittest.main()