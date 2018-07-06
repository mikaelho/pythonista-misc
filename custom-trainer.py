#coding: utf-8
from ui import *
from sound import *
from speech import *
from scripter import *

moves = [
  'Skater',
  'Pushups',
  'Slalom jumps',
  'Dips',
  'Back',
  'Jumping jacks'
]

@script
def exercise(v):
  for i in range(2):
    for move in moves:
      v.text = move
      say('Next up: ' + move +', prepare')
      breather(v)
      yield
      say('Now!')
      thirty_seconds(v)
      yield 2.0
    if i == 0:
      say('Two minute break')
      v.text = 'BREATHER'
      yield 90
      thirty_seconds(v)
      yield
  yield 2.0
  say_blocking(v, 'Ready')
  
@script
def thirty_seconds(v):
  #blip()
  yield 10
  blip()
  yield 10
  blip()
  yield 5
  for _ in range(5):
    blip()
    yield 1
  bleep()
  
@script
def breather(v):
  yield 10
  for _ in range(5):
    blip()
    yield 1
  
def blip():
  play_effect('piano:D3')
  
def bleep():
  play_effect('piano:D4')
  
@script
def say_blocking(v, text):
  say(text)
  while is_speaking(): yield

if __name__ == '__main__':
  i = Button()
  #i.image = Image('iob:ios7_pause_256')
  i.tint_color = 'grey'
  i.background_color = 'white'
  v = Label()
  v.alignment = ALIGN_CENTER
  i.add_subview(v)
  v.frame = i.bounds
  v.flex = 'WH'
  v.touch_enabled = False
  i.present('sheet')
  
  v.height = i.height/2
  v.text = 'Tap to start'
  
  exercise(v)
  ctrl = find_scripter_instance(v)
  ctrl.pause_play_all()
  paused = True
  
  def play_pause(sender):
    global paused, ctrl
    ctrl.pause_play_all()
    if paused:
      i.image = Image('iob:ios7_play_256')
      paused = False
    else:
      i.image = Image('iob:ios7_pause_256')
      paused = True
    
  i.action = play_pause
