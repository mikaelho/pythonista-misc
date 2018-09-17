#coding: utf-8
import uuid, collections, urllib
import inheritable
from jswrapper import *
import styleproperties
from types import SimpleNamespace as ns

click_event = 'click'
resize_event = 'resize'

LEFT = 'left'
X = 'x'
RIGHT = 'right'
WIDTH = 'width'
CENTER = 'center'
TOP = 'top'
Y = 'y'
BOTTOM = 'bottom'
HEIGHT = 'height'
MIDDLE = 'middle'

def _prop(obj, name):
  props = {
    LEFT: type(obj).left,
    X: type(obj).x,
    RIGHT: type(obj).right,
    WIDTH: type(obj).width,
    CENTER: type(obj).center,
    TOP: type(obj).top,
    Y: type(obj).y,
    BOTTOM: type(obj).bottom,
    HEIGHT: type(obj).height,
    MIDDLE: type(obj).middle
  }
  return props[name]
  
def _get(obj, name):
  prop = _prop(obj, name)
  return prop.fget(obj)
  
def _set(obj, name, value):
  prop = _prop(obj, name)
  prop.fset(obj, value)
  
class View(AttributeWrapper, styleproperties.StyleProps):
  
  def __init__(self, parent, name=None, tint_color='black'):
    self.parent = parent
    name = name or type(self).__name__
    self.tint_color = tint_color
    self.id = str(uuid.uuid4())[-12:]
    self.children = []
    self._anchors = {}
    self._dependents = set()
    self.root = parent.root
    self.name = self.root.add_child_for(self, parent, name)
    self.margin = 5
    self.style()
      
  def _refresh_position(self):
    for prop in (TOP, LEFT, WIDTH, HEIGHT):
      value = _get(self, prop)
      # was: type(self).__dict__[prop].fget(self)
      self.js().set_style(prop, f'{value}px')
    
  def add_dependent(self, anchor):
    self.dependents.add(anchor)
    
  def style(self):
    self.background_color = 'transparent'
    #self.align_vertical = MIDDLE
    self.font = '15px Arial'
    self.font_bold = True
    self.font_small_caps = True

  def render(self):
    child_renders = ''
    for child in self.children:
      child_renders += child.render()
    return f'<div id=\'{self.id}\' style=\'position: absolute;\'> {child_renders}</div>'
    
  #Section: Event handling
    
  @property
  def on_click(self):
    return self.root.get_event_handler(self, click_event)
    
  @on_click.setter
  def on_click(self, handler):
    self.root.register_event_handler(self, click_event, handler)  
    
  #Section: Anchor helpers
    
  def _set_anchor(self, prop, value):
    if value == Refresh:
      return self._resolve_anchor(prop)
    self._anchors[prop] = value
    if type(value) is At:
      value.ref._dependents.add((self, prop))
    actual_value = self._resolve_anchor(prop)
    self.root.update_dependencies(self)
    return actual_value
    
  def _resolve_anchor(self, prop):
    anchor = self._anchors.get(prop, None)
    if anchor is None: return None
    if type(anchor) in [int, float]:
      return anchor
    else:
      return anchor.resolve()
    return None
    
  def js(self):
    return JSWrapper(self.root).by_id(self.id)

  def _getr(self, prop, prop2=None):
    value = float(self.js().abs_style(prop).strip('px'))
    if prop2:
      value2 = float(self.js().abs_style(prop2).strip('px'))
      value = value + value2/2
    return value
    
  def _setr(self, prop, value, reverse_prop=None):
    if reverse_prop and isinstance(value, At):
      value.receiver = (self, reverse_prop)
    value = self._set_anchor(prop, value)
    value = 'null' if value is None else f'{value}px'
    self.js().set_style(prop, value)

  @property
  def left(self):
    return self._getr(LEFT)
    
  @left.setter
  def left(self, value):
    self._setr(LEFT, value)
    
  x = left
    
  @property
  def top(self):
    return self._getr(TOP)
    
  @top.setter
  def top(self, value):
    self._setr(TOP, value)
    
  y = top
    
  @property
  def width(self):
    return self._getr(WIDTH)
    
  @width.setter
  def width(self, value):
    self._setr(WIDTH, value)
    
  @property
  def height(self):
    return self._getr(HEIGHT)
    
  @height.setter
  def height(self, value):
    self._setr(HEIGHT, value)
    
  @property
  def right(self):
    return self._getr(RIGHT)
    
  @right.setter
  def right(self, value):
    self._setr(RIGHT, value, reverse_prop=WIDTH)
    
  @property
  def bottom(self):
    return self._getr(BOTTOM)
    
  @bottom.setter
  def bottom(self, value):
    self._setr(BOTTOM, value, reverse_prop=HEIGHT)
    
  @property
  def center(self):
    return self._getr(LEFT, WIDTH)
    
  @center.setter
  def center(self, value):
    value = self._set_anchor(CENTER, value)
    if value is None:
      value = 'null'
    else:
      value = value - self.width/2
      value = f'{value}px'
    self.js().set_style('left', value)
    
  @property
  def middle(self):
    return self._getr(TOP, HEIGHT)

  @middle.setter
  def middle(self, value):
    value = self._set_anchor(MIDDLE, value)
    if value is None:
      value = 'null'
    else:
      value = value - self.height/2
      value = f'{value}px'
    self.js().set_style('top', value)

  @property
  def margin(self):
    return (self.margin_top, self.margin_right, self.margin_bottom, self.margin_left)
    
  @margin.setter
  def margin(self, value):
    "Insets to be applied to flexible layout values. 1-4 pixel values (or percentages?)."
    if type(value) in [int, float]:
      margins = (value,)*4
    elif type(value) in [list, tuple]:
      if len(value) == 1:
        margins = (value[0],)*4
      elif len(value) == 2:
        margins = (value[0], value[1])*2
      elif len(value) == 3:
        margins = (value[0], value[1], value[2], value[1])
      elif len(value) == 4:
        margins = value
    self.margin_top, self.margin_right, self.margin_bottom, self.margin_left = margins
    js = f'{self.margin_top}px {self.margin_right}px {self.margin_bottom}px {self.margin_left}px'
    self.js().set_style('margin', js)

  def stretch_all(self):
    pass
    
  def stretch_horizontal(self):
    pass
    
  def stretch_vertical(self):
    pass

  def dock_top(self, share=0.25):
    self.left = 0
    self.top = 0
    self.right = 0
    self.height = Height(self.parent, multiplier=share)
    
  def dock_bottom(self, share=0.25):
    self.left = 0
    self.bottom = 0
    self.right = 0
    self.height = Height(self.parent, multiplier=share)
    
  @classmethod
  def dock_left(cls):
    pass
    
  @classmethod
  def dock_right(cls):
    pass
    
  @classmethod
  def stack_below(cls, other_view):
    pass
    
  @classmethod
  def stack_above(cls, other_view):
    pass
    
  @classmethod
  def continue_right(cls, other_view):
    pass
    
  @classmethod
  def continue_left(cls, other_view):
    pass
    
    
