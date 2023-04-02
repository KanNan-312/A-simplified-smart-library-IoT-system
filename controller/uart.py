import serial.tools.list_ports
class SerialDataHandler:
  def __init__(self, processData):
    self.mess = ""
    self.ser = serial.Serial(port=self.__getPort(), baudrate=115200) if self.__getPort() != 'None' else None
    # set callback function for processing serial data
    self.processData = processData

  def isSerialConnected(self):
    return (self.ser is not None)

  def __getPort(self):
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
      port = ports[i]
      strPort = str(port)
      if "USB-SERIAL" in strPort:
        splitPort = strPort.split(" ")
        commPort = (splitPort[0])
    return commPort


  def readSerial(self, client):
    bytesToRead = self.ser.inWaiting()
    if (bytesToRead > 0):
      self.mess = self.mess + self.ser.read(bytesToRead).decode("utf-8")
      while ("#" in self.mess) and ("!" in self.mess):
        start = self.mess.find("!")
        end = self.mess.find("#")
        data = self.mess[start:end+1]
        self.processData(data)
        self.mess = self.mess[end+1:]

  def writeData(self, data):
    self.ser.write(str(data + "#").encode("utf-8"))