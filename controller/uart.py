import serial.tools.list_ports
import time
import logging

class SerialDataHandler:
  def __init__(self, processData):
    self.mess = ""
    # set callback function for processing serial data
    self.processData = processData

    self.port = self.__getPort()
    if self.port:
      self.ser = serial.Serial(port=self.port, baudrate=115200)

  def is_serial_connected(self):
    # check if serial is still connected and try to reconnect
    port = self.__getPort()
    if not port:
      self.port = None
      return False
    else:
      if self.port != self.__getPort():
        # print('je')
        self.port = self.__getPort()
        self.ser = serial.Serial(port=self.port, baudrate=115200)
      return True


  def __getPort(self):
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = None
    for i in range(0, N):
      port = ports[i]
      strPort = str(port)
      if "USB-SERIAL CH340" in strPort:
        splitPort = strPort.split(" ")
        commPort = (splitPort[0])
    return commPort

  def extract_data(self):
    while ("#" in self.mess) and ("!" in self.mess):
      start = self.mess.find("!")
      end = self.mess.find("#")
      data = self.mess[start:end+1]
      self.mess = self.mess[end+1:]
      data = data.replace("!", "")
      data = data.replace("#", "")
      return data

  def read_serial(self):
    bytesToRead = self.ser.inWaiting()
    if (bytesToRead > 0):
      self.mess = self.mess + self.ser.read(bytesToRead).decode("utf-8")
      print(self.mess)
      data = self.extract_data()
      if data:
        self.processData(data)

  def write_data(self, data):
    try:
      self.ser.write(str("!" + data + "#").encode("utf-8"))
    except:
      logging.info("Detect uart disconnection...")
      self.controller.uart_connected = False


if __name__ == '__main__':
  ser = SerialDataHandler(lambda x: None)
  print(ser.port)
  ser.write_data("jaja")
  ser.read_serial()