# message handler and error controller
class MessageHandler:
  def __init__(serial_handler, mqtt_client, timeout=3, resend=3):
    self.timeout = timeout
    self.resend = resend
    self.
  
  def sendMessageToServer(self, message):
    pass
  
  def receiveServerMessage(self, message):
    pass

  def sendMessageToMCU(self, message):
    pass

  def receiveMCUMessage(self, message):
    pass
