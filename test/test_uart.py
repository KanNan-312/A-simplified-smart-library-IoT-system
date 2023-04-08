import unittest
from controller import SerialDataHandler

class TestUart(unittest.TestCase):
  def test_extract_data_1(self):
    ser = SerialDataHandler(n_reconnect=3, processData=(lambda x: None))
    ser.mess = "!01:T:35.6#"
    data = ser.extract_data()
    self.assertEqual(data, "01:T:35.6")
    self.assertEqual(ser.mess, "")
  
  def test_extract_data_2(self):
    ser = SerialDataHandler(n_reconnect=3, processData=(lambda x: None))
    ser.mess = "!01:T:35.6# !02:H"
    data = ser.extract_data()
    self.assertEqual(data, "01:T:35.6")
    self.assertEqual(ser.mess, " !02:H")

  def test_extract_data_3(self):
    ser = SerialDataHandler(n_reconnect=3, processData=(lambda x: None))
    ser.mess = ":T:35!ACK# !02:H:35"
    data = ser.extract_data()
    self.assertEqual(data, "ACK")
    self.assertEqual(ser.mess, " !02:H:35")
  
if __name__ == "__main__":
  unittest.main()