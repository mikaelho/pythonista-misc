#coding: utf-8
import uuid, collections
import inheritable
from jswrapper import *
from types import SimpleNamespace as ns

click_event = 'click'


class View(AttributeWrapper):
  
  def __init__(self, parent=None):
    self.id = str(uuid.uuid4())[-12:]
    self.default_left = 0
    self.default_top = 0
    self.default_width = 100
    self.default_height = 100
    self.default_layout_offset = 0
    self.children = []
    self._anchors = {}
    self._dependents = set()
    if parent:
      self.parent = parent
      self.root = parent.root
      self.root.add_child_for(self, parent)
      self.style()
    self._refresh_position()     
      
  def _refresh_position(self):
    for prop, js_prop in ((View.top, 'top'), (View.left, 'left'), (View.width, 'width'), (View.height, 'height')):
      value = prop.fget(self)
      self.js().set_style(js_prop, f'{value}px')
    
  def add_dependent(self, anchor):
    self.dependents.add(anchor)
    
  def style(self):
    #self.layout_position = View.FIXED
    #self.x = self.y = 100
    #self.height = 100
    #self.width = 100
    self.background_color = 'cyan'

  def render(self):
    child_renders = ''
    for child in self.children:
      child_renders += child.render()
    return f'<div id=\'{self.id}\' style=\'position: absolute;\'>{child_renders}</div>'
    
  @property
  def on_click(self):
    return self.root.get_event_handler(self, click_event)
    
  @on_click.setter
  def on_click(self, handler):
    self.root.register_event_handler(self, click_event, handler)  
    
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
    if type(anchor) in [int, float]:
      return anchor
    if type(anchor) is At:
      offset = self.default_layout_offset if anchor.offset is None else anchor.offset
      return anchor.prop.fget(anchor.ref) + offset
    return None
      
  def _refresh_anchor(self, prop):
    anchor = self._anchors.get(prop)
    prop.fset(self, anchor)
    
  def _resolve_horizontal(self):
    left = self._resolve_anchor(View.left)
    right = self._resolve_anchor(View.right)
    width = self._resolve_anchor(View.width)
    center = self._resolve_anchor(View.center)
    if not left:
      if right and center:
        left = right - (right-center)
        # check center
      elif width and center:
        left = center - width/2
        # check right
      elif right and width:
        left = right - width
      elif right or center:
        width = self.default_width
        if right:
          left = right - width
        elif center:
          left = center - width/2
      else:
        left = self.default_left
    if not width:
      if right:
        width = right - left
        # check center
      elif center:
        width = (center - left)*2
      else:
        width = self.default_width
    if not right:
      right = left + width
      # check center
    if not center:
      center = (left + right)/2
    return ns(left=left, right=right, center=center, width=width)
    
  def _resolve_vertical(self):
    top = self._resolve_anchor(View.top)
    bottom = self._resolve_anchor(View.bottom)
    height = self._resolve_anchor(View.height)
    middle = self._resolve_anchor(View.middle)
    if not top:
      if bottom and middle:
        top = bottom - (bottom - middle)
        # check center
      elif height and middle:
        top = middle - height/2
        # check right
      elif bottom and height:
        top = bottom - height
      elif bottom or middle:
        height = self.default_height
        if bottom:
          top = bottom - height
        elif middle:
          top = middle - height/2
      else:
        top = self.default_top
    if not height:
      if bottom:
        height = bottom - top
        # check center
      elif middle:
        height = (middle - top)*2
      else:
        height = self.default_height
    if not bottom:
      bottom = top + height
      # check center
    if not middle:
      middle = (top + bottom)/2
    return ns(top=top, bottom=bottom, middle=middle, height=height)
    
  def js(self):
    return JSWrapper(self.root).by_id(self.id)

  @property
  def left(self):
    "left"
    value = self._resolve_anchor(View.left)
    if not value:
      value = self._resolve_horizontal().left
    return value
    
  @left.setter
  def left(self, value):
    value = self._set_anchor(View.left, value)
    self.js().set_style('left', f'{value}px')
    
  x = left
    
  @property
  def top(self):
    "top"
    value = self._resolve_anchor(View.top)
    if not value:
      value = self._resolve_vertical().top
    return value
    
  @top.setter
  def top(self, value):
    value = self._set_anchor(View.top, value)
    self.js().set_style('top', f'{value}px')
    
  y = top
    
  @property
  def width(self):
    "width"    
    value = self._resolve_anchor(View.width)
    if not value:
      value = self._resolve_horizontal().width
    return value
    
  @width.setter
  def width(self, value):
    value = self._set_anchor(View.width, value)
    self.js().set_style('width', f'{value}px')
    
  @property
  def height(self):
    "height"
    value = self._resolve_anchor(View.height)
    if not value:
      value = self._resolve_vertical().height
    return value
    
  @height.setter
  def height(self, value):
    value = self._set_anchor(View.height, value)
    self.js().set_style('height', f'{value}px')
    
  @property
  def right(self):
    "right"
    value = self._resolve_anchor(View.right)
    if not value:
      value = self._resolve_horizontal().right
    return value
    
  @right.setter
  def right(self, value):
    value = self._set_anchor(View.right, value)
    left = value - self.width
    self.js().set_style('left', f'{left}px')
    
  @property
  def bottom(self):
    "bottom"
    value = self._resolve_anchor(View.bottom)
    if not value:
      value = self._resolve_vertical().bottom
    return value
    
  @bottom.setter
  def bottom(self, value):
    value = self._set_anchor(View.bottom, value)
    top = value - self.height
    self.js().set_style('top', f'{top}px')
    
  @property
  def center(self):
    value = self._resolve_anchor(View.center)
    if not value:
      value = self._resolve_horizontal().center
    return value
    
  @center.setter
  def center(self, value):
    value = self._set_anchor(View.center, value)
    left = value - self.width/2
    self.js().set_style('left', f'{left}px')
    
  @property
  def middle(self):
    value = self._resolve_anchor(View.middle)
    if not value:
      value = self._resolve_vertical().middle
    return value

  @middle.setter
  def middle(self, value):
    value = self._set_anchor(View.middle, value)
    top = value - self.height/2
    self.js().set_style('top', f'{top}px')

  def stretch_all(self):
    pass
    
  def stretch_horizontal(self):
    pass
    
  def stretch_vertical(self):
    pass

  @classmethod
  def dock_top(cls):
    pass
    
  @classmethod
  def dock_bottom(cls):
    pass
    
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
    
  def inset(self, *amounts):
    "1-4 pixels or percentages"
    pass
    
  def to_css_color(self, color):
    if type(color) is str:
      return color
    if type(color) == tuple and len(color) >= 3:
      alpha = color[3] if len(color) == 4 else 1.0
      if all((component >= 1.0) for component in color):
        color_rgb = [int(component*255) for component in color[:3]]
        color_rgb.append(color[3] if len(color) == 4 else 1.0)
        color = tuple(color_rgb)
      return f'rgba{str(color)}'
    
  @property
  def background_color(self):
    return self.js().style('backgroundColor')
    
  @background_color.setter
  def background_color(self, value):
    self.js().set_style('backgroundColor', self.to_css_color(value))
    
  @property
  def background_image(self):
    return self.js().style('backgroundImage')
    
  @background_image.setter
  def background_image(self, value):
    self.js().set_style('backgroundImage', self.to_css_color(value))


