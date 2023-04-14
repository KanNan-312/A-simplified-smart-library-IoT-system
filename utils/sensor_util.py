def is_valid_sensor_value(sensor, value):
  if sensor == 'T':
    return -5.0 <= float(value) <= 70.0
  elif sensor == 'H':
    return 0 <= float(value) <= 100
  return False