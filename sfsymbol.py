
import ui, clipboard
from objc_util import *

UIImage = ObjCClass('UIImage')
UIImageSymbolConfiguration = ObjCClass('UIImageSymbolConfiguration')

UIImagePNGRepresentation = c.UIImagePNGRepresentation
UIImagePNGRepresentation.restype = c_void_p
UIImagePNGRepresentation.argtypes = [c_void_p]

#WEIGHTS
ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK = range(1, 10)
# SCALES
SMALL, MEDIUM, LARGE = 1, 2, 3

def SymbolImage(name, point_size=None, weight=None, scale=None):
    ''' Create a ui.Image from an SFSymbol name. Optional parameters:
        * point_size - Integer font size
        * weight - Font weight, one of ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK
        * scale - Size relative to font size, one of SMALL, MEDIUM, LARGE 
        
    Run the file to see a symbol browser.'''
    objc_image = ObjCClass('UIImage').systemImageNamed_(name)
    conf = UIImageSymbolConfiguration.defaultConfiguration()
    if point_size is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithPointSize_(point_size))
    if weight is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithWeight_(weight))
    if scale is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithScale_(scale))
    objc_image = objc_image.imageByApplyingSymbolConfiguration_(conf)
        
    return ui.Image.from_data(
        nsdata_to_bytes(ObjCInstance(UIImagePNGRepresentation(objc_image)))
    )


if __name__ == '__main__':

    class SymbolSource:
        
        symbols_per_page = 20
      
        def __init__(self, tableview):
            self.tableview = tableview
            tableview.row_height = 50
            self.weight = THIN
            
            with open('sfsymbolnames.txt', 'r') as fp:
                all_lines = fp.read()    
            raw = all_lines.splitlines()
            
            restricted_prefix = 'Usage restricted'
            
            self.symbol_names = []
            for i, symbol_name in enumerate(raw):
                if raw[i].startswith(restricted_prefix): continue
                if i+1 == len(raw): continue
                value = symbol_name
                if raw[i+1].startswith(restricted_prefix):
                    value = 'R ' + value
                self.symbol_names.append(value)
    
            self.index = 0
            
            self.prev_button = ui.ButtonItem(
              tint_color='black',
              image=SymbolImage('arrow.left', 8, weight=THIN),
              enabled=False,
              action=self.prev,
            )
            self.to_start_button = ui.ButtonItem(
              tint_color='black',
              image=SymbolImage('arrow.left.to.line', 8, weight=THIN),
              enabled=False,
              action=self.to_start,
            )
            self.next_button = ui.ButtonItem(
              tint_color='black',
              image=SymbolImage('arrow.right', 8, weight=THIN),
              enabled=True,
              action=self.next,
            )
            self.to_end_button = ui.ButtonItem(
              tint_color='black',
              #title='Next',
              image=SymbolImage('arrow.right.to.line', 8, weight=THIN),
              enabled=True,
              action=self.to_end,
            )
            self.weight_button = ui.ButtonItem(
              tint_color='black',
              title='Thin',
              enabled=True,
              action=self.change_weight,
            )
          
            tableview.left_button_items = [
                self.to_start_button,
                self.prev_button]
            tableview.right_button_items = [
                self.to_end_button, 
                self.next_button, 
                self.weight_button]
            
        def next(self, sender):
            self.index += self.symbols_per_page
            if self.index + self.symbols_per_page >= len(self.symbol_names):
                self.index = len(self.symbol_names) - self.symbols_per_page - 1
                self.next_button.enabled = False
                self.to_end_button.enabled = False
            self.prev_button.enabled = True
            self.to_start_button.enabled = True
            self.tableview.reload()
            
        def to_end(self, sender):
            self.index = len(self.symbol_names) - self.symbols_per_page - 1
            self.next_button.enabled = False
            self.to_end_button.enabled = False
            self.prev_button.enabled = True
            self.to_start_button.enabled = True
            self.tableview.reload()
            
        def prev(self, sender):
            self.index -= self.symbols_per_page
            if self.index <= 0:
                self.index = 0
                self.prev_button.enabled = False
                self.to_start_button.enabled = False
            self.next_button.enabled = True
            self.to_end_button.enabled = True
            self.tableview.reload()
            
        def to_start(self, sender):
            self.index = 0
            self.prev_button.enabled = False
            self.to_start_button.enabled = False
            self.next_button.enabled = True
            self.to_end_button.enabled = True
            self.tableview.reload()
            
        def change_weight(self, sender):
            titles = ['Ultralight', 'Thin', 'Light', 'Regular', 'Medium', 'Semibold', 'Bold', 'Heavy', 'Black']
            self.weight += 1
            if self.weight > BLACK:
                self.weight = ULTRALIGHT
            self.weight_button.title = titles[self.weight-1]
            self.tableview.reload()
            
        def tableview_number_of_rows(self, tableview, section):
            return self.symbols_per_page
            
        def tableview_cell_for_row(self, tableview, section, row):
            cell = ui.TableViewCell()
            cell.selectable = False
            cell.background_color='black'
            
            symbol_name = self.symbol_names[self.index+row]
            tint_color = 'white'
            if symbol_name.startswith('R '):
                symbol_name = symbol_name[2:]
                tint_color = 'orange'
            symbol_image = SymbolImage(symbol_name, 
            point_size=14, weight=self.weight, scale=SMALL)
    
            button = ui.Button(
                tint_color=tint_color,
                title='   '+symbol_name,
                font=('Fira Mono', 14),
                image=symbol_image,
                frame=cell.content_view.bounds,
                flex='WH',
                action=self.copy_to_clipboard,
                #enabled=False,
            )
            
            cell.content_view.add_subview(button)
    
            return cell
    
        def copy_to_clipboard(self, sender):
            clipboard.set(sender.title[3:])
      
    symbol_table = ui.TableView(
        background_color='black',
    )
    
    symbol_table.data_source = SymbolSource(symbol_table)
    
    symbol_table.present()