class At():
  def __init__(self, ref, prop, offset=None):
    self.ref = ref
    self.prop = prop
    self.offset = offset

class UI(inheritable.WebView):
  
  event_prefix = 'pythonista-event://'
  
  def __init__(self, **kwargs):
    self.super().__init__(**kwargs)
    self.root = self
    self.children = []
    self.all_views_by_id = {}
    self.event_handlers = {}
    self.delegate = self
    
    self.scales_page_to_fit = False
    self.objc_instance.subviews()[0].subviews()[0].setScrollEnabled(False)
    #self.add_subview(ui.View(frame=(100,100,100,100), border_width=1, border_color='black'))
    
    with open('main-ui.html', 'r') as h:
      self.load_html(h.read())
    
  def webview_did_finish_load(self, webview):
    self.init()
    self.present()
    
  def webview_should_start_load(self, webview, url, nav_type):
    #print(url)
    if url.startswith(self.event_prefix):
      url = url[len(self.event_prefix):]
      id = url[:12]
      event_name = url[12:]
      view = self.all_views_by_id[id]
      handler = self.event_handlers[id+event_name]
      handler(view)
      return False
    return True
    
  def register_event_handler(self, view, event_name, handler):
    self.event_handlers[view.id+event_name] = handler
    JSWrapper(self).by_id(view.id).dot(f'addEventListener("click", function(event) {{ window.location.href="{self.event_prefix}{view.id}{event_name}" }})').evaluate()
    
  def get_event_handler(self, view, event_name):
    return self.event_handlers[view.id+event_name]
    
  def remove_event_handler(self, id, event_name):
    del self.event_handlers[id+event_name]
    
  def init(self):
    pass
    
  def add_child_for(self, child, parent):
    if child not in parent.children:
      parent.children.append(child)
    self.all_views_by_id[child.id] = child
    js = JSWrapper(self)
    parent_elem = js.xpath('body') if parent is self else js.by_id(parent.id)
    parent_elem.append(child.render())
  

if __name__ == '__main__':
  
  def click_handler(source):
    print(source)
  
  class TestUI(UI):
    
    def init(self):
      v = View(parent=self)
      #v.background_image = 'linear-gradient(black, darkgrey, lightgrey)'
      v.background_color = 'cyan'
      v.on_click = click_handler
      v2 = View(parent=self)
      v2.background_color = 'red'
      v2.y = At(v, View.bottom)
      v2.left = At(v, View.right)
      v2.height = At(v, View.height)
      v3 = View(parent=self)
      v3.background_color = 'orange'
      v3.bottom = At(v, View.top)
      v3.right = At(v, View.left)
      v3.width = At(v, View.width)
      v4 = View(parent=self)
      v4.background_color = 'green'
      v4.center = At(v, View.center)
      v4.width = 20
      v4.height = 200
      v4.middle = At(v, View.middle)
      v.y = 200
      v.x = 150
      v.height = 50
      v.width = 75
      #print('Content', self.eval_js('document.body.innerHTML'))
  
  root = TestUI()