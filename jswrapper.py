#coding: utf-8
import ui, json
import inheritable

class JSWrapper():
  
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
    
  def fix(self, expr):
    expr = expr.replace('"', "'")
    if expr[0] != '.':
      expr = './/' + expr
    return expr
  
  def xpath(self, expr):
    expr = self.fix(expr)
    js = f'xpath_result = document.evaluate("{expr}", elem, null, XPathResult.ANY_TYPE, null); elem = xpath_result.iterateNext();'
    return JSWrapper(self, js)
  
  def value(self, expr=None):
    return JSWrapper(self, self.generate_value_js(expr)).evaluate()
    
  def generate_value_js(self, expr=None):
    expr = self.fix(expr)
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
    self.xpath(f"input[@name='{field_name}']").set_attribute('value', value)
  
  def for_each(self, expr):
    expr = self.fix(expr)
    js = f'collected_result = {{}}; nodeset = document.evaluate("{expr}", elem, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null); n = -1; not_found = true;\n while(n++, elem = nodeset.iterateNext(), elem) {{\n not_found = false; '
    post_js = ' }; if (not_found) { collected_result = "No iterable element found"; }JSON.stringify(collected_result);\n\n'
    return JSWrapper(self, js, post_js)
    
  def map(self, **expr_mappings):
    create_dict = 'key' in expr_mappings
    js = 'mapping_result = {};'
    if create_dict:
      js += f'get_key = function() {{ { self.generate_value_js(expr_mappings.pop("key")) }; return result; }}\n js_key = get_key();'
    else:
      js += 'js_key = n;'
    for key in expr_mappings:
      expr = expr_mappings[key]
      expr = self.fix(expr)
      js += f"get_value = function() {{ { self.generate_value_js(expr) } return result; }}\n mapping_result['{key}'] = get_value();"
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
    self.url_map = {
      'about:blank': self.default 
    }
    self.delegate = self
    if autostart: self.start()
    
  def start(self):
    self.handler = self.default
    self.load_url('about:blank')
    
  def webview_did_finish_load(self, webview):
    url = self.eval_js('document.URL')
    if url.startswith(self.url_map[self.handler]):
      self.handler()
    
  def webview_did_fail_load(self, webview, error_code, error_msg):
    if error_code != -999:
      print(error_code, error_msg)
    
  def default(self):
    pass
