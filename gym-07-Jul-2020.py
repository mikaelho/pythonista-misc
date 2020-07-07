#coding: utf-8

from ui import *
from anchor import *
import pygestures

import tinysync

import functools, types, datetime

dark_background = '#0e0e0e'
default_tint = '#fffade' # '#e6fbff' 
default_highlight = '#7faa6e'

def style_title(view):
  view.background_color = '#202029'
  view.text_color = default_highlight
  view.tint_color = view.text_color
  view.alignment = ALIGN_CENTER
  view.line_break_mode = LB_WORD_WRAP
  view.font = ('<System-Bold>', 18)
  if hasattr(view, 'title') and view.title is not None:
    view.title = view.title.upper()
  if hasattr(view, 'text') and view.text is not None:
    view.text = view.text.upper()
  return view
  
def style_title_transparent(view):
  style_title(view)
  view.background_color = 'transparent'
  return view
  
def style_data(view):
  view.background_color = '#202029'
  view.text_color = default_tint
  view.tint_color = default_tint
  view.alignment = ALIGN_CENTER
  view.font = ('Apple SD Gothic Neo', 32)
  view.border_color = view.background_color
  return view

def style_data_transparent(view):
  style_data(view)
  view.background_color = 'transparent'
  return view

def background_style(view):
  view.background_color = dark_background


class DaySelection(ui.View):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_color = default_highlight
    
    days = [day.title for day in exercises]
    grid = GridView(
      frame=self.bounds, flex='WH')
    for i, day in enumerate(days):
      day_button = ui.Button(title=day)
      style_title(day_button)
      
      day_button.day_index = i
      day_button.action = self.day_select
      grid.add_subview(day_button)
    self.add_subview(grid)
    
  def day_select(self, sender):
    e = ExerciseCard(
      sender.day_index, 0,
      frame=self.bounds, flex='WH',
      background_color=dark_background
    )
    self.navigation_view.push_view(e)
    

class ExerciseCard(GridView, pygestures.GestureView):
  
  def __init__(self,
  day_index, exercise_index, **kwargs):
    super().__init__(**kwargs)
    
    self.day_index = day_index
    self.exercise_index = exercise_index
    
    exercise = exercises[day_index].exercises[exercise_index]
    
    #grid = GridView(frame=self.bounds, flex='WH')
    
    title_label = style_title(Autofit_Label(
      32,
      text=exercise.title,
      number_of_lines=0))
    self.add_subview(title_label)    
    #title_label.objc_instance.setAdjustsFontSizeToFitWidth(True)
    
    iv = style_title(
      ImageView(image=ui.Image(
        'gym-images/'+exercise.image_name, 
        with_rendering_mode=ui.CONTENT_SCALE_ASPECT_FIT
      ))
      if exercise.image_name is not ''
      else ui.View()
    )
    reps = style_title(Label(text=exercise.reps))
    iv.add_subview(reps)
    reps.dock.bottom_trailing()
    self.add_subview(iv)
    
    self.add_subview(style_title(
      NotesSection('Mikael', exercise))
      if 'weight_mikael' in exercise
      else ui.View()
    )
    self.add_subview(style_title(
      NotesSection('Oskari', exercise))
      if 'weight_oskari' in exercise
      else ui.View()
    )

    self.done_mikael = Round_Button(
      image=ui.Image('iob:ios7_checkmark_empty_256'), 
      tint_color='grey',
      border_color='grey',
      border_width=1)
    self.done_mikael.action = functools.partial(self.completed, 'Mikael', exercise)
    self.add_subview(self.done_mikael)
    
    self.done_oskari = Round_Button(
      image=ui.Image('iob:ios7_checkmark_empty_256'), 
      tint_color='grey',
      border_color='grey',
      border_width=1)
    self.done_oskari.action = functools.partial(self.completed, 'Oskari', exercise)
    self.add_subview(self.done_oskari)
    
  def completed(self, name, exercise, sender):
    weight = getattr(exercise, 'weight_'+name.lower())
    title = exercise.title.replace(' ', '_')
    today = datetime.datetime.now()
    with open('gym-log', 'a', encoding='utf-8') as fp:
      fp.write(f'{today:%Y-%m-%d} {name} {title} {weight}\n')
    sender.background_color = default_highlight
    sender.border_color = default_highlight
    sender.tint_color = 'white'
    
  def on_edge_swipe_left(self, data):
    ex_index = self.exercise_index + 1
    if ex_index < len(exercises[self.day_index].exercises):
      e = ExerciseCard(
        self.day_index, ex_index,
        frame=self.bounds, flex='WH',
        background_color=dark_background
      )
    else:
      e = DaySelection()
    self.navigation_view.push_view(e)
    

