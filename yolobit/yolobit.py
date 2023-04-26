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
resend = 2
timeout = 7

sending_temp = False
sending_humid = False
num_resent_temp = 0
num_resent_humid = 0

temp_sent = None
humid_sent = None
temp_wait = 0
humid_wait = 0

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
  global sending_temp, sending_humid
  # gateway response ACK
  if "ACK_T" in data:
    if sending_temp:
      sending_temp = False
  elif "ACK_H" in data:
    if sending_humid:
      sending_humid = False
  # gateway request
  else:
    lst = data.split(':')
    cmd = lst[0]
    payload = lst[-1]
    if cmd == 'L':
      print("!ACK_L# ")
      if payload == '0':
        tiny_rgb.show(0, hex_to_rgb('#000000'))
      elif payload == '1':
        tiny_rgb.show(0, hex_to_rgb('#ffffff'))
    elif cmd == 'F':
      print("!ACK_F# ")
      pin2.write_analog(round(translate((int(payload)), 0, 100, 0, 1023)))
    elif cmd == 'D':
      print("!ACK_D# ")
      aiot_lcd1602.clear()
      aiot_lcd1602.move_to(0, 0)
      aiot_lcd1602.putstr(payload)

def on_event_timer_callback_K_Q_C_m_O():
  global mess
  a = read_terminal_input()
  mess = mess + a
  while ('!' in mess) and ("#" in mess):
    start = mess.find('!')
    end = mess.find("#")
    data = mess[start+1:end]
    processData(data)
    mess = mess[end+1:]


event_manager.add_timer_event(1000, on_event_timer_callback_K_Q_C_m_O)

def send_temp_to_gateway(temp):
  global temp_wait, num_resent_temp, sending_temp, temp_sent
  if sending_temp:
    return
  # send data using stop and wait protocol
  print(temp)
  temp_wait = 0
  num_resent_temp = 0
  sending_temp = True
  temp_sent = temp

def send_humid_to_gateway(humid):
  global humid_wait, num_resent_humid, sending_humid, humid_sent
  if sending_humid:
    return
  # send data using stop and wait protocol
  print(humid)
  humid_wait = 0
  num_resent_humid = 0
  sending_humid = True
  humid_sent = humid
  
aiot_dht20 = DHT20(SoftI2C(scl=Pin(22), sda=Pin(21)))

def on_event_timer_callback_n_c_j_z_a():
  temperature = '!01:T:' + str(aiot_dht20.dht20_temperature()) + '# '
  humidity = '!02:H:' + str(aiot_dht20.dht20_humidity()) + '# '
  (temperature)
  send_temp_to_gateway(temperature)
  send_humid_to_gateway(humidity)


event_manager.add_timer_event(30000, on_event_timer_callback_n_c_j_z_a)

if True:
  display.scroll('OK')
  aiot_lcd1602.backlight_on()

while True:
  event_manager.run()
  # handle temperature resend
  if sending_temp:
    temp_wait += 1
    # timeout for a send
    if temp_wait == timeout:
      temp_wait = 0
      # resend the data
      if num_resent_temp < resend:
        num_resent_temp += 1
        print(temp_sent)
      # max number of resend reached, reject
      else:
        sending_temp = False
    
    # handle humidity resend
  if sending_humid:
    humid_wait += 1
    # timeout for a send
    if humid_wait == timeout:
      humid_wait = 0
      # resend the data
      if num_resent_humid < resend:
        num_resent_humid += 1
        print(humid_sent)
      # max number of resend reached, reject
      else:
        sending_humid = False

  # handle humidity resend
  time.sleep_ms(1000)