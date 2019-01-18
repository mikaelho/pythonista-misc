import ui, console, objc_util, keychain
from types import SimpleNamespace as ns

font = 'Apple SD Gothic Neo'
UIColor = objc_util.ObjCClass('UIColor')
objc_black = UIColor.darkGrayColor().CGColor()

light_theme = ns(front='black', back='white', secondary='darkgrey', shadow=objc_black)
dark_theme = ns(front='white', back='black', secondary='grey', shadow=objc_black)
blue_theme = ns(front='#1976D2', back='white', secondary='#03A9F4', shadow=objc_black)
green_theme = ns(front='#009688', back='white', secondary='#80CBC4', shadow=objc_black)
red_theme = ns(front='#E53935', back='white', secondary='#FFA726', shadow=objc_black)
cyan_dark_theme = ns(front='#4DD0E1', back='black', secondary='#00897B', shadow=objc_black)

themes = [light_theme, dark_theme, blue_theme, green_theme, red_theme, cyan_dark_theme]

try:
  current_theme_index = int(keychain.get_password('timer','timer'))
  theme = themes[current_theme_index]
except TypeError:
  current_theme_index = 0
  theme = light_theme


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
      l.text_color = theme.secondary
      console.set_idle_timer_disabled(False)
      return
    self.seconds -= 1
    self.set_needs_display()
    if self.seconds == 0:
      self.seconds = 60
      self.current_time -= 1

  def draw(self):
    ui.set_color(theme.front)
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
        l.text_color = theme.front
        console.set_idle_timer_disabled(True)
      else:
        self.update_interval = 0
        l.text_color = theme.secondary
        console.set_idle_timer_disabled(False)
    self.panning = False
    self.prev_y = 0


max_size = min(ui.get_screen_size())
timer_font_size = 1000
while timer_font_size > 1:
  w, h = ui.measure_string('OO', font=(font, timer_font_size), alignment=ui.ALIGN_CENTER)
  if w < max_size: break
  #if w/max_size > 1.2:
  timer_font_size /= 1.1
  #else:
  #  timer_font_size -= 1
    
class TimeSelection(ui.View):
  
  default_times = ('theme', 1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90)
  times_per_row = 3
  rows = 4
  cell_font = timer_font_size/(times_per_row+1)
  first_time = True
    
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
        tint_color='black',
        #tint_color='white',
        background_color='white',
        #border_color='lightgrey',
        #border_width=1,
        corner_radius=10,
        flex='WH')
      if time_value == 'theme':
        b.image = ui.Image('iob:waterdrop_32')
        b.action = self.toggle_theme
      else:
        b.title = str(time_value)
        b.action = self.go_to_timer
      #b.objc_instance.setClipsToBounds_(False)
      bl = b.objc_instance.layer()
      bl.setMasksToBounds_(False)
      bl.setShadowOpacity_(1)
      bl.setShadowRadius_(1)
      bl.setShadowOffset_(objc_util.CGSize(2, 2))
      bl.setShadowColor_(objc_black)
      
      b.font = (font, self.cell_font)
      #if i % 2 == 1:
      #  b.background_color = 'darkgrey'
      self.times.append(b)
      self.add_subview(b)     
    self.set_theme() 
     
  def toggle_theme(self, sender):
    global theme, current_theme_index, themes
    current_theme_index = (current_theme_index + 1) % len(themes)
    theme = themes[current_theme_index]
    keychain.set_password('timer', 'timer', str(current_theme_index))
    self.set_theme() 
              
  def set_theme(self):
    self.background_color = theme.back
    for b in self.times:
      b.background_color = theme.back
      b.tint_color = theme.front
      b.objc_instance.layer().setShadowColor_(theme.shadow)
        
  def layout(self):
    insets = self.objc_instance.safeAreaInsets()
    w = self.width - insets.left - insets.right
    h = self.height - insets.top - insets.bottom
  
    cell_width = w/self.times_per_row
    cell_height = h/self.rows
    #w,h = 0,0
    dim = 0
    for i in range(len(self.default_times)):
      b = self.times[i]
      b.size_to_fit()
      dim = max(dim, b.width, b.height)
      #w = max(w, b.width)
      #h = max(h, b.height)
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
      b.width = b.height = dim
      b.center = center
      #b.frame = b.frame.inset(10,10)
      
  def go_to_timer(self, sender):
    if self.first_time:
      self.first_time = False
    else:
      self.navigation_view.pop_view()
    first_start_time = int(sender.title)
    l = ui.Label()
    l.background_color = theme.back
    l.text_color = theme.secondary
    l.text = str(first_start_time)
    l.alignment = ui.ALIGN_CENTER
        
    l.font = (font, timer_font_size)
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
