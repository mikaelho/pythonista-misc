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
    self.default_left = 0
    self.default_top = 0
    self.default_width = Flex(self, WIDTH)
    self.default_height = Flex(self, HEIGHT)
    self.default_layout_offset = 0
    self.children = []
    self._anchors = {}
    self._dependents = set()
    self.root = parent.root
    self.name = self.root.add_child_for(self, parent, name)
    self.x = 0
    self.y = 0
    self.width = At(parent, WIDTH)
    self.height = At(parent, HEIGHT)
    self.inset = 0
    self.style()
    self._refresh_position()     
      
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
    self._anchors[prop] = value
    if type(value) is At:
      value.ref._dependents.add((self, prop))
    actual_value = self._resolve_anchor(prop)
    for dependent, dep_prop in self._dependents:
      dependent._refresh_anchor(dep_prop)
    return actual_value
    
  def _resolve_anchor(self, prop):
    anchor = self._anchors.get(prop, None)
    if anchor is None: return None
    if type(anchor) in [int, float]:
      return anchor
    else:
      return anchor.resolve()
    return None
      
  def _refresh_anchor(self, prop):
    anchor = self._anchors[prop]
    _set(self, prop, anchor)
    # was: type(self).__dict__[prop].fset(self, anchor)
    # was: prop.fset(self, anchor)
    
  def _resolve_horizontal(self, horizontal=True):
    if horizontal:
      left = self._resolve_anchor(LEFT)
      right = self._resolve_anchor(RIGHT)
      width = self._resolve_anchor(WIDTH)
      center = self._resolve_anchor(CENTER)
    else:
      left = self._resolve_anchor(TOP)
      right = self._resolve_anchor(BOTTOM)
      width = self._resolve_anchor(HEIGHT)
      center = self._resolve_anchor(MIDDLE)
    if left is None:
      if right is not None and center is not None:
        left = right - (right-center)
        # check center
      elif width is not None and center is not None:
        left = center - width/2
        # check right
      elif right is not None and width is not None:
        left = right - width
      elif right is not None or center is not None:
        width = self.default_width
        if right is not None:
          left = right - width
        elif center is not None:
          left = center - width/2
      else:
        left = self.default_left
    if width is None:
      if right is not None:
        width = right - left
        # check center
      elif center is not None:
        width = (center - left)*2
      else:
        width = self.default_width
    if right is None:
      right = left + width
      # check center
    if center is None:
      center = (left + right)/2
    if horizontal:
      return ns(left=left, right=right, center=center, width=width)
    else:
      return ns(top=left, bottom=right, middle=center, height=width)
    
  def _resolve_vertical(self):
    return self._resolve_horizontal(horizontal=False)
    
  def js(self):
    return JSWrapper(self.root).by_id(self.id)

  @property
  def left(self):
    "left"
    value = self._resolve_anchor(LEFT)
    if value is None:
      value = self._resolve_horizontal().left
    return value
    
  @left.setter
  def left(self, value):
    value = self._set_anchor(LEFT, value)
    self.js().set_style('left', f'{value}px')
    
  x = left
    
  @property
  def top(self):
    "top"
    value = self._resolve_anchor(TOP)
    if value is None:
      value = self._resolve_vertical().top
    return value
    
  @top.setter
  def top(self, value):
    value = self._set_anchor(TOP, value)
    self.js().set_style('top', f'{value}px')
    
  y = top
    
  @property
  def width(self):
    "width"    
    value = self._resolve_anchor(WIDTH)
    if value is None:
      value = self._resolve_horizontal().width
    return value
    
  @width.setter
  def width(self, value):
    value = self._set_anchor(WIDTH, value)
    if type(value) is not Flex:
      self.js().set_style('width', f'{value}px')
    
  @property
  def height(self):
    "height"
    value = self._resolve_anchor(HEIGHT)
    if value is None:
      value = self._resolve_vertical().height
    return value
    
  @height.setter
  def height(self, value):
    value = self._set_anchor(HEIGHT, value)
    if type(value) is not Flex:
      self.js().set_style('height', f'{value}px')
    
  @property
  def right(self):
    "right"
    value = self._resolve_anchor(RIGHT)
    if value is None:
      value = self._resolve_horizontal().right
    return value
    
  @right.setter
  def right(self, value):
    value = self._set_anchor(RIGHT, value)
    left = value - self.width
    self.js().set_style('left', f'{left}px')
    
  @property
  def bottom(self):
    "bottom"
    value = self._resolve_anchor(BOTTOM)
    if value is None:
      value = self._resolve_vertical().bottom
    return value
    
  @bottom.setter
  def bottom(self, value):
    value = self._set_anchor(BOTTOM, value)
    top = value - self.height
    self.js().set_style('top', f'{top}px')
    
  @property
  def center(self):
    value = self._resolve_anchor(CENTER)
    if value is None:
      value = self._resolve_horizontal().center
    return value
    
  @center.setter
  def center(self, value):
    value = self._set_anchor(CENTER, value)
    left = value - self.width/2
    self.js().set_style('left', f'{left}px')
    
  @property
  def middle(self):
    value = self._resolve_anchor(MIDDLE)
    if value is None:
      value = self._resolve_vertical().middle
    return value

  @middle.setter
  def middle(self, value):
    value = self._set_anchor(MIDDLE, value)
    top = value - self.height/2
    self.js().set_style('top', f'{top}px')

  @property
  def inset(self):
    return (self.inset_top, self.inset_right, self.inset_bottom, self.inset_left)
    
  @inset.setter
  def inset(self, value):
    "Insets to be applied to flexible layout values. 1-4 pixel values (or percentages?)."
    if type(value) in [int, float]:
      insets = (value,)*4
    elif type(value) in [list, tuple]:
      if len(value) == 1:
        insets = (value[0],)*4
      elif len(value) == 2:
        insets = (value[0], value[1])*2
      elif len(value) == 3:
        insets = (value[0], value[1], value[2], value[1])
      elif len(value) == 4:
        insets = value
    self.inset_top, self.inset_right, self.inset_bottom, self.inset_left = insets

  def stretch_all(self):
    pass
    
  def stretch_horizontal(self):
    pass
    
  def stretch_vertical(self):
    pass

  def dock_top(self, share=0.25):
    self.left = 0
    self.top = 0
    self.width = At(self.parent, WIDTH)
    self.height = At(self.parent, HEIGHT, multiplier=share)
    
  def dock_bottom(self, share=0.25):
    self.left = 0
    self.bottom = At(self.parent, HEIGHT)
    self.width = At(self.parent, WIDTH)
    self.height = At(self.parent, HEIGHT, multiplier=share)
    
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
    
    
class Box(View):
  
  def style(self):
    super().style()
    self.shadow(0, 0, 7, 1, inset=True)
  

