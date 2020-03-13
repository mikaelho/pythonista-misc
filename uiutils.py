''' Utility functions and classes for Pythonista (iOS app) ui module. '''

from itertools import groupby
from more_itertools import chunked, collapse
import keyword

import ui


def add_subviews(view, *subviews):
    ''' Helper to add several subviews at once.
    Subviews can be provided as comma-separated arguments:
        
        add_subviews(view, subview1, subview2)
        
    ... or in an iterable:
        
        subviews = (subview1, subview2)
        add_subviews(view, subviews)
    '''
    for subview in collapse(subviews):
        view.add_subview(subview)

def apply(view, **kwargs):
    ''' Applies named parameters as changes to the view's attributes. '''
    for key in kwargs:
        setattr(view, key, kwargs[key])
                        
def apply_down(view, include_self=True, **kwargs):
    ''' Applies named parameter as changes to the view's attributes, then
    applies them also to the hierarchy of the view's subviews.
    Set `include_self` to `False` to only apply the changes to subviews. '''
    if include_self:
        apply(view, **kwargs)
    for subview in view.subviews:
        apply_down(subview, **kwargs)


class GridView(ui.View):
  """
  Places subviews as squares that fill the available space.
  """
  
  FILL = 'III'
  SPREAD = '___'
  CENTER = '_I_'
  START = 'II_'
  END = '_II'
  SIDES = 'I_I'
  START_SPREAD = 'I__'
  END_SPREAD = '__I'
  
  MARGIN = At.standard
  TIGHT = 0
  
  def __init__(self,
    pack_x=None, pack_y=None, pack=CENTER,
    count_x=None, count_y=None,
    gap=MARGIN, **kwargs):
    '''By default, subviews are laid out in a grid as squares of optimal size and
    centered in the view.
    
    You can fix the amount of views in either dimension with the `count_x` or
    `count_y` parameter, or change the packing behaviour by providing
    the `pack` parameter with one of the following values:
      
    * `CENTER` - Clustered in the center (the default)
    * `SPREAD` - Distributed evenly
    * `FILL` - Fill the available space with only margins in between
    (no longer squares)
    * `LEADING, TRAILING` (`pack_x` only)
    * `TOP, BOTTOM` (`pack_y` only)
    '''
    
    super().__init__(**kwargs)

    self.pack_x = pack_x or pack
    self.pack_y = pack_y or pack
    
    self.leading_free = self.pack_x[0] == '_'
    self.center_x_free = self.pack_x[1] == '_'
    self.trailing_free = self.pack_x[2] == '_'
    self.top_free = self.pack_y[0] == '_'
    self.center_y_free = self.pack_y[1] == '_'
    self.bottom_free = self.pack_y[2] == '_'

    self.count_x = count_x
    self.count_y = count_y
    
    self.gap = gap

    enable(self)

  def dimensions(self, count):
    if self.height == 0:
      return 1, count
    ratio = self.width/self.height
    count_x = math.sqrt(count * self.width/self.height)
    count_y = math.sqrt(count * self.height/self.width)
    operations = (
      (math.floor, math.floor),
      (math.floor, math.ceil),
      (math.ceil, math.floor),
      (math.ceil, math.ceil)
    )
    best = None
    best_x = None
    best_y = None
    for oper in operations:
      cand_x = oper[0](count_x)
      cand_y = oper[1](count_y)
      diff = cand_x*cand_y - count
      if diff >= 0:
        if best is None or diff < best:
          best = diff
          best_x = cand_x
          best_y = cand_y         
    return (best_x, best_y)
  
  def layout(self):
    count = len(self.subviews)
    if count == 0: return

    count_x, count_y = self.count_x, self.count_y
    if count_x is None and count_y is None:
      count_x, count_y = self.dimensions(count)
    elif count_x is None:
      count_x = math.ceil(count/count_y)
    elif count_y is None:
      count_y = math.ceil(count/count_x)
    if count > count_x * count_y:
      raise ValueError(
        f'Fixed counts (x: {count_x}, y: {count_y}) not enough to display all views')
        
    borders = 2 * self.border_width
        
    dim_x = (self.width-borders-(count_x+1)*self.gap)/count_x
    dim_y = (self.height-borders-(count_y+1)*self.gap)/count_y
        
    dim = min(dim_x, dim_y)
      
    px = self.pack_x
    exp_pack_x = px[0] + px[1]*(count_x-1) + px[2]
    py = self.pack_y
    exp_pack_y = py[0] + py[1]*(count_y-1) + py[2]
    free_count_x = exp_pack_x.count('_')
    free_count_y = exp_pack_y.count('_')
    
    if free_count_x > 0:
      per_free_x = (
        self.width - 
        borders -
        count_x*dim -
        (count_x+1-free_count_x)*self.gap)/free_count_x
    if free_count_y > 0:
      per_free_y = (
        self.height - 
        borders -
        count_y*dim -
        (count_y+1-free_count_y)*self.gap)/free_count_y
              
    real_dim_x = dim_x if free_count_x == 0 else dim
    real_dim_y = dim_y if free_count_y == 0 else dim
              
    subviews = iter(self.subviews)
    y = self.border_width + (per_free_y if self.top_free else self.gap)
    for row in range(count_y):
      x = self.border_width + (per_free_x if self.leading_free else self.gap)
      for col in range(count_x):
        try:
          view = next(subviews)
        except StopIteration:
          break
        view.frame = (x, y, real_dim_x, real_dim_y)
        x += real_dim_x + (per_free_x if self.center_x_free else self.gap)
      y += real_dim_y + (per_free_y if self.center_y_free else self.gap)
      