class NotesSection(ui.View):
  
  def __init__(self, trainer_name, exercise, **kwargs):
    super().__init__(**kwargs)
    enable(self)
    
    self.exercise = exercise
    #exercise = exercises[day_index].exercises[exercise_index]
    #self.day_index = day_index
    #self.exercise_index = exercise_index
    self.attr = 'weight_'+trainer_name.lower()
    
    self.trainer = Label(text=trainer_name)
    style_title(self.trainer)

    self.weight = TextField(
      text=str(exercise[self.attr]),
      clear_button_mode='while_editing',
      keyboard_type=KEYBOARD_NUMBERS,
      bordered=False,
      action=self.edited)
    style_data_transparent(self.weight)

    add_subviews(self)
    
    self.trainer.dock.bottom_leading() 
    self.weight.dock.all()
    
  def edited(self, sender):
    #print(self.day_index, self.exercise_index, self.attr)
    #try:
    new_weight = sender.text
    #except:
    #exercise = exercises[self.day_index].exercises[self.exercise_index]
    #sender.text = str(self.exercise[self.attr])
    #return 
    self.exercise[self.attr] = new_weight
    #exercises[self.day_index].exercises[self.exercise_index][self.attr] = new_weight
    
    #print(exercises)
    
    
def relay(attribute_name):
  '''Property creator for pass-through properties'''
  p = property(
    lambda self:
      getattr(self.target, attribute_name),
    lambda self, value:
      setattr(self.target, attribute_name, value)
  )
  return p
    
    
class PassthruView(ui.View):
  
  def __new__(cls, *args, **kwargs):
    _, ui_cls_name = cls.__name__.split('_')
    ui_cls = getattr(ui, ui_cls_name)
    t = cls.target = ui_cls()
    for key in ui_cls.__dict__:
      if not key.startswith('_'):
        setattr(cls, key, relay(key))
    instance = super().__new__(cls, *args, **kwargs)
    instance.target = t
    t.frame = instance.bounds
    t.flex = 'WH'
    instance.add_subview(t)
    #cls.__init__(instance, *args, **kwargs)
    return instance
    
    
class Round_Button(PassthruView):
  
  background_color = relay('background_color')
  border_color = relay('border_color')
  border_width = relay('border_width')
  tint_color = relay('tint_color')
      
  def layout(self):
    self.target.width = self.target.height = min(self.width, self.height)/2
    self.target.center = self.bounds.center()
    self.target.corner_radius = self.target.width/2
    

class Autofit_Label(PassthruView):
  
  def __init__(self, font_max_size, **kwargs):
    self.font_max_size = font_max_size
    super().__init__(**kwargs)
    
  '''
  alignment = relay('alignment')
  font = relay('font')
  line_break_mode = relay('line_break_mode')
  number_of_lines = relay('number_of_lines')
  text = relay('text')
  text_color = relay('text_color')
  '''
  
  def layout(self):
    font_name, _ = self.font
    font_size = self.font_max_size

    while True:
      by_word_ok = True
      for word in self.text.split():
        w,h = ui.measure_string(
          word,
          max_width=0, 
          font=(font_name, font_size), 
        )
        if w > self.width - 16:
          by_word_ok = False
          break
      if not by_word_ok:
        font_size -= 1
        continue
      w,h = ui.measure_string(
        self.text,
        max_width=self.width, 
        font=(font_name, font_size), 
        alignment=self.alignment
      )
      if h > self.height - 16:
        font_size -= 1
        continue
      break
      
    self.font = (font_name, font_size)
    
    
if __name__ == '__main__':
  
  exercises = tinysync.track([], name='gym-program')
  
  v = View(background_color=dark_background)
  
  d = DaySelection()
  
  n = NavigationView(
    d,
    navigation_bar_hidden=False, 
    #tint_color=default_tint,
    frame=v.bounds, flex='WH')
  n.objc_instance.navigationController().navigationBar().hidden = True
  
  v.add_subview(n)
  n.dock.all(fit=Dock.SAFE)
  
  v.present(
    'full_screen',
    animated=False,
    hide_title_bar=True,
    title_bar_color='white',
    orientations=['portrait'])
