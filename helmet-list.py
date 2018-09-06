#coding: utf-8
import requests, bs4, reminders, ui, sound, console, random, json, time
from urllib import parse
from objc_util import *
from ctypes import c_void_p
import inheritable

from xpath import dsl as xp
from xpath.renderer import to_xpath

#logins = (
#  ('Name', 'Card_number', 'PIN'), ('...','...','...'))
from helmetids import logins as logins

class JSWrapper():
  
  #callback_protocol = 'scraper-callback-'+str(random.randint(10000, 100000))
  
  def __init__(self, prev, to_add_js, post=''):
    if hasattr(prev, 'target_webview'):
      self.target_webview = prev.target_webview
      prev_js = prev.js
      post_js = prev.post_js
    else:
      self.target_webview = prev
      prev_js = 'elem = document;'
      post_js = ''
    self.post_js = post
    self.js = prev_js + ' ' + to_add_js + post_js
  
  def alert(self, msg=None):
    return JSWrapper(self, f'alert("{(msg + ": ") if msg else ""}" + elem);')
    
  def debug(self, msg=None):
    msg = msg + ': ' if msg else ''
    print(msg + self.js)
    return self
  
  def xpath(self, expr):
    expr = expr.replace('"', "'")
    js = f'xpath_result = document.evaluate("{expr}", elem, null, XPathResult.ANY_TYPE, null); elem = xpath_result.iterateNext();'
    return JSWrapper(self, js)
  
  def value(self, expr=None):
    return JSWrapper(self, self.generate_value_js(expr)).evaluate()
    
  def generate_value_js(self, expr=None):
    expr = expr.replace('"', "'")
    pre_js = 'value_elem = ' + ('elem; ' if not expr else f'document.evaluate("{expr}", elem, null, XPathResult.ANY_TYPE, null).iterateNext(); ')
    js = pre_js + f'result = "Element not found"; if (value_elem) {{ xpath_result = document.evaluate("string()", value_elem, null, XPathResult.ANY_TYPE, null); if (xpath_result) {{ result = xpath_result.stringValue; }}; }}; result;'
    return js
    
  
  def by_id(self, id):
    return JSWrapper(self, f'elem = document.getElementById("{id}");')
    
  def by_name(self, name):
    return JSWrapper(self, f'elem = document.getElementsByName("{name}")[0];')
  
  def set_attribute(self, attr_name, value):
    value = str(value)
    JSWrapper(self, f'elem.setAttribute("{attr_name}", "{value}")').evaluate()
  
  def set_field(self, field_name, value):
    self.xpath(f"//input[@name='{field_name}']").set_attribute('value', value)
  
  def for_each(self, expr):
    expr = expr.replace('"', "'")
    js = f'collected_result = {{}}; nodeset = document.evaluate("{expr}", elem, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null); n = -1; not_found = true;\n while(n++, elem = nodeset.iterateNext(), elem) {{\n not_found = false; '
    post_js = ' }; if (not_found) { collected_result = "No iterable element found"; }JSON.stringify(collected_result);\n\n'
    return JSWrapper(self, js, post_js)
    
  def dummy(self, **expr_mappings):
    js = 'collected_result[n]="blaa";'
    return JSWrapper(self, js)
    
  def map(self, **expr_mappings):
    create_dict = 'key' in expr_mappings
    js = 'mapping_result = {};'
    if create_dict:
      js += f'get_key = function() {{ { self.generate_value_js(expr_mappings.pop("key")) }; return result; }}\n js_key = get_key();'
    else:
      js += 'js_key = n;'
    for key in expr_mappings:
      js += f"get_value = function() {{ { self.generate_value_js(expr_mappings[key]) } return result; }}\n mapping_result['{key}'] = get_value();"
    js += 'collected_result[js_key] = mapping_result;'
    return JSWrapper(self, js)
  
  def set_string_value(self, value):
    return JSWrapper(self, f'elem.value = "{value}";')
    
  def dot(self, dot_attributes):
    return JSWrapper(self, f'elem = elem.{dot_attributes};')
    
  def click(self):
    return JSWrapper(self, 'elem.click();').evaluate()
    
  def html(self):
    return JSWrapper(self, 'elem.innerHTML;').evaluate()
    
  def frame_body(self):
    return self.dot('contentDocument.body')
    
  def frame_window(self):
    return self.dot('contentWindow')
    
  def submit(self):
    "Submit selected element, or the first form in the document if nothing selected"
    if type(self) is not JSWrapper:
      self = self.xpath('//form[1]')
    JSWrapper(self, f'elem.submit();').evaluate()
    
  #TODO: Still valuable to be able to separately set by name?
  def set_value_by_name(self, name, value):
    self.by_name(name).set_string_value(value).evaluate()
    
  #TODO: Better ideas for calling JS functions?
  def call(self, func_name, *args):
    js_args = [f'"{item}"' if type(item) == str else str(item) for item in args]
    JSWrapper(self, f'elem.{func_name}({js_args})').evaluate()
    
  def evaluate(self):
    return self.target_webview.eval_js(self.js)
    
  def evaluate_with_json(self):
    return json.loads(self.evaluate())