class Refresh():
  "When used to set a property value, instead refreshes from the anchor value."
    
class Box(View):
  
  def style(self):
    super().style()
    self.shadow(0, 0, 7, 1, inset=True)
  

class Label(Box):
  
  def style(self):
    super().style()
    c = self.content = Box(self, tint_color='black')
    c.center = At(self, WIDTH, multiplier=0.5)
    c.middle = At(self, HEIGHT, multiplier=0.5)
    
  @property
  def text(self):
    return 'NOT IMPLEMENTED'
    
  @text.setter
  def text(self, value):
    #self.content.js().set_style('width', 'auto')
    #self.content.js().set_style('height', 'auto')
    self.content.js().set_content(value)
    self.content.center = At(self, WIDTH, multiplier=0.5)
    self.content.middle = At(self, HEIGHT, multiplier=0.5)
    #print(self.content.js().style('height'))


class At():
  
  from_origin = True
  
  def __init__(self, ref, prop, multiplier=None, offset=0):
    self.ref = ref
    self.prop = prop
    self.offset = offset
    self.multiplier = multiplier
    self.edge_prop = None
    self.receiver = None

  def resolve(self):
    result = _get(self.ref, self.prop)
    if not self.from_origin:
      result = _get(self.ref.parent, self.invert_prop) - result
    if self.receiver: # is inverted
      result = _get(self.receiver[0].parent, self.receiver[1]) - result
    if type(self.multiplier) is str:
      self.multiplier = float(self.multiplier.strip('%'))/100
    result *= self.multiplier or 1
    result += self.offset
    return result
    
  def from_edge(self, result):
    return _get(self.ref, self.edge_prop) - result

class Top(At):
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, TOP, multiplier, offset)
class Left(At):
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, LEFT, multiplier, offset)
class Width(At):
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, WIDTH, multiplier, offset)
class Height(At):
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, HEIGHT, multiplier, offset)

class FromEdge(At):
  from_origin = False
class Right(FromEdge):
  invert_prop = WIDTH
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, RIGHT, multiplier, offset)
class Bottom(FromEdge):
  invert_prop = HEIGHT
  def __init__(self, ref, multiplier=None, offset=0):
    super().__init__(ref, BOTTOM, multiplier, offset)

def _to_edge(view, prop, value):
  return _get(view, prop) - value
  

