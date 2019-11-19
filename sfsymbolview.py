
import ui
from objc_util import *

UIImage = ObjCClass('UIImage')
UIImageSymbolConfiguration = ObjCClass('UIImageSymbolConfiguration')

UIImagePNGRepresentation = c.UIImagePNGRepresentation
UIImagePNGRepresentation.restype = c_void_p
UIImagePNGRepresentation.argtypes = [c_void_p]

SMALL, MEDIUM, LARGE = 1, 2, 3
ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK = range(1, 10)

def SymbolImage(name, scale=None, weight=None):
    objc_image = ObjCClass('UIImage').systemImageNamed_(name)
    if scale is not None:
        conf = UIImageSymbolConfiguration.configurationWithScale_(scale)
        objc_image = objc_image.imageByApplyingSymbolConfiguration_(conf)
        
    return ui.Image.from_data(
        nsdata_to_bytes(ObjCInstance(UIImagePNGRepresentation(objc_image)))
    )


class SymbolSource:
    
    symbols_per_page = 20
  
    def __init__(self, tableview):
        self.tableview = tableview
        tableview.row_height = 75
        
        with open('sfsymbolnames.txt', 'r') as fp:
            all_lines = fp.read()    
        raw = all_lines.splitlines()
        restricted_prefix = 'Usage restricted'
        
        self.symbol_names = [ symbol_name
            for symbol_name in raw
            if not symbol_name.startswith(restricted_prefix)
        ]

        self.index = 0
        
        self.next_button = ui.ButtonItem(
          tint_color='grey',
          title='Next',
          enabled=True,
          action=self.next,
        )
      
        self.prev_button = ui.ButtonItem(
          tint_color='grey',
          title='Prev',
          enabled=False,
          action=self.prev,
        )
      
        tableview.left_button_items = [self.prev_button]
        tableview.right_button_items = [self.next_button]
        
    def next(self, sender):
        self.index += self.symbols_per_page
        self.prev_button.enabled = True
        self.tableview.reload()
        
    def prev(self, sender):
        self.index -= self.symbols_per_page
        self.next_button.enabled = True
        self.tableview.reload()
        
    def tableview_number_of_rows(self, tableview, section):
        return self.symbols_per_page
        
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.selectable = False
        cell.background_color='black'
        
        symbol_name = self.symbol_names[self.index+row]
        symbol_image = SymbolImage(symbol_name, SMALL)

        button = ui.Button(
            tint_color='white',
            title='   '+symbol_name,
            image=symbol_image,
            frame=cell.content_view.bounds,
            flex='WH',
            #enabled=False,
        )
        
        cell.content_view.add_subview(button)

        return cell

  
symbol_table = ui.TableView(
    background_color='black',
)

symbol_table.data_source = SymbolSource(symbol_table)

symbol_table.present()

