import ui, console

class Toucher(ui.View):

  seconds = 60
  running = False
  threshold = 60
  panning = False
  prev_y = 0
  start_loc = None
  
  def __init__(self, start_time, **kwargs):
    super().__init__(**kwargs)
    self.start_time = self.current_time = start_time

  def update(self):
    l = self.superview
    l.text = str(self.current_time)
    if self.current_time == 0:
      self.update_interval = 0
      self.running = False
      self.seconds = 60
      l.text_color = 'darkgrey'
      console.set_idle_timer_disabled(False)
      return
    self.seconds -= 1
    self.set_needs_display()
    if self.seconds == 0:
      self.seconds = 60
      self.current_time -= 1

  def draw(self):
    ui.set_color('black')
    path = ui.Path()
    path.line_width = 10
    insets = self.objc_instance.safeAreaInsets()
    path.move_to(0, self.height-5-insets.bottom)
    path.line_to(self.width/60*self.seconds, self.height-5-insets.bottom)
    path.stroke()

  def touch_began(self, touch):
    self.start_loc = touch.location
    self.panning = False
    self.prev_y = touch.location[1]

  def touch_moved(self, touch):
    l = self.superview
    (x,y) = touch.location
    if not self.panning:
      (px,py) = self.start_loc
      if abs(x-px)+abs(y-py) > 40:
        self.panning = True
        if self.prev_y == 0:
          self.prev_y = y
    if self.panning:
      if not self.running:
        delta_y = y - self.prev_y
        if abs(delta_y) > self.threshold:
          self.prev_y = y
          if delta_y > 0:
            self.current_time -= 1
          else:
            self.current_time += 1
          if self.current_time > 99: self.current_time = 0
          if self.current_time < 0: 
            self.current_time = self.start_time
          l.text = str(self.current_time)
          self.seconds = 60
          self.set_needs_display()

  def touch_ended(self, touch):
    l = self.superview
    if not self.panning:
      self.running = self.running == False
      if self.running:
        self.update_interval = 1
        l.text_color = 'black'
        console.set_idle_timer_disabled(True)
      else:
        self.update_interval = 0
        l.text_color = 'darkgrey'
        console.set_idle_timer_disabled(False)
    self.panning = False
    self.prev_y = 0


max_size = min(ui.get_screen_size())
timer_font_size = 1000
while timer_font_size > 1:
  w, h = ui.measure_string('99', font=('Courier', timer_font_size), alignment=ui.ALIGN_CENTER)
  if w < max_size: break
  if w/max_size > 1.2:
    timer_font_size /= 1.2
  else:
    timer_font_size -= 1
    
class TimeSelection(ui.View):
  
  default_times = (1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 75, 90)
  times_per_row = 3
  rows = 4
  cell_font = timer_font_size/(times_per_row+1)
  first_time = True

  @property 
  def masks_to_bounds(self):
    return self.pntr.layer().masksToBounds()
        
  @masks_to_bounds.setter
  def masks_to_bounds(self, val):
    self.pntr.layer().setMasksToBounds_(val)
  
  @property
  def shadow_opacity(self):
    return self.pntr.layer().shadowOpacity()
        
  @shadow_opacity.setter
  def shadow_opacity(self, val):
    self.pntr.layer().setShadowOpacity_(val)
        
  @property
  def shadow_radius(self):
    return self.pntr.layer().shadowRadius()
        
  @shadow_radius.setter
  def shadow_radius(self, val):
    self.pntr.layer().setShadowRadius_(val)
        
  @property
  def shadow_offset(self):
    return self.pntr.layer().shadowOffset()
        
  @shadow_offset.setter
  def shadow_offset(self, offset):
    self.pntr.layer().setShadowOffset_(CGSize(*offset))
            
  @property
  def shadow_color(self):
    return self.pntr.layer().shadowColor()
        
  @shadow_color.setter
  def shadow_color(self, color):
    (red, green, blue, alpha) = parse_color(color)
    objc_color = ObjCClass('UIColor').colorWithRed_green_blue_alpha_(red, green, blue, alpha).CGColor()
    
    self.pntr.layer().setShadowColor_(objc_color)
    
  def set_drop_shadow(self, color):
    self.shadow_opacity = 1
    self.shadow_offset = (5,5)
    self.shadow_color = color
    self.shadow_radius = 5  
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.times = []
    for i in range(len(self.default_times)):
      time_value = self.default_times[i]
      b = ui.Button(
        title=str(time_value), 
        tint_color='black',
        border_color='lightgrey',
        border_width=1,
        corner_radius=10,
        flex='WH')
      b.font = ('Courier', self.cell_font)
      if i % 2 == 1:
        b.tint_color = 'grey'
      self.times.append(b)
      b.action = self.go_to_timer
      self.add_subview(b)      
        
  def layout(self):
    insets = self.objc_instance.safeAreaInsets()
    w = self.width - insets.left - insets.right
    h = self.height - insets.top - insets.bottom
  
    cell_width = w/self.times_per_row
    cell_height = h/self.rows
    for i in range(len(self.default_times)):
      b = self.times[i]
      column = i % self.times_per_row
      row = int(i/self.times_per_row)
      frame = (
        insets.left + column*cell_width,
        insets.top + row*cell_height,
        cell_width,
        cell_height
      )
      b.frame = frame
      center = b.center
      b.size_to_fit()
      b.center = center
      #b.frame = b.frame.inset(10,10)
      
  def go_to_timer(self, sender):
    if self.first_time:
      self.first_time = False
    else:
      self.navigation_view.pop_view()
    first_start_time = int(sender.title)
    l = ui.Label()
    l.background_color = 'white'
    l.text_color = 'darkgrey'
    l.text = str(first_start_time)
    l.alignment = ui.ALIGN_CENTER
        
    l.font = ('Courier', timer_font_size)
    l.touch_enabled = True
    t = Toucher(start_time=int(sender.title), frame=l.bounds, flex='WH')
    l.add_subview(t)
    self.navigation_view.push_view(l)

m = TimeSelection(flex='WH', hidden='True')

n = ui.NavigationView(m, navigation_bar_hidden=False, tint_color='white')
n.objc_instance.navigationController().navigationBar().hidden = True
n.present('full_screen', hide_title_bar=True)


insets = n.objc_instance.safeAreaInsets()
#n.frame = n.frame.inset(insets.top, insets.left, insets.bottom, insets.right)

m.hidden = False
