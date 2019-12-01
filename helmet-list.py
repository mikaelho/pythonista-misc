#coding: utf-8
import requests, bs4, reminders, ui, sound, console, random, json, time, clipboard
from urllib import parse
from objc_util import *
from ctypes import c_void_p
import inheritable
from jswrapper import *

from xpath import dsl as xp
from xpath.renderer import to_xpath

first = False

#logins = (
#  ('Name', 'Card_number', 'PIN'), ('...','...','...'))
from helmetids import logins as logins

class HelmetScraper(WebScraper):

  list_name = 'Kirjaston kirjat'

  def __init__(self, **kwargs):
    self.super().__init__(**kwargs)  
    self.url_map = {
      self.default: 'about:blank',
      self.login_page: 'https://luettelo.helmet.fi/iii/cas/login',
      self.loans_page: 'https://haku.helmet.fi/iii/mobile/myaccount',
      self.renew_confirmation: 'https://haku.helmet.fi/iii/mobile/myaccount',
      self.capture_list: 'https://haku.helmet.fi/iii/mobile/myaccount',
      self.logged_out: 'https://haku.helmet.fi/iii/mobile/homepage'
    }
    
  def default(self): 
    global first
    if first:
      action = 1
      first = False
    else:
      try:
        action = console.alert('Helmet', button1='Uusi lainat', button2='Skannaa kassiin', button3='Hae lainat')
      except KeyboardInterrupt:
        self.close()
        return
      
    if action == 1 or action == 3:
      db = self.get_reminder_list()
      self.checked_titles = [reminder.title for reminder in reminders.get_reminders(db, completed=True)]
      reminders.delete_calendar(db)
      self.db = self.create_reminder_list()
      
      self.handler = self.login_page
      self.action_type = 'renewing' if action == 1 else 'retrieving'
      self.person_index = 0
      self.start_per_person()
      
    if action == 2:
      start_scanning()
      self.default()
    
  def start_per_person(self):
    print('Person:', logins[self.person_index][0])
    self.handler = self.login_page
    self.load_url('https://haku.helmet.fi/iii/mobile/myaccount?lang=fin&suite=mobile')
    
  def login_page(self):
    self.set_field('code', logins[self.person_index][1])
    self.set_field('pin', logins[self.person_index][2])
    self.handler = self.loans_page
    self.by_id('fm1').submit()
      
  def loans_page(self):
    
    loans_iframe = self.by_id('accountContentIframe').frame_body()
    content = loans_iframe.html()
    #print(content)

    if 'patFuncNoEntries' in content:
      print('Ei lainoja')
      self.logout()
    else:
      print(loans_iframe.value('th[@class="patFuncTitle"]').strip())
      if self.action_type == 'renewing':
        self.handler = self.renew_confirmation
        loans_iframe.frame_window().dot('submitCheckout("requestRenewAll", "requestRenewAll");').evaluate()
      else:
        self.capture_list()
      
  def renew_confirmation(self):
    self.handler = self.capture_list
    self.by_id('accountContentIframe').frame_window().call('submitCheckout', 'renewall', 'renewall')
    
  def capture_list(self):
    loans_iframe = self.by_id('accountContentIframe').frame_body()
    
    loans = loans_iframe.for_each('tr[@class="patFuncEntry"]').map(
      barcode='td[@class="patFuncBarcode"]',
      key='span[@class="patFuncTitleMain"]',
      status='td[@class="patFuncStatus"]'
      ).evaluate_with_json()
    #print('RESULT', result)
    
    title_list = list(loans.keys())
    for title in sorted(title_list):
      r = reminders.Reminder(self.db)
      r.title = title
      r.notes = loans[title]['barcode'].strip() + ' - ' + loans[title]['status'].strip()
      if title in self.checked_titles:
        r.completed = True
      r.save()
    
    self.logout()
    
  def logout(self):
    self.handler = self.logged_out
    self.load_url('https://haku.helmet.fi:443/iii/mobile/logoutFilterRedirect?suite=mobile')
    
  def logged_out(self):
    #js = 'document.body.innerHTML'
    #print(self.eval_js(js))
    self.person_index += 1
    if self.person_index == len(logins):
      self.start()
    else:
      self.start_per_person()
  
  def get_reminder_list(self):
    all_calendars = reminders.get_all_calendars()
    for calendar in all_calendars:
      if calendar.title == self.list_name:
        return calendar
    return self.create_reminder_list()
  
  def create_reminder_list(self):
    new_calendar = reminders.Calendar()
    new_calendar.title = self.list_name
    new_calendar.save()
    return new_calendar

main_view = None

AVCaptureSession = ObjCClass('AVCaptureSession')
AVCaptureDevice = ObjCClass('AVCaptureDevice')
AVCaptureDeviceInput = ObjCClass('AVCaptureDeviceInput')
AVCaptureMetadataOutput = ObjCClass('AVCaptureMetadataOutput')
AVCaptureVideoPreviewLayer = ObjCClass('AVCaptureVideoPreviewLayer')
dispatch_get_current_queue = c.dispatch_get_current_queue
dispatch_get_current_queue.restype = c_void_p

def captureOutput_didOutputMetadataObjects_fromConnection_(_self, _cmd, _output, _metadata_objects, _conn):
  global all_books
  objects = ObjCInstance(_metadata_objects)
  for obj in objects:
    try:
      s = str(obj.stringValue())
      if s in all_books:
        sound.play_effect('digital:PowerUp7')
        main_view['label'].text = all_books[s].title
        r = all_books[s]
        r.completed = True
        r.save()
    except:
      pass
      
MetadataDelegate = create_objc_class('MetadataDelegate', methods=[captureOutput_didOutputMetadataObjects_fromConnection_], protocols=['AVCaptureMetadataOutputObjectsDelegate'])

@on_main_thread
def start_scanning():
  global main_view, all_books
  global scraper
  db = scraper.get_reminder_list()
  for r in reminders.get_reminders(db):
    code = r.notes[:r.notes.index(' ')]
    all_books[code] = r
  delegate = MetadataDelegate.new()
  main_view = ui.View(frame=(0, 0, 400, 400))
  main_view.name = 'Kirjaskanneri'
  session = AVCaptureSession.alloc().init()
  device = AVCaptureDevice.defaultDeviceWithMediaType_('vide')
  _input = AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
  if _input:
    session.addInput_(_input)
  else:
    print('Failed to create input')
    return
  output = AVCaptureMetadataOutput.alloc().init()
  queue = ObjCInstance(dispatch_get_current_queue())
  output.setMetadataObjectsDelegate_queue_(delegate, queue)
  session.addOutput_(output)
  output.setMetadataObjectTypes_(output.availableMetadataObjectTypes())
  prev_layer = AVCaptureVideoPreviewLayer.layerWithSession_(session)
  prev_layer.frame = ObjCInstance(main_view).bounds()
  prev_layer.setVideoGravity_('AVLayerVideoGravityResizeAspectFill')
  ObjCInstance(main_view).layer().addSublayer_(prev_layer)
  label = ui.Label(frame=(0, 0, 400, 30), flex='W', name='label')
  label.background_color = (0, 0, 0, 0.5)
  label.text_color = 'white'
  label.text = 'Nothing scanned yet'
  label.alignment = ui.ALIGN_CENTER
  main_view.add_subview(label)
  session.startRunning()
  main_view.present('sheet')
  main_view.wait_modal()
  session.stopRunning()
  delegate.release()
  session.release()
  output.release()

if __name__ == '__main__':
  all_books = {}
  scraper = HelmetScraper()
  #scraper.present()
