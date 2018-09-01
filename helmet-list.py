#coding: utf-8
import requests, bs4, reminders, ui, sound, console
from objc_util import *
from ctypes import c_void_p
import inheritable

#logins = (
#  ('Name', 'Card_number', 'PIN'), ('...','...','...'))
from helmetids import logins as logins

class BackgroundBrowser(inheritable.WebView):
  
  def __init__(self, **kwargs):
    self.super().__init__(**kwargs)
    self.delegate = self
    self.states = ['initial', 'first', 'loggedin', 'listed', 'renew', 'confirm', 'logout', 'initial']
    self.state = 'initial'
    
  def webview_did_finish_load(self, webview):
    print(self.state)    
    if self.state == 'first':
      js = f'document.getElementsByName("code")[0].value = "{logins[1][1]}"; document.getElementsByName("pin")[0].value = "{logins[1][2]}"; document.getElementById("fm1").submit();'
      self.state = 'loggedin'
      self.eval_js(js)
    elif self.state == 'loggedin':
      content = self.eval_js('ifr = document.getElementById("accountContentIframe").contentWindow; ifr.submitCheckout( "requestRenewAll", "requestRenewAll" );')
      self.state = 'renew1'
    elif self.state == 'renew1':
      #print(self.eval_js('document.getElementById("accountContentIframe").contentDocument.body.innerHTML'))
      content = self.eval_js('ifr = document.getElementById("accountContentIframe").contentWindow; ifr.submitCheckout( "renewall", "renewall_" );')
      self.state = 'logout'
    elif self.state == 'logout':
      self.load_url('https://haku.helmet.fi:443/iii/mobile/logoutFilterRedirect?suite=mobile')
      self.state = 'loggedout'
    
  def webview_did_fail_load(self, webview, error_code, error_msg):
    print(error_code, error_msg)
    self.state = 'error'
    
browsery = BackgroundBrowser()

def renew_loans():
  global browsery
  browsery.present()
  browsery.state = 'first'
  browsery.load_url('https://haku.helmet.fi/iii/mobile/myaccount?lang=fin&suite=mobile')

list_name = 'Kirjaston kirjat'

all_books = {}

def get_books(card_number, pin, book_list):
  s = requests.session()
  page = s.get('https://haku.helmet.fi/iii/mobile/myaccount?lang=fin&suite=mobile')

  soup = bs4.BeautifulSoup(page.text, 'html5lib')
  print(page.text)
  action_url = 'https://luettelo.helmet.fi' + soup.find(id='fm1').get('action')

  inputs = soup.find_all('input')
  for field in inputs:
    if field.get('name') == 'lt':
      lt = field.get('value')
      
  login_data = {
    'code': card_number,
    'pin': pin,
    'lt': lt,
    '_eventId': 'submit'
  }

  next_page = s.post(action_url, data=login_data)
  
  soup = bs4.BeautifulSoup(next_page.text, 'html5lib')
  content_url = soup.find(id='accountContentIframe').get('src')
  
  content_page = s.get(content_url)
  #print('_'*100)
  #print(content_page.text)
  soup = bs4.BeautifulSoup(content_page.text, 'html5lib')
  
  entry_class = 'patFuncEntry'
  title_class = 'patFuncTitleMain'
  barcode_class = 'patFuncBarcode'
  expiry_class = 'patFuncStatus'
  renews_class = 'patFuncRenewCount'
  
  for entry in soup.find_all('tr', class_=entry_class):
    title = entry.find(class_=title_class).string.strip()
    barcode = entry.find(class_=barcode_class).string.strip()
    expiry = entry.find(class_=expiry_class).get_text()
    #renews = entry.find(class_=renews_class).string
    book_list[barcode] = { 'title': title }
  
def update_reminders(book_list):
  db = get_reminder_list()
  checked_titles = [reminder.title for reminder in reminders.get_reminders(db, completed=True)]
  reminders.delete_calendar(db)
  db = create_reminder_list()
  title_list = (book['title'] for book in book_list.values())
  lookup = {book_list[barcode]['title']: barcode for barcode in book_list.keys()}
  for title in sorted(title_list):
    r = reminders.Reminder(db)
    r.title = title
    if title in checked_titles:
      r.completed = True
    r.save()
    book_list[lookup[title]]['reminder'] = r

def get_reminder_list():
  all_calendars = reminders.get_all_calendars()
  for calendar in all_calendars:
    if calendar.title == list_name:
      return calendar
  return create_reminder_list()

def create_reminder_list():
  new_calendar = reminders.Calendar()
  new_calendar.title = list_name
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
  db = get_reminder_list()
  objects = ObjCInstance(_metadata_objects)
  for obj in objects:
    try:
      s = str(obj.stringValue())
      if s in all_books:
        sound.play_effect('digital:PowerUp7')
        main_view['label'].text = all_books[s]['title']
        r = all_books[s]['reminder']
        r.completed = True
        r.save()
    except:
      pass
      
MetadataDelegate = create_objc_class('MetadataDelegate', methods=[captureOutput_didOutputMetadataObjects_fromConnection_], protocols=['AVCaptureMetadataOutputObjectsDelegate'])

@on_main_thread
def start_scanning():
  global main_view
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
  
  while True:
    
    action = console.alert('Helmet', button1='Uusi lainat', button2='Hae ja skannaa', button3='Hae lainat')
    if not action: break
    
    if action == 1:
      renew_loans()
    
    if action != 1:
      for (name, card_number, pin) in logins:
        print('Requesting books for', name)
        get_books(card_number, pin, all_books)
        print('Total books:', len(all_books))
    
      update_reminders(all_books)
      
    if action == 2:
      start_scanning()
  

