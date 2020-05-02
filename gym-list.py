#coding: utf-8

import ui
import anchor
import pygestures

import tinysync

import functools, types, datetime


dark_background = '#0e0e0e'
default_tint = '#fffade' # '#e6fbff' 
default_highlight = '#7faa6e'
font = 'Apple SD Gothic Neo'

class DaySource:
  
  def __init__(self, tableview, exercises):
    self.ex = exercises   
    self.tableview = tableview
    self.full_height = None
    tableview.row_height = 100
    
    self.edit_button = ui.ButtonItem(
      tint_color='grey',
      title='Edit',
      enabled=True,
      action=self.edit,
    )
  
    self.add_button = ui.ButtonItem(
      tint_color='grey',
      title='Add',
      enabled=True,
      action=self.add,
    )
  
    tableview.right_button_items = [self.add_button, self.edit_button]

  def tableview_number_of_rows(self, tableview, section):
      return len(self.ex)

  def tableview_cell_for_row(self, tableview, section, row):
      cell = ui.TableViewCell()
      cell.selectable = False
      cell.background_color='black'
      tf = ui.TextField(text=self.ex[row].title,
        key='title',
        row=row,
        delegate=self,
        font = (font, 32),
        background_color='black',
        text_color='white',
        alignment=ui.ALIGN_CENTER,
        bordered=False,
        frame=cell.content_view.bounds.inset(8,8),
        flex='WH')
      cell.content_view.add_subview(tf)
      return cell

  def tableview_did_select(self, tableview, section, row):
    day = self.ex[row]
    
    ex_table = ui.TableView(
      background_color='black',
      frame=self.nav_view.bounds, flex='WH'
    )
    
    ex_source = ExerciseSource(ex_table, day.exercises)
    
    ex_table.data_source = ex_source
    ex_table.delegate = ex_source
    
    self.nav_view.push_view(ex_table)
    
  def textfield_should_begin_editing(self, textfield):
    if self.tableview.editing:
      if self.full_height is None:
        self.full_height = self.tableview.height
      self.tableview.height = 450
      return True
    else:
      self.tableview_did_select(None, 0, textfield.row)
      return False
  
  def textfield_did_end_editing(self, textfield):
    self.ex[textfield.row][textfield.key] = textfield.text
    self.tableview.height = self.full_height
    #self.edit(self.edit_button)
    
  def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
    self.ex.insert(to_row, self.ex.pop(from_row))
    
  def tableview_delete(self, tableview, section, row):
      self.ex.remove(self.ex[row])
      self.tableview.reload()
    
  def edit(self, sender):
    if not self.tableview.editing:
      self.tableview.set_editing(True, True)
      sender.title = 'Done'
    else:
      self.tableview.set_editing(False, True)
      sender.title = 'Edit'
      
  def add(self, sender):
    self.ex.append({
      'title': '?',
      'exercises': []
    })
    self.tableview.reload()
      
  def tableview_can_delete(self, tableview, section, row): return True

  def tableview_can_move(self, tableview, section, row): return True
  

class ExerciseSource(DaySource):

  def create_textfield(self, row, key, size, container):
    tf = anchor.TextField(
      text=str(self.ex[row].get(key, '')),
      row=row,
      key=key,
      delegate=self,
      font = (font, size),
      background_color='black',
      text_color='white',
      alignment=ui.ALIGN_CENTER,
      bordered=False,
    )
    container.add_subview(tf)
    return tf
    
  def create_label(self, text, size, container):
    l = anchor.Label(
      text=text,
      font = (font, size),
      background_color='black',
      text_color='white',
      alignment=ui.ALIGN_RIGHT,
      )
    container.add_subview(l)
    return l

  def tableview_cell_for_row(self, tableview, section, row):
    cell = ui.TableViewCell()
    cell.selectable = False
    cell.background_color = 'black'
    ex = self.ex[row]
    container = anchor.View(
      frame=cell.content_view.bounds, 
      flex='WH')
    cell.content_view.add_subview(container)
    
    tf_title = self.create_textfield(
      row, 'title', 24, container)
    tf_title.dock.top_leading()
    tf_title.at.height == 40
    
    tf_reps = self.create_textfield(
      row, 'reps', 24, container)
    tf_reps.dock.top_trailing()
    tf_reps.at.width == 75
    tf_reps.align.height(tf_title)
    
    tf_title.at.trailing == tf_reps.at.leading_padding
    
    l_o = self.create_label('OSKARI', 10, container)
    l_m = self.create_label('MIKAEL', 10, container)
    l_filler = self.create_label('', 10, container)
    
    tf_w_o = self.create_textfield(
      row, 'weight_oskari', 24, container)
    tf_w_m = self.create_textfield(
      row, 'weight_mikael', 24, container)
      
    l_o.dock.bottom_leading()
    l_o.at.top == tf_title.at.bottom_padding
    l_o.align.top(l_m, l_filler, tf_w_o, tf_w_m)
    l_o.align.bottom(l_m, l_filler, tf_w_o, tf_w_m)
    l_o.align.width(l_m)
    l_filler.at.width == l_o.width/2
    tf_w_o.at.width == 75
    tf_w_o.align.width(tf_w_m)
    l_filler.at.trailing == container.at.trailing_margin
    tf_w_o.at.leading == l_o.at.trailing_padding
    l_m.at.leading == tf_w_o.at.trailing_padding
    tf_w_m.at.leading == l_m.at.trailing_padding
    l_filler.at.leading == tf_w_m.at.trailing_padding
  
    return cell
    
  def textfield_should_begin_editing(self, textfield):
    if self.full_height is None:
      self.full_height = self.tableview.height
    self.tableview.height = 433
    return True
    
  def add(self, sender):
    self.ex.append({
      'title': '?',
      'image_name': '',
      'reps': '3x10',
      'weight_mikael': 0,
      'weight_oskari': 0,
    })
    self.tableview.reload()


if __name__ == '__main__':
  
  exercises = tinysync.track([], name='gym-program')
  
  v = ui.View(background_color='black',)
  
  
  day_table = ui.TableView(
    background_color='black',
    frame=v.bounds, flex='WH',
  )
  
  day_source = DaySource(day_table, exercises)
  day_table.data_source = day_source
  day_table.delegate = day_source
  
  n = anchor.NavigationView(
    day_table,
    navigation_bar_hidden=False,
    background_color='black',
    title_color='black',
    tint_color='grey',
    bar_tint_color='black',
    frame=v.bounds, flex='WH')
  day_source.nav_view = n
  #n.objc_instance.navigationController().navigationBar().hidden = True
  
  v.add_subview(n)
  n.dock.all(fit=anchor.Dock.SAFE)
  
  v.present(
    'fullscreen',
    animated=False,
    hide_title_bar=True,
    title_bar_color='black',
    orientations=['portrait'])
