import wikipedia
from unsync import unsync
import ui
from scene import Rect, Size
from anchor import *
from vector import Vector
import time
from random import *
import spritekit as sk
from objc_util import on_main_thread, ObjCInstance


class WikipediaGraph:
  
  def __init__(self, scene):
    self.scene = scene
    self.selected_page = None
    self.loaded_content = None
    self.nodes = {}
    
  @unsync
  def search_term(self, term):
    for node in self.nodes.values():
      node.parent = None
    hits = wikipedia.search(term)
    for hit in hits:
      if term.lower() == hit.lower():
        self.put_on_screen([hit])
        break
    else:
      self.put_on_screen(hits)
    
  @on_main_thread
  def put_on_screen(self, hits, parent=None):
    for hit in hits:
      pos_v = Vector(randint(100,150),0)
      pos_v.degrees = randint(1, 360)
      self.nodes[hit] = node = GraphNode(hit,
        position=tuple(pos_v),
        charge=1.0,
        mass=1.0,
        field_bitmask=3,
        parent=self.scene
      )
      if parent is not None:
        j = sk.Joint.spring(parent, node,
          parent.position, node.position,
          frequency=0.8, damping=0.2)
    if len(hits) == 1:
      self.fetch_page(hits[0])
      
  @on_main_thread
  def no_match(self):
    self.nodes = { 'Not found':
      sk.LabelNode('Not found',
        position=(0,100),
        font_color='grey',
        alignment=sk.LabelNode.ALIGN_CENTER,
        parent=self.scene
      )
    }
    
  @unsync
  def fetch_page(self, name):
    if name != self.selected_page:
      self.selected_page = name
      node = self.nodes[name]
      node.dynamic = False
      node.run_action(
        sk.Action.move_to((0,0)))
      for key in self.nodes:
        if key != name:
          self.nodes[key].parent = None
      self.nodes = { name: node }
      self.loaded_content = wikipedia.page(name)
      if self.loaded_content.title == name:
        self.put_on_screen(self.loaded_content.links, node)
      else:
        self.no_match()


class SpringScene(sk.Scene):
  
  def layout(self):
    x,y,w,h = self.view.bounds
    self.set_edge_loop(
      *self.convert_from_view((0,h)),
      w,h
    )
    
class GraphNode(sk.BoxNode):
  
  def __init__(self, text,
    fill_color='lightgrey',
    font_color='black',
    font=('Apple SD Gothic Neo', 12),
    **kwargs):
      
    self.text = text
      
    size = ui.measure_string(text, 
      max_width=150,
      font=font,
      alignment=ui.ALIGN_CENTER,
    )
    outer = size + Size(32, 16)
    inner = size + Size(24, 8)
    super().__init__(outer,
      fill_color='transparent',
      line_color='transparent',
      **kwargs)
    self.visible_background = sk.BoxNode(inner,
      fill_color=fill_color,
      no_body=True,
      parent=self
    )
    label = sk.LabelNode(text,
      font=font,
      font_color=font_color,
      max_width=150,
      line_break_mode=ui.LB_WORD_WRAP,
      number_of_lines=0,
      alignment=sk.LabelNode.ALIGN_CENTER,
      vertical_alignment=sk.LabelNode.ALIGN_MIDDLE,
      parent=self.visible_background
    )
    self.touch_enabled = True
    
  def touch_began(self, t):
    self.start_time = time.time()
    self.prev_pos = self.convert_point_to(t.location, self.scene)
    self.dynamic = False
    
  def touch_moved(self, t):
    scene_pos = self.convert_point_to(t.location, self.scene)
    self.position += (scene_pos - self.prev_pos)
    self.prev_pos = scene_pos
    
  def touch_ended(self, t):
    self.dynamic = True
    if time.time() - self.start_time < 0.3:
      self.visible_background.fill_color = 'red'
      self.parent.graph.fetch_page(self.text)


class SectionNode(GraphNode):
  pass

class WikipediaBrowser(ui.View):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.previous_size_class = None
    self.active_constraints = []
    enable(self)
    self.create_ui()
  
  def style(self, view):
    #view.background_color='black'
    #view.border_color = 'black'
    #view.border_width = 1
    #view.text_color = 'black'
    view.tint_color = 'black'
    
  def create_ui(self):    
    self.style(self)
    
    main_frame = View(name='Main frame')
    self.add_subview(main_frame)
    main_frame.dock.all(fit=Dock.SAFE)
    
    self.search_field = search_field = TextField(
      name='Searchfield', 
      placeholder='Search term',
      clear_button_mode='always',
      action=self.search,
      )
    main_frame.add_subview(search_field)
    self.style(search_field)
    
    search_button = Button(
      name='Search', 
      title='Search',
      action=self.search,
    ).dock.fit()
    main_frame.add_subview(search_button)
    self.style(search_button)
    
    self.scene = SpringScene(
      physics=sk.UIPhysics,
      physics_debug=True,
      background_color='white',
      anchor_point=(0.5, 0.5)
    )

    sk.FieldNode.electric(
      strength=0.2,
      falloff=1.5,
      minimum_radius=10,
      category_bitmask=1,
      parent=self.scene
    )
    
    sk.FieldNode.radial_gravity(
      strength=0.2,
      falloff=1,
      minimum_radius=10,
      parent=self.scene
    )
    
    
    result_area = self.scene.view
    enable(result_area)
    main_frame.add_subview(result_area)

    search_field.dock.top_leading()
    search_button.dock.top_trailing()
    search_field.at.trailing == search_button.at.leading_padding
    search_field.align.height(search_button)
    
    result_area.dock.bottom()
    result_area.at.top == search_field.at.bottom_padding
    
    self.scene.graph = WikipediaGraph(self.scene)
    self.search_field.begin_editing()

  '''
  def layout(self):
    x,y,w,h = self.scene.view.bounds
    self.scene.set_edge_loop(
      *self.scene.convert_from_view((0,h)),
      *self.scene.convert_from_view((w,0))
    )
  '''

  def search(self, sender):
    self.search_field.end_editing()
    search_term = self.search_field.text
    self.scene.graph.search_term(search_term)


root = WikipediaBrowser()
root.present('full_screen', hide_title_bar=True, animated=False)
