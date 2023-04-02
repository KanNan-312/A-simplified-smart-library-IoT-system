import unittest
from utils import *


class TestUnit(unittest.TestCase):
  def test_counter_1(self):
    mock_counter = Counter(15)
    self.assertEqual(mock_counter.update(), False)
  
  def test_counter_2(self):
    mock_counter = Counter(1)
    self.assertEqual(mock_counter.update(), True)

if __name__ == "__main__":
  unittest.main()