class Label(Box):
  
  def style(self):
    super().style()
    c = self.content = Box(self, tint_color='black')
    c.width = Flex(c, WIDTH)
    c.height = Flex(c, HEIGHT)
    c.center = At(self, WIDTH, multiplier=0.5)
    c.middle = At(self, HEIGHT, multiplier=0.5)
    
    #self.js().set_content("<div class='content' style='position: absolute; top: 0; left: 0; right: 0; bottom: 0;'></div>")
    #self.js().set_content("<div class='content' style='position: relative;'></div>")
    #self.js().set_style('textAlign', CENTER)
    #self.js().set_style('margin', 'auto')
    #self.js().set_style('verticalAlign', 'middle')
    
  @property
  def text(self):
    return 'NOT IMPLEMENTED'
    
  @text.setter
  def text(self, value):
    #self.content.js().set_style('width', 'auto')
    #self.content.js().set_style('height', 'auto')
    self.content.js().set_content(value)
    #print(self.content.js().style('height'))


class At():
  def __init__(self, ref, prop, offset=0, multiplier=None):
    self.ref = ref
    self.prop = prop
    self.offset = offset
    self.multiplier = multiplier

  def resolve(self):
    result = _get(self.ref, self.prop)
    if type(self.multiplier) is str:
      self.multiplier = float(self.multiplier.strip('%'))/100
    result *= self.multiplier or 1
    result += self.offset
    return result

class Flex():
  def __init__(self, view, prop):
    self.view = view
    self.prop = prop
    
  def resolve(self):
    prop_actual = 'clientWidth' if self.prop == WIDTH else 'clientHeight'
    js = f'document.getElementById("{self.view.id}").style.{self.prop}'
    print(js)
    print(self.view.root.eval_js(js))
    print(self.view.js().style(self.prop))

    value = self.view.js().dot(prop_actual).evaluate()
    #print(value)
    value = float(value.strip('px'))
    return value

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
    for dependent, dep_prop in self._dependents:
      dependent._refresh_anchor(dep_prop)
    
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
    self.present('full_screen', hide_title_bar=True, hide_close_button=True)
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
      v.dock_top(share = .5)
      v.text = 'Testing with paljon enemmän tärkeää tekstiä joka varmasti täyttää koko systeemin'
      #v.align_vertical = MIDDLE
      
      v2 = Box(root, tint_color='red')
      v2.dock_bottom(share='20%')
      
      v3 = Box(root, tint_color='orange')
      v3.dock_bottom(share='20%')
      
      v4 = Box(root, tint_color='green')
      v4.dock_bottom(share='20%')

      #print('Content', self.eval_js('document.body.innerHTML'))
  
  webview = TestUI()