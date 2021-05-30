import ui
from tinysync import track


font = 'Apple SD Gothic Neo'

class FoodSource:
    
    def __init__(self, tableview):
        self.tableview = tableview
        self.ruoat = track([], 'ruoat')
        
        self.add_button = ui.ButtonItem(
            tint_color='black',
            title='Lisää',
            enabled=True,
            action=self.add,
        )
        tableview.right_button_items = [self.add_button]
        
        self.last_created = None
        self.full_height = None
    
    def tableview_number_of_rows(self, tableview, section):
        return len(self.ruoat)
        
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        #cell.selectable = False
        cell.background_color='#f6f6f6'
        tf = ui.TextField(
            text=self.ruoat[row],
            row=row,
            placeholder='???',
            delegate=self,
            font=(font, 20),
            background_color='white',
            text_color='black',
            alignment=ui.ALIGN_LEFT,
            bordered=False,
            frame=cell.content_view.bounds.inset(8, 8, 8, 75),
            flex='WH',
        )
        cell.content_view.add_subview(tf)
        self.last_created = tf
        return cell
        
    def tableview_delete(self, tableview, section, row):
        self.ruoat.remove(self.ruoat
        [row])
        self.tableview.delete_rows([row])
    
    def add(self, sender):
        self.ruoat.insert(0, '')
        self.tableview.insert_rows([0])
        self.last_created.begin_editing()
      
    def tableview_can_delete(self, tableview, section, row):
        return True
        
    def tableview_did_select(self, tableview, section, row):
        moving = self.ruoat[row]
        self.tableview_delete(tableview, section, row)
        self.ruoat.append(moving)
        self.tableview.insert_rows([len(self.ruoat)-1])
    
    def textfield_should_begin_editing(self, textfield):
        if self.full_height is None:
            self.full_height = self.tableview.height
        self.tableview.height = 434
        return True
  
    def textfield_did_end_editing(self, textfield):
        self.ruoat[textfield.row] = textfield.text
        self.tableview.height = self.full_height


table = ui.TableView(
    background_color='white',
)
  
source = FoodSource(table)
table.data_source = source
table.delegate = source

  
table.present(
    'fullscreen',
    animated=False,
    #hide_title_bar=True,
    #title_bar_color='black',
    orientations=['portrait'],
)

