from event_manager import *
import sys
import uselect
from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from aiot_rgbled import RGBLed
from aiot_lcd1602 import LCD1602
import time
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20

event_manager.reset()

# global variable
mess = ""
ack = False
resend = 2
num_resent = 0
timeout = 3

def read_terminal_input():
  spoll=uselect.poll()        # Set up an input polling object.
  spoll.register(sys.stdin, uselect.POLLIN)    # Register polling object.

  input = ''
  if spoll.poll(0):
    input = sys.stdin.read(1)

    while spoll.poll(0):
      input = input + sys.stdin.read(1)

  spoll.unregister(sys.stdin)
  return input

tiny_rgb = RGBLed(pin1.pin, 4)

aiot_lcd1602 = LCD1602()

def processData(data):
  global ack

  # gateway response ACK
  if "ACK" in data:
    ack = True
  # gateway request
  else:
    print("!ACK# ")
    lst = data.split(':')
    cmd = lst[0]
    payload = lst[-1]
    if cmd == 'L':
      if payload == '0':
        tiny_rgb.show(0, hex_to_rgb('#000000'))
      elif payload == '1':
        tiny_rgb.show(0, hex_to_rgb('#ffffff'))
    elif cmd == 'F':
      pin2.write_analog(round(translate((int(payload)), 0, 100, 0, 1023)))
    elif cmd == 'D':
      aiot_lcd1602.move_to(0, 0)
      aiot_lcd1602.putstr(payload)
    # elif cmd == 'R':
    #   if payload == '0':
    #     pin14.write_digital(0)
    #   elif payload == '1':
    #     pin14.write_digital(1)

def on_event_timer_callback_K_Q_C_m_O():
  global mess
  a = read_terminal_input()
  mess = mess + a
  while "#" in mess:
    end = mess.find("#")
    data = mess[:end]
    processData(data)
    mess = mess[end+1:]


event_manager.add_timer_event(2000, on_event_timer_callback_K_Q_C_m_O)

def sendDataToGateway(data):
  global ack, resend, num_resent, timeout
  # send data using stop and wait protocol
  print(data)
  time.sleep(timeout)
  while not ack and num_resent < resend:
    print(data)
    num_resent += 1
    time.sleep(timeout)
  
  # if not ack:
  #   print("Rejected ...")
  
  ack = False
  num_resent = 0
  
aiot_dht20 = DHT20(SoftI2C(scl=Pin(22), sda=Pin(21)))

def on_event_timer_callback_n_c_j_z_a():
  temperature = '!01:T:' + str(aiot_dht20.dht20_temperature()) + '# '
  humidity = '!02:H:' + str(aiot_dht20.dht20_humidity()) + '# '
  sendDataToGateway(temperature)
  sendDataToGateway(humidity)


event_manager.add_timer_event(30000, on_event_timer_callback_n_c_j_z_a)

if True:
  display.scroll('OK')
  aiot_lcd1602.backlight_on()

while True:
  event_manager.run()
  time.sleep_ms(1000)
