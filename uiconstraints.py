#coding: utf-8
from objc_util import *
import ui
from types import SimpleNamespace
from copy import copy

NSLayoutConstraint = ObjCClass('NSLayoutConstraint')
UILayoutGuide = ObjCClass('UILayoutGuide')

class Constrain:
  
  autofit_types = [ui.Button, ui.Label]
  
  def __init__(self, view, priority=1000):
    self.view = view
    self.attribute = None
    self.operator = None
    self.other_view = None
    self.other_attribute = 0
    self.multiplier = 1
    self._constant = 0
    self._priority = priority
    self.objc_constraint = None
    
  @property
  def constant(self):
    return self._constant
    
  @constant.setter
  def constant(self, value):
    self._constant = value
    if self.objc_constraint:
      self.objc_constraint.setConstant_(value)
    
  def __str__(self):
    return f'{type(self.view).__name__}.{self.attribute} {self.operator} {type(self.other_view).__name__}.{self.other_attribute} * {self.multiplier} + {self.constant}'
    
  def __mul__(self, other):
    self.multiplier *= other
    return self
    
  def __truediv__(self, other):
    self.multiplier *= 1/other
    return self
    
  def __add__(self, other):
    self._constant += other
    return self
    
  def __sub__(self, other):
    self._constant -= other
    return self
    
  def __le__(self, other):
    self.operator = -1
    self._create_constraint(other)
    return self
    
  def __eq__(self, other):
    self.operator = 0
    self._create_constraint(other)
    return self
    
  def __ge__(self, other):
    self.operator = 1
    self._create_constraint(other)
    return self
    
  @property
  def no_attribute(self):
    c = copy(self)
    c.attribute = 0
    return c
    
  @property
  def left(self):
    c = copy(self)
    c.attribute = 1
    return c
    
  @property
  def right(self):
    c = copy(self)
    c.attribute = 2
    return c
    
    
  @property
  def top(self):
    c = copy(self)
    c.attribute = 3
    return c
    
  @property
  def bottom(self):
    c = copy(self)
    c.attribute = 4
    return c
    
  @property
  def leading(self):
    c = copy(self)
    c.attribute = 5
    return c
    
  @property
  def trailing(self):
    c = copy(self)
    c.attribute = 6
    return c
    
  @property
  def width(self):
    c = copy(self)
    c.attribute = 7
    return c
    
  @property
  def height(self):
    c = copy(self)
    c.attribute = 8
    return c
    
  @property
  def center_x(self):
    c = copy(self)
    c.attribute = 9
    return c
    
  @property
  def center_y(self):
    c = copy(self)
    c.attribute = 10
    return c
    
  @property
  def last_baseline(self):
    c = copy(self)
    c.attribute = 11
    return c
    
  @property
  def first_baseline(self):
    c = copy(self)
    c.attribute = 12
    return c
    
  @property
  def left_margin(self):
    c = copy(self)
    c.attribute = 13
    return c
    
  @property
  def right_margin(self):
    c = copy(self)
    c.attribute = 14
    return c
    
  @property
  def top_margin(self):
    c = copy(self)
    c.attribute = 15
    return c
    
  @property
  def bottom_margin(self):
    c = copy(self)
    c.attribute = 16
    return c
    
  @property
  def leading_margin(self):
    c = copy(self)
    c.attribute = 17
    return c
    
  @property
  def trailing_margin(self):
    c = copy(self)
    c.attribute = 18
    return c
    
  @property
  def top_padding(self):
    c = copy(self)
    c.attribute = 3
    c._constant -= c.margin_inset().top
    return c
    
  @property
  def bottom_padding(self):
    c = copy(self)
    c.attribute = 4
    c._constant += c.margin_inset().bottom
    return c
    
  @property
  def leading_padding(self):
    c = copy(self)
    c.attribute = 5
    c._constant -= c.margin_inset().leading
    return c
    
  @property
  def trailing_padding(self):
    c = copy(self)
    c.attribute = 6
    c._constant += c.margin_inset().trailing
    return c
    
  @property
  def safe_area(self):
    self.view = SimpleNamespace(
      objc_instance=self.view.objc_instance.safeAreaLayoutGuide(), name='Safe area')
    return self
    
  @property
  def margins(self):
    self.view = SimpleNamespace(
      objc_instance=self.view.objc_instance.layoutMarginsGuide(), name='Margins')
    return self
    
  @classmethod
  def create_guide(cls, view):
    class Guide(SimpleNamespace):
      @property
      def superview(self):
        if self.view:
          return self.view.superview
          
      @property
      def subviews(self):
        if self.view:
          return self.view.subviews
      
    guide = UILayoutGuide.new().autorelease()
    view.objc_instance.addLayoutGuide_(guide)
    return Guide(objc_instance=guide, view=view, name='LayoutGuide')
    
  @property
  def priority(self):
    "Note: Cannot change priority between required and optional after present()."
    if self.objc_constraint:
      return objc_constraint.priority()
      
  @priority.setter
  def priority(self, value):
    if type(value) is not int or value < 0 or value > 1000:
      raise ValueError('priority must be an integer in the range [0, 1000]')
    if self.objc_constraint:
      previous_value = self.objc_constraint.priority()
      if self.view.on_screen and \
      ((value == 1000 and \
        previous_value != 1000) or \
      (value != 1000 and \
        previous_value == 1000)):
        raise ValueError(
          'Cannot change priority value between required (1000) and lower value')
      self.objc_constraint.setPriority_(value)
      
  @property
  def active(self):
    if self.objc_constraint:
      return self.objc_constraint.isActive()

  @classmethod
  def constraints_by_attribute(cls, view, attribute, active_only=True):
    constraints = getattr(view, 'layout_constraints', [])
    result = []
    for constraint in constraints:
      if active_only and not constraint.active:
        continue
      if attribute == cls.characteristics[constraint.attribute][0]:
        result.append(constraint)
    return result
        
  @classmethod
  def deactivate(cls, *constraints):
    for constraint in constraints:
      print(type(constraint))
      if type(constraint) in (tuple, list):
        Constraint.deactivate(*constraint)
      else:
        self.objc_constraint.setActive_(False)

  def margin_inset(self):
    m = self.view.objc_instance.directionalLayoutMargins()
    return SimpleNamespace(bottom=m.a, leading=m.b, trailing=m.c, top=m.d)
    
  @property
  def superview(self):
    if self.view:
      return self.view.superview
      
  @property
  def subviews(self):
    if self.view:
      return self.view.subviews
    
  TIGHT = 0
  MARGIN = 1
  SAFE = 2
  default_fit = MARGIN

  def _fit(self, fit):
    s = self.superview
    if fit == Constrain.TIGHT:
      return Constrain(s)
    elif fit == Constrain.MARGIN:
      return Constrain(s).margins
    elif fit == Constrain.SAFE:
      return Constrain(s).safe_area
    
  def dock_all(self, constant=0, fit=default_fit):
    view = self.view
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    
  def dock_center(self, share=None):
    s = Constrain(self.superview)
    self.center_x == s.center_x
    self.center_y == s.center_y
    self._set_size(share)
  
  def dock_sides(self, constant=0, fit=default_fit):
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    
  dock_horizontal = dock_sides
  
  def dock_horizontal_between(self, top_view, bottom_view, constant=0, fit=default_fit):
    self.dock_horizontal(constant, fit)
    if fit == Constrain.TIGHT:
      self.top == Constrain(top_view).bottom + constant
      self.bottom == Constrain(bottom_view).top + constant
    elif fit == Constrain.MARGIN:
      self.top == Constrain(top_view).bottom_padding + constant
      self.bottom == Constrain(bottom_view).top_padding + constant
    
  def dock_vertical(self, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    
  def dock_vertical_between(self, leading_view, trailing_view, constant=0, fit=default_fit):
    self.dock_vertical(constant, fit)
    if fit == Constrain.TIGHT:
      self.leading == Constrain(leading_view).trailing + constant
      self.trailing == Constrain(trailing_view).leading + constant
    elif fit == Constrain.MARGIN:
      self.leading == Constrain(leading_view).trailing_padding + constant
      self.trailing == Constrain(trailing_view).leading_padding + constant
    
  def _set_size(self, share):
    if share is not None:
      share_x, share_y = share if type(share) in (list, tuple) else (share, share)
      s = Constrain(self.superview)
      self.width == s.width * share_x
      self.height == s.height * share_y
    
  def dock_top(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      self.height == Constrain(self.superview).height * share
  
  def dock_bottom(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      self.height == Constrain(self.superview).height * share
    
  def dock_leading(self, share=None, constant=0, fit=default_fit):
    self.leading == self._fit(fit).leading + constant
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      self.width == Constrain(self.superview).width * share
    
  def dock_trailing(self, share=None, constant=0, fit=default_fit):
    self.trailing == self._fit(fit).trailing - constant
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      self.width == Constrain(self.superview).width * share
    
  def dock_top_leading(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.leading == self._fit(fit).leading + constant
    self._set_size(share)
    
  def dock_top_trailing(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  def dock_bottom_leading(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self._set_size(share)

  def dock_bottom_trailing(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  position = 0
  size = 1
  horizontal = 0
  vertical = 1
  na = -1
        
  characteristics = {
    0: (no_attribute, size, na),
    1: (left, position, horizontal),
    2: (right, position, horizontal),
    3: (top, position,vertical),
    4: (bottom, position, vertical),
    5: (leading, position, horizontal),
    6: (trailing, position, horizontal),
    7: (width, size, horizontal),
    8: (height, size, vertical),
    9: (center_x, position, horizontal),
    10: (center_y, position, vertical),
    11: (last_baseline, position, vertical),
    12: (first_baseline, position, vertical),
    13: (left_margin, position, horizontal),
    14: (right_margin, position, horizontal),
    15: (top_margin, position, vertical),
    16: (bottom_margin, position, vertical),
    17: (leading_margin, position, horizontal),
    18: (trailing_margin, position, horizontal)
  }
    
  @on_main_thread
  def _create_constraint(self, other):
    if isinstance(other, Constrain):
      self.other_view = other.view
      self.other_attribute = other.attribute
      self.constant = other.constant
      self.multiplier = other.multiplier
    elif isinstance(other, (int, float)):
      self.constant = other
    else:
      raise TypeError(
        f'Cannot use object of type {str(type(other))} in a constraint comparison: ' + 
        str(self))
    
    a = Constrain.characteristics[self.attribute]
    b = Constrain.characteristics[self.other_attribute]
    
    if a[1] == Constrain.position and (
      self.multiplier == 0 or
      self.other_view == None or 
      self.other_attribute == 0):
      raise AttributeError(
        'Location constraints cannot relate to a constant only: ' + str(self))
    
    if a[1] != b[1]:
      raise AttributeError(
        'Constraint cannot relate location and size attributes: ' + str(self))
      
    if a[1] == b[1] == Constrain.position and a[2] != b[2]:
      raise AttributeError(
        'Constraint cannot relate horizontal and vertical location attributes: '\
        + str(self))
    
    try:
      view_first_seen = \
      self.view.objc_instance.translatesAutoresizingMaskIntoConstraints()
    except AttributeError:
      view_first_seen = False
    if view_first_seen: 
      self.view.objc_instance.setTranslatesAutoresizingMaskIntoConstraints_(False)
      #C._set_defaults(self.view)
      if type(self.view) in C.autofit_types:
        self.size_to_fit()
      
    layout_constraints = getattr(self.view, 'layout_constraints', [])
    layout_constraints.append(self)
    self.view.layout_constraints = layout_constraints
    
    self.objc_constraint = NSLayoutConstraint.\
    PG_constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_priority_(
      self.view.objc_instance,
      self.attribute,
      self.operator,
      None if not self.other_view else self.other_view.objc_instance,
      self.other_attribute,
      self.multiplier,
      self.constant,
      self._priority
    ) #.autorelease()
    
    #retain_global(self.objc_constraint)
    #retain_global(self.view)
    #if self.other_view:
    #  retain_global(self.other_view)
    
    self.objc_constraint.setActive_(True)
   
    
  @classmethod
  def _set_defaults(cls, view):
    C = Constrain
    (C(view, priority=1).width == view.width)
    (C(view, priority=1).height == view.height)
    (C(view, priority=1).left == C(view.superview).left + view.x)
    (C(view, priority=1).top == C(view.superview).top + view.y)
    
  def size_to_fit(self):
    view = self.view
    size = view.objc_instance.sizeThatFits_((0,0))
    margins = self.margin_inset()
    (Constrain(view).width == size.width + margins.leading + margins.trailing).priority = 1
    (Constrain(view).height == size.height).priority = 1


if __name__ == '__main__':
  
  import ui
  import scripter
  
  C = Constrain
  
  def style(view):
    view.background_color='white'
    view.border_color = 'black'
    view.border_width = 1
    view.text_color = 'black'
    view.tint_color = 'black'
  
  root = ui.View(background_color='white')
  
  search_field = ui.TextField(placeholder='Search path')
  root.add_subview(search_field)
  style(search_field)
  
  search_button = ui.Button(title='Search')
  root.add_subview(search_button)
  style(search_button)
  
  result_area = ui.View()
  root.add_subview(result_area)
  style(result_area)
  
  done_button = ui.Button(title='Done')
  root.add_subview(done_button)
  style(done_button)
  
  def done(sender):
    root.close()
  done_button.action = done
  
  cancel_button = ui.Button(title='Cancel')
  root.add_subview(cancel_button)
  style(cancel_button)
  
  search_field_c = Constrain(search_field)
  search_button_c = Constrain(search_button)
  done_button_c = Constrain(done_button)
  cancel_button_c = Constrain(cancel_button)
  result_area_c = Constrain(result_area)
  
  search_field_c.dock_top_leading()
  search_field_c.trailing == search_button_c.leading_padding
  
  search_field_c.dock_top_leading()
  search_button_c.dock_top_trailing()
  search_field_c.trailing == search_button_c.leading_padding
  search_field_c.height == search_button_c.height
  
  done_button_c.dock_bottom_trailing()
  cancel_button_c.trailing == done_button_c.leading_padding
  cancel_button_c.top == done_button_c.top
  
  result_area_c.dock_horizontal_between(search_button, done_button)
  
  '''
  result_area_c.dock_sides()
  result_area_c.top == search_button_c.bottom_padding
  result_area_c.bottom == done_button_c.top_padding
  '''
  '''
  path = 'resources/images/awesome/regular/industry/travel/sun'
  for component in path.split('/'):
    label = ui.Label(text=component)
    style(label)
    result_area.add_subview(label)

    if len(result_area.subviews) > 1:
      previous_label = result_area.subviews[-2]
      
      C(label).last_baseline >= C(previous_label).last_baselineä
      C(label).trailing <= C(result_area).trailing_margin
      #C(label, priority=300).top == C(result_area).top_margin
      C(label, priority=399).top == C(previous_label).top

      C(label, priority=500).leading == C(previous_label).trailing_padding
      C(label, priority=400).leading == C(result_area).leading_margin
      C(label, priority=400).top == C(previous_label).bottom_padding
    else:
      C(label).top == C(result_area).top_margin
      C(label).leading == C(result_area).leading_margin
    previous_label = label
  '''
  #for c in C.constraints_by_attribute(textfield, C.height):
  #  print(c)
  
  '''
  guide = C.create_guide(root)
  C(guide).left_margin == C(root).left

  C(textfield).leading == C(guide).leading
  gap = (C(button).left == C(textfield).right + C.margin_inset(button).leading)
  C(button).trailing == C(guide).trailing
  C(textfield).top == C(guide).top

  C(textfield).bottom == C(guide).bottom
  C(button).center_y == C(textfield).center_y
  C(button).height == C(button).width

  C(guide).leading == C(root).margins.leading
  C(guide).trailing == C(root).margins.trailing
  C(guide).center_y == C(root).center_y
  C(guide).height == 30
  '''
  
  root.present(animated=False)
  
  @scripter.script
  def constant_to(constraint, value, **kwargs):
    scripter.slide_value(constraint, 'constant', value, **kwargs)
  #constant_to(gap, 100, ease_func=scripter.ease_in_out)
  
