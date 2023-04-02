class Counter:
  def __init__(self, n):
    self.n = n
    self.current_cnt = n
  
  def update(self):
    self.current_cnt -= 1
    if self.current_cnt <= 0:
      self.current_cnt = self.n
      return True
    return False