class Root():
  
  def __init__(self, webview):
    self.id = '----root----'
    self.name = 'Root'
    self.webview = webview
    self.root = self
    self.all_views_by_id = {
      self.id: self
    }
    self.all_views_by_name = {}
    self.children = []
    self.event_handlers = {}
    self._dependents = set()
    
  @property
  def top(self):
    return 0
    
  y = top
    
  @property
  def left(self):
    return 0
    
  x = left
    
  @property
  def width(self):
    value = int(self.webview.eval_js('window.innerWidth'))
    return value
    
  right = width
    
  @property
  def height(self):
    value = int(self.webview.eval_js('window.innerHeight'))
    return value
    
  bottom = height
  
  @property
  def center(self):
    value = self.width/2
    return value
    
  @property
  def middle(self):
    value = self.height/2
    return value
    
  def on_resize(self, view):
    print('refreshing')
    self.update_dependencies(view)
    
  def register_event_handler(self, view, event_name, handler):
    self.event_handlers[view.id+event_name] = handler
    JSWrapper(self.webview).by_id(view.id).dot(f'addEventListener("{event_name}", function(event) {{ window.location.href="{self.webview.event_prefix}{view.id}{event_name}" }})').evaluate()
    
  def register_resize_handler(self, view, handler):
    self.event_handlers[view.id+'resize'] = handler
    self.webview.eval_js(f'window.addEventListener("resize", function(event) {{ window.location.href="{self.webview.event_prefix}{view.id}resize" }})')

  def handle_event(self, url):
    id = url[:12]
    event_name = url[12:]
    view = self.all_views_by_id[id]
    handler = self.event_handlers[id+event_name]
    handler(view)
    
  def get_event_handler(self, view, event_name):
    return self.event_handlers[view.id+event_name]
    
  def remove_event_handler(self, id, event_name):
    del self.event_handlers[id+event_name]
    
  def add_child_for(self, child, parent, name):
    if child not in parent.children:
      parent.children.append(child)
    self.all_views_by_id[child.id] = child
    while name in self.all_views_by_name:
      name += '*'
    self.all_views_by_name[name] = child
    js = JSWrapper(self.webview)
    parent_elem = js.xpath('body') if parent is self else js.by_id(parent.id)
    parent_elem.append(child.render())
    return name
    
  def update_dependencies(self, changed_view):
    seen = set()
    deps_per_view = {}
    visit_queue = [changed_view]
    update_queue = []
    while visit_queue:
      view = visit_queue.pop(0)
      for dep_view, dep_prop in view._dependents:
        if (dep_view, dep_prop) in seen:
          raise RecursionError(f'Cyclical layout dependency involving {changed_view.name}{(", " + view.name) if changed_view is not view else ""} and {dep_view.name}')
        seen.add((dep_view, dep_prop))
        visit_queue.append(dep_view)
        deps_per_view.setdefault(dep_view, []).append(dep_prop)
        try:
          update_queue.remove(dep_view)
        except ValueError: pass
        update_queue.append(dep_view)
    for dep_view in update_queue:
      for dep_prop in deps_per_view[dep_view]:
        _set(dep_view, dep_prop, Refresh)
    
  def eval_js(self, js):
    return self.webview.eval_js(js)
    

class UI(inheritable.WebView):
  
  event_prefix = 'pythonista-event://'
  log_prefix = 'pythonista-log:'
  
  def __init__(self, **kwargs):
    self.super().__init__(**kwargs)
    self.delegate = self
    self.root = Root(self)
    self.scales_page_to_fit = False
    self.objc_instance.subviews()[0].subviews()[0].setScrollEnabled(False)  
    with open('main-ui.html', 'r', encoding='utf-8') as h:
      self.load_html(h.read())
    
  def webview_did_finish_load(self, webview):
    self.init(self.root)
    self.root.register_resize_handler(self.root, self.root.on_resize)

    #print(self.root.webview.eval_js(f'document.body.innerHTML'))
    
  def webview_should_start_load(self, webview, url, nav_type):
    #print(url)
    if url.startswith(self.event_prefix):
      url = url[len(self.event_prefix):]
      self.root.handle_event(url)
      return False
    if url.startswith(self.log_prefix):
      print(urllib.parse.unquote(url[len(self.log_prefix):]))
      return False
    return True
    
  def init(self, root):
    pass
    

if __name__ == '__main__':
  
  def click_handler(source):
    print()
    print('Click from:', source.name)
  
  class TestUI(UI):
    
    def init(self, root):
      v = Label(root, tint_color='blue')
      v.on_click = click_handler
      v.dock_top(.3)
      v.text = 'Testing with text that shows font formatting, contains unicode characters (åäö) and is long enough'
      
      v2 = Box(root, tint_color='red')
      v2.dock_bottom('20%')
      
      v3 = Box(root, tint_color='orange')
      v3.top = Bottom(v)
      v3.bottom = Top(v2)
      v3.left = 0
      v3.right = Width(root, 0.7)
      v3.js().set_style('margin', '5px')
      #v3.right = At(root, WIDTH)
      
      '''
      v4 = Box(root, tint_color='green')
      v4.top = At(v, BOTTOM)
      v4.height = At(root, HEIGHT, .3)
      v4.width = At(root, WIDTH, .7)
      '''

      #print('Content', self.eval_js('document.body.innerHTML'))
  
  webview = TestUI()
  webview.present('full_screen', hide_title_bar=True, hide_close_button=True)