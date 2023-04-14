import tkinter as tk
import random
import time

class Dashboard():
  def __init__(self):
    self.master = tk.Tk()
    self.master.title('Temperature and Humidity Dashboard')
    self.master.protocol("WM_DELETE_WINDOW", self.handler)
    self.master.geometry('600x600')
    self.master.configure(bg='white')
    self.__createWidgets()
  
  def __createWidgets(self):
    # Create temperature label
    self.temperature_label = tk.Label(self.master, text='Temperature: 22.0°C', font=('Arial', 20))
    self.temperature_label.grid(row=0, column=0, padx=20, pady=20)
    
    # Create humidity label
    self.humidity_label = tk.Label(self.master, text='Humidity: 50%', font=('Arial', 20))
    self.humidity_label.grid(row=0, column=1, padx=20, pady=20)
    
    # Create slider for fan speed
    self.fan_label = tk.Label(self.master, text='Fan Speed:', font=('Arial', 16))
    self.fan_label.grid(row=1, column=0, padx=20, pady=20)
    
    self.fan_slider = tk.Scale(self.master, from_=0, to=3, orient='horizontal', command=self.control_fan)
    
    self.fan_slider.set(0)
    self.fan_slider.grid(row=1, column=1, padx=20, pady=20)

    # Create led toggle button
    self.led_label = tk.Label(self.master, text='LED:', font=('Arial', 16))
    self.led_label.grid(row=2, column=0, padx=20, pady=20)

    self.led_slider = tk.Scale(self.master, from_=0, to=1, orient='horizontal', command=self.control_LED)
    
    self.led_slider.set(0)
    self.led_slider.grid(row=2, column=1, padx=20, pady=20)

    # Create ai label
    self.ai_label = tk.Label(self.master, text='AI Result:', font=('Arial', 16))
    self.ai_label.grid(row=3, column=0, padx=20, pady=20)

    self.ai_label = tk.Label(self.master, text='No Human', font=('Arial', 20))
    self.ai_label.grid(row=3, column=1, padx=20, pady=20)


  def add_controller(self, controller):
    self.controller = controller

  def run(self):
    self.master.mainloop()

  def control_LED(self, value):
    # control the led
    self.controller.app_control_LED(value)

  def control_fan(self, value):
    # update the fan speed to sensor
    self.controller.app_control_fan(value)

  def update_LED(self, value):
    self.led_slider.set(int(value))

  def update_fan(self, value):
    self.fan_slider.set(int(value))

  def update_AI(self, value):
    self.ai_label.config(text=value)

  def update_temperature(self, value):
    # Update the temperature label
    temperature_text = 'Temperature: {:.1f}°C'.format(float(value))
    self.temperature_label.config(text=temperature_text)
  
  def update_humidity(self, value):
    # Update the humidity label
    humidity_text = 'Humidity: {:.0f}%'.format(float(value))
    self.humidity_label.config(text=humidity_text)

  def handler(self):
    self.master.destroy()
    