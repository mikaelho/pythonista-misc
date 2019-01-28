#coding: utf-8
from objc_util import *
from types import SimpleNamespace

NSLayoutConstraint = ObjCClass('NSLayoutConstraint')
UILayoutGuide = ObjCClass('UILayoutGuide')

class Constraint:
  
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
    self.multiplier = other
    return self
    
  def __truediv__(self, other):
    self.multiplier = 1/other
    return self
    
  def __add__(self, other):
    self.constant = other
    return self
    
  def __sub__(self, other):
    self.constant = -other
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
    self.attribute = 0
    return self
    
  @property
  def left(self):
    self.attribute = 1
    return self
    
  @property
  def right(self):
    self.attribute = 2
    return self
    
    
  @property
  def top(self):
    self.attribute = 3
    return self
    
  @property
  def bottom(self):
    self.attribute = 4
    return self
    
  @property
  def leading(self):
    self.attribute = 5
    return self
    
  @property
  def trailing(self):
    self.attribute = 6
    return self
    
  @property
  def width(self):
    self.attribute = 7
    return self
    
  @property
  def height(self):
    self.attribute = 8
    return self
    
  @property
  def center_x(self):
    self.attribute = 9
    return self
    
  @property
  def center_y(self):
    self.attribute = 10
    return self
    
  @property
  def last_baseline(self):
    self.attribute = 11
    return self
    
  @property
  def first_baseline(self):
    self.attribute = 12
    return self
    
  @property
  def left_margin(self):
    self.attribute = 13
    return self
    
  @property
  def right_margin(self):
    self.attribute = 14
    return self
    
  @property
  def top_margin(self):
    self.attribute = 15
    return self
    
  @property
  def bottom_margin(self):
    self.attribute = 16
    return self
    
  @property
  def leading_margin(self):
    self.attribute = 17
    return self
    
  @property
  def trailing_margin(self):
    self.attribute = 18
    return self
  
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
    if self.objc_constraint:
      self.objc_constraint.setPriority_(value)
      
  @property
  def active(self):
    if self.objc_constraint:
      return self.objc_constraint.isActive()
      
  '''
  @classmethod 
  def activate(cls, *constraints):
    for constraint in constraints:
      if type(constraint) in (tuple, list):
        Constraint.activate(*constraint)
      else:
        constraint.active = True
  '''
        
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

  @classmethod
  def margin_inset(cls, view):
    m = view.objc_instance.directionalLayoutMargins()
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
    
  @classmethod
  def _fit(cls, view, fit):
    s = view.superview
    if fit == C.TIGHT:
      return C(s)
    elif fit == C.MARGIN:
      return C(s).margins
    elif fit == C.SAFE:
      return C(s).safe_area
    
  @classmethod
  def dock_all(cls, view, constant=0, fit=default_fit):
    C = Constraint
    C(view).top == C._fit(view, fit).top + constant
    C(view).bottom == C._fit(view, fit).bottom - constant
    C(view).leading == C._fit(view, fit).leading + constant
    C(view).trailing == C._fit(view, fit).trailing - constant
    
  @classmethod
  def dock_center(cls, view, share=None):
    C = Constraint
    s = view.superview
    C(view).center_x == C(s).center_x
    C(view).center_y == C(s).center_y
    cls._set_size(view, share)
    
  @classmethod
  def _set_size(cls, view, share):
    if share is not None:
      share_x, share_y = share if type(share) in (list, tuple) else (share, share)
      C(view).width == C(view.superview).width * share_x
      C(view).height == C(view.superview).height * share_y
    
  @classmethod
  def dock_top(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).top == C._fit(view, fit).top + constant
    C(view).leading == C._fit(view, fit).leading + constant
    C(view).trailing == C._fit(view, fit).trailing - constant
    if share is not None:
      
      C(view).height == C(view.superview).height * share
    
  @classmethod
  def dock_bottom(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).bottom == C._fit(view, fit).bottom - constant
    C(view).leading == C._fit(view, fit).leading + constant
    C(view).trailing == C._fit(view, fit).trailing - constant
    if share is not None:
      
      C(view).height == C(view.superview).height * share
    
  @classmethod
  def dock_leading(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).leading == C._fit(view, fit).leading + constant
    C(view).top == C._fit(view, fit).top + constant
    C(view).bottom == C._fit(view, fit).bottom - constant
    if share is not None:
      
      C(view).width == C(view.superview).width * share
    
  @classmethod
  def dock_trailing(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).trailing == C._fit(view, fit).trailing - constant
    C(view).top == C._fit(view, fit).top + constant
    C(view).bottom == C._fit(view, fit).bottom - constant
    if share is not None:
      
      C(view).width == C(view.superview).width * share
    
  @classmethod
  def dock_top_leading(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).top == C._fit(view, fit).top + constant
    C(view).leading == C._fit(view, fit).leading + constant
    cls._set_size(view, share)
    
  @classmethod
  def dock_top_trailing(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).top == C._fit(view, fit).top + constant
    C(view).trailing == C._fit(view, fit).trailing - constant
    cls._set_size(view, share)
    
  @classmethod
  def dock_bottom_leading(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).bottom == C._fit(view, fit).bottom - constant
    C(view).leading == C._fit(view, fit).leading + constant
    cls._set_size(view, share)
    
  @classmethod
  def dock_bottom_trailing(cls, view, share=None, constant=0, fit=default_fit):
    C = Constraint
    C(view).bottom == C._fit(view, fit).bottom - constant
    C(view).trailing == C._fit(view, fit).trailing - constant
    cls._set_size(view, share)
    
  @on_main_thread
  def _create_constraint(self, other):
    if isinstance(other, C):
      self.other_view = other.view
      self.other_attribute = other.attribute
      self.constant = other.constant
      self.multiplier = other.multiplier
    elif isinstance(other, (int, float)):
      self.constant = other
    else:
      raise TypeError(f'Cannot use object of type {str(type(other))} in a constraint comparison')
    
    try:
      view_first_seen = \
      self.view.objc_instance.translatesAutoresizingMaskIntoConstraints()
    except AttributeError:
      view_first_seen = False
    if view_first_seen: 
      self.view.objc_instance.setTranslatesAutoresizingMaskIntoConstraints_(False)
      C._set_defaults(self.view)
      
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
    ).autorelease()
    
    retain_global(self.objc_constraint)
    retain_global(self.view)
    if self.other_view:
      retain_global(self.other_view)
    
    self.objc_constraint.setActive_(True)
   
    
  @classmethod
  def _set_defaults(cls, view):
    (C(view, priority=1).left == C(view.superview).left + view.x)
    (C(view, priority=1).top == C(view.superview).top + view.y)
    (C(view, priority=1).width == view.width)
    (C(view, priority=1).height == view.height)
    

if __name__ == '__main__':
  
  import ui
  import scripter
  
  C = Constraint
  
  root = ui.View()
  
  textfield = ui.TextField()
  root.add_subview(textfield)
  
  button = ui.Button(background_color='blue', tint_color='white', title='Go')
  root.add_subview(button)
  
  C.dock_center(textfield, (0.9, 0.1))
  
  for c in C.constraints_by_attribute(textfield, C.height):
    print(c)
  
  '''
  guide = C.create_guide(root)
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
  
