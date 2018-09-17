#coding: utf-8

class StyleProps():
  
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
  def align_horizontal(self):
    return 'NOT IMPLEMENTED'
    
  @align_horizontal.setter
  def align_horizontal(self, value):
    self.js().set_style('textAlign', f'{value}')

  @property
  def align_vertical(self):
    return 'NOT IMPLEMENTED'
    
  @align_vertical.setter
  def align_vertical(self, value):
    
    self.js().set_style('display', 'table-cell')
    self.js().set_style('verticalAlign', f'{value}')
    self.js().xpath('text()').set_style('position', f'relative')
    self.js().xpath('text()').set_style('height', f'100%')
    
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

  @property
  def font(self):
    return self.js().style('font')
    
  @font.setter
  def font(self, value):
    self.js().set_style('font', value)
    
  @property
  def font_family(self):
    return self.js().style('fontFamily')
    
  @font_family.setter
  def font_family(self, value):
    self.js().set_style('fontFamily', value)
    
  @property
  def font_size(self):
    return self.js().style('fontSize').strip('px')
    
  @font_size.setter
  def font_size(self, value):
    self.js().set_style('fontSize', str(value)+'px')
    
  @property
  def font_bold(self):
    value = self.js().style('fontWeight')
    return value == 'bold'
    
  @font_bold.setter
  def font_bold(self, value):
    value = 'bold' if value else 'normal'
    self.js().set_style('fontWeight', value)
    
  @property
  def font_small_caps(self):
    "Set to True to display text in small caps. "
    value = self.js().style('fontVariant')
    return value == 'small-caps'
    
  @font_small_caps.setter
  def font_small_caps(self, value):
    value = 'small-caps' if value else 'normal'
    self.js().set_style('fontVariant', value)

  @property
  def visible(self):
    "Set to False to hide the view. The layout of other views will remain anchored to a hidden view."
    value = self.js().style('visibility')
    return value == 'visible'
    
  @visible.setter
  def visible(self, value):
    value = 'visible' if value else 'hidden'
    self.js().set_style('visibility', value)

  def shadow(self, *args, color=None, inset=False):
    color = color or self.tint_color
    if len(args) == 1 and args[0] == False:
      attr_js = 'none'
    else:
      attr_js = 'inset ' if inset else ''
      for dimension in args:
        attr_js += f'{dimension}px '
      attr_js += self.to_css_color(color)
    self.js().set_style('boxShadow', attr_js)