class Views(dict):
    ''' A class that is used to create a hierarchy of ui views defined by
    a tree structure, and with the given constraints.
    Also stores the created views in depth-first order.
    Views can be accessed equivalently with dict references or as attributes:
        
    * `views['top']`
    * `views.top`
    '''
    
    def __init__(self):
        super().__init__()
        self._create_views()
        
    def view_hierarchy(self):
        ''' Sample view hierarchy dictionary:
            
            { 'root': (ui.View, {
                'top': (ui.View, {
                    'search_text': ui.TextField,
                    'search_action': ui.Button,
                }),
                'middle': ui.View,
                'bottom': (ui.View, {
                    'accept': ui.Button,
                    'cancel': ui.Button,
                })
            }) }
            
        I.e. view names as keys, view classes as values.
        If the value is a tuple instead, the first value must be the view class
        and the second value a dictionary for the next level of the view
        hierarchy.
        
        View names must match the requirements for identifiers, and
        not be any of the Python keywords or attributes of this class
        (inheriting `dict`). '''
        
        return ( 'root', ui.View )
        
    def view_defaults(self, view):
        ''' Views are initialized with no arguments. This method is called
        with the initialized view to set any defaults you want.
        The base implementation creates black views with
        white borders, tint and text. '''
        bg = 'black'
        fg = 'white'
        view.background_color = bg
        view.border_color = fg
        view.border_width = 1
        view.tint_color = fg
        view.text_color = fg
        
    def set_constraints(self):
        ''' After all views have been initialized and included in
        the hierarchy, this method is called to set the constraints.
        Base implementation does nothing. '''
        pass

    def present(self):
        ''' Presents the root view of the hierarchy. The base implementation
        is a plain `present()` with no arguments.
        Return `self` so that you can combine the call with hierarchy init:
            
            views = Views().present()
        '''
        next(iter(self.values())).present()
        return self
    
    def __getattr__(self, key, oga=object.__getattribute__):
        if key in self:
            return self[key]
        else:
            return oga(self, key)
    
    def _create_views(self):
        ''' Method that creates a view hierarchy as specified by the 
        view hierarchy spec.
        Each created view is stored by name in `self`.
        '''
        
        def recursive_view_generation(view_spec, parent):
            if parent is None:
                assert len(view_spec) in (2, 3), 'Give exactly one root element'
            previous_view = None
            for is_subspec, group in groupby(view_spec, lambda x: type(x) is tuple):
                if is_subspec:
                    recursive_view_generation(next(group), previous_view)
                    continue
                for view_name, view_class in chunked(group, 2):
                    assert (
                        view_name.isidentifier()
                    ), f'{view_name} is not a valid identifier'
                    assert (
                        not keyword.iskeyword(view_name)
                    ), f'Cannot use a keyword as a view name ({view_name})'
                    assert (
                        not view_name in dir(self)
                    ), f'{view_name} is a member of Views class'

                    previous_view = view = view_class(name=view_name)
                    if parent:
                        parent.add_subview(view)
                    self.view_defaults(view)
                    self[view_name] = view
            if parent is None:
                self.set_constraints()
            
        recursive_view_generation(self.view_hierarchy(), None)
        