class WebScraper(inheritable.WebView, JSWrapper):
  
  def __init__(self, autostart=True, **kwargs):
    self.super().__init__(**kwargs)
    self.delegate = self
    if autostart: self.start()
    
  def start(self):
    self.handler = self.default
    self.load_url('about:blank')
  
  '''  
  def webview_should_start_load(self, webview, url, nav_type):
    print(url)
    return True
    if url.startswith(self.callback_protocol + '://'):
      args = dict(parse.parse_qsl(parse.urlsplit(url).query))
      func_name = args.pop('func', None)
      if func_name:
        self.__dict__[func_name](**args)
      return False
    else:
      return True
  '''
    
  def webview_did_finish_load(self, webview):
    url = self.eval_js('document.URL')
    #print(url)
    if url.startswith(self.url_map[self.handler]):
      #print(f'Handler: {self.handler.__name__}')
      self.handler()
    
    
  def webview_did_fail_load(self, webview, error_code, error_msg):
    if error_code != -999:
      print(error_code, error_msg)
    
  def default(self):
    pass
    

class HelmetScraper(WebScraper):
    
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
  
    #self.for_each('blaa1').map('daa2').map('laa3').debug('Chaining')
  
    #js = 'dv= {1;2;3}; dv'
    #print('Result:', self.eval_js(js))
    
    try:
      action = console.alert('Helmet', button1='Uusi lainat', button2='Skannaa kassiin', button3='Hae lainat')
    except KeyboardInterrupt:
      self.close()
      return
      
    
    if action == 1 or action == 3:
      self.handler = self.login_page
      self.action_type = 'renewing' if action == 1 else 'retrieving'
      self.person_index = 0
      self.start_per_person()
    
    if action == 'fiobar':
      for (name, card_number, pin) in logins:
        print('Requesting books for', name)
        get_books(card_number, pin, all_books)
        print('Total books:', len(all_books))
    
      update_reminders(all_books)
      
    if action == 2:
      start_scanning()
    
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
      print(loans_iframe.value('.//th[@class="patFuncTitle"]').strip())
      if self.action_type == 'renewing':
        self.handler = self.renew_confirmation
        #loans_iframe.frame_window().dot('submitCheckout("renewall", "renewall");').evaluate()
        loans_iframe.frame_window().dot('submitCheckout("requestRenewAll", "requestRenewAll");').evaluate()
      else:
        self.capture_list()
      
  def renew_confirmation(self):
    self.handler = self.capture_list
    self.by_id('accountContentIframe').frame_window().call('submitCheckout', 'renewall', 'renewall')
    
  def capture_list(self):
    loans_iframe = self.by_id('accountContentIframe').frame_body()
    
    result = loans_iframe.for_each('//tr[@class="patFuncEntry"]').map(
      key='.//td[@class="patFuncBarcode"]',
      title='.//span[@class="patFuncTitleMain"]',
      status='.//td[@class="patFuncStatus"]'
      ).evaluate_with_json()
    #print('RESULT', result)
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
  
  scraper = HelmetScraper()
  #scraper.present()
  
  '''
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
  '''

