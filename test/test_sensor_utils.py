import unittest
from utils import is_valid_sensor_value

class TestUart(unittest.TestCase):
  def test_valid_sensor_value_1(self):
    output = is_valid_sensor_value("T", "40.5")
    self.assertEqual(output, True)

  def test_valid_sensor_value_2(self):
    output = is_valid_sensor_value("T", "90.5")
    self.assertEqual(output, False)

  def test_valid_sensor_value_3(self):
    output = is_valid_sensor_value("H", "0")
    self.assertEqual(output, True)

  def test_valid_sensor_value_4(self):
    output = is_valid_sensor_value("H", "-5")
    self.assertEqual(output, False)
  
if __name__ == "__main__":
  unittest.main()