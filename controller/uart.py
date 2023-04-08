import serial.tools.list_ports
import time
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class SerialDataHandler:
  def __init__(self, n_reconnect, processData):
    self.mess = ""
    self.n_reconnect = n_reconnect
    # set callback function for processing serial data
    self.processData = processData

    self.port = self.__getPort()
    if self.port:
      self.ser = serial.Serial(port=self.port, baudrate=115200)

  def is_serial_connected(self):
    # check if serial is still connected
    if self.port and self.__getPort() == self.port:
      return True
    else:
      # try to reconnect
      cnt = 0
      while not self.port and cnt < self.n_reconnect:
        logging.debug("Trying to reconnect uart...")
        time.sleep(1)
        self.port = self.__getPort()
        cnt += 1
      # uart is reconnected
      if self.port:
        return True
      return False

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

  def read_serial(self, client):
    bytesToRead = self.ser.inWaiting()
    if (bytesToRead > 0):
      self.mess = self.mess + self.ser.read(bytesToRead).decode("utf-8")
      self.processData(extract_data())

  def write_data(self, data):
    self.ser.write(str(data + "#").encode("utf-8"))