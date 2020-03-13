import ui
from anchor import GridView
from scripter import *
import sfsymbol
from pydantic import BaseModel
from typing import List, Set, Dict, Tuple
import copy

dim = 9


class CellData(BaseModel):
    col: int
    row: int
    square: Tuple[int, int]
    possible: Set[int] = set(range(1, 10))
    update: bool = True
    recent: bool = False
    
    def __str__(self):
        return f'{self.col}{self.row}'
    
    def __hash__(self):
        return hash(str(self))
        
    @property
    def certain(self):
        return len(self.possible) == 1
        
    def add_possible(self, value):
        self.possible.add(value)
        self.update = True
        self.recent = True
        
    def set_possible(self, possible):
        self.possible = possible
        self.update = True
        self.recent = True
        
    def discard_possible(self, value):
        self.possible.discard(value)
        self.update = True
        self.recent = True


class BoardData(BaseModel):
    cells: List[CellData] = []
    coords: Dict[Tuple[int, int], CellData] = {}
    cols: List[List[CellData]] = []
    rows: List[List[CellData]] = []
    squares: Dict[Tuple[int, int], Set[CellData]] = {}


class Board(ui.View):
    
    def __init__(self, prefilled=None, **kwargs):
        self.prefilled = prefilled
        
        self.data = BoardData()
        super().__init__(**kwargs)
        self.background_color = 'grey'
        
        self.grid = GridView(
            frame=self.bounds,
            flex='WH'
        )
        self.add_subview(self.grid)
        
        #self.cols = []
        #self.rows = []
        #self.squares = {}
        
        bg_color = 'white'
        for i in range(dim * dim):
            col = i % dim
            row = i // dim
            square = col // 3, row // 3
            
            bg_color = 'lightgrey' if sum(square) % 2 == 0 else 'white'
            
            starting_value = '' if (
                prefilled is None or prefilled[row][col] == 0) else str(prefilled[row][col])
            
            cell_data = CellData(
                col=col,
                row=row,
                square=square
            )
            
            cell = Cell(
                self.data,
                col, row,
                starting_value,
                name=str(cell_data),
                background_color=bg_color
            )
            
            if len(self.data.cols) == col:
                self.data.cols.append([])
            if len(self.data.rows) == row:
                self.data.rows.append([])
                
            self.data.cells.append(cell_data)
            self.data.coords[(col,row)] = cell_data
            self.data.cols[col].append(cell_data)
            self.data.rows[row].append(cell_data)
            self.data.squares.setdefault(square, set()).add(cell_data)
            
            self.grid.add_subview(cell)
        
    def layout(self):
        s = self.superview
        ui_dim = min(s.width, s.height)
        self.width = self.height = ui_dim
        #self.center = s.bounds.center()
    
    @script    
    def play(self, sender):
        if not self.prefilled:
            self.print_start()
            
        for cell_view in self.grid.subviews:
            cell_view.entry.end_editing()
            try:
                value = int(cell_view.entry.text)
            except:
                value = 0
            if value > 0:
                cell_data = self.data.coords[(cell_view.col, cell_view.row)]
                cell_data.set_possible(set((value,)))
                cell_view.update_view()
                yield
        
        step = self.solve()
        
        try:
            while True:
                next(step)
                for cell in self.data.cells:
                    if not cell.update:
                        continue
                    cell_view = self.grid[str(cell)]
                    cell_view.update_view()
                    cell.update = False
                yield
        except StopIteration:
            pass
            
    def solve(self, data_in=None):
        data = data_in or self.data
        changing = True
        while changing:
            changing = self.obvious(data)
            if not changing:
                self.background_color = 'orange'
                yield
                changing = self.infer(data)
            if not changing:
                self.background_color = 'red'
                yield
                changing = self.guess(data)
            yield
        self.background_color = 'green'
        
    def obvious(self, data):
        for cell in data.cells:
            if cell.certain and cell.recent:
                value = min(cell.possible)
                to_process = self.get_others(data, cell)
                for other in to_process:
                    if (other is not cell and 
                    value in other.possible):
                        if other.certain:
                            raise WrongGuess
                        other.discard_possible(value)
                cell.recent = False
                return True
        return False
        
    def infer(self, data):
        for cell in data.cells:
            if not cell.certain:
                if self.process(cell, data.squares[cell.square]):
                    return True
                if self.process(cell, set(data.rows[cell.row])):
                    return True
                if self.process(cell, set(data.cols[cell.col])):
                    return True
        return False
        
    def guess(self, data):
        print('guessing')
        cells = sorted([cell
            for cell in data.cells
            if not cell.certain],
            key=lambda c: len(c.possible)
        )
        for cell in cells:
            impossible = set()
            for candidate in cell.possible:
                one_guess = copy.deepcopy(data)
                #assert not (data.cells[0] is one_guess.cells[0])
                changing_cell = one_guess.coords[(cell.col,cell.row)]
                assert not cell is changing_cell
                changing_cell.set_possible(set([candidate]))
                guess_runner = self.solve(one_guess)
                try:
                    while True:
                        next(guess_runner)
                except WrongGuess:
                    impossible.add(candidate)
                    continue
                except StopIteration:
                    break
                    #data.__dict__.update(**one_guess.__dict__)
                    #return True     
            print(cell.possible, impossible)
            cell.set_possible(cell.possible.difference(impossible))
            assert len(cell.possible) > 0
            if len(impossible) > 0:
                return True
        return False
            
    def print_start(self):
        for row in self.data.rows:
            row_values = []
            for cell in row:
                cell_view = self.grid[str(cell)]
                row_values.append('0' if cell_view.entry.text == ''
                else cell_view.entry.text)
            print(f'  [{",".join(row_values)}],')
                
    def get_others(self, data, cell_data):
        return data.squares[cell_data.square].union(
            set(data.rows[cell_data.row])
        ).union(
            set(data.cols[cell_data.col])
        )
        
    def process(self, cell, others):
        uniques = set(cell.possible)
        for other in others:
            if not other is cell and not other.certain:
                uniques.difference_update(other.possible)
        if len(uniques) > 0:
            cell.set_possible(uniques)
            return True
        return False
        
        
class WrongGuess(Exception):
    pass

class Cell(ui.View):
    
    def __init__(self, data, col, row, starting_value, **kwargs):
        self.data = data
        self.col = col
        self.row = row
        #self.square = square
        super().__init__(**kwargs)
        
        #self.possibilities = set(range(1, dim+1))
        #self.fixed = False
        self.entry = ui.TextField(
            text=starting_value,
            frame=self.bounds, flex='WH',
            background_color=self.background_color,
            alignment=ui.ALIGN_CENTER,
            font=('Arial Rounded MT Bold', 24),
            bordered=False,
            keyboard_type=ui.KEYBOARD_NUMBER_PAD,
            delegate=self,
        )
        self.uncertain = GridView(
            gap=1,
            #background_color='white',
            frame=self.bounds, flex='WH',
            background_color=self.background_color,
        )
        for _ in range(dim):
            self.uncertain.add_subview(ui.View())
        self.certain = ui.Label(
            frame=self.bounds, flex='WH',
            background_color=self.background_color,
            alignment=ui.ALIGN_CENTER,
            font=('Arial Rounded MT Bold', 24),
        )

        self.add_subview(self.uncertain)
        self.add_subview(self.certain)
        self.add_subview(self.entry)
        
    def textfield_should_change(self, textfield, range, replacement):
        allow_change = len(textfield.text) < 1 or range[1] - range[0] == 1
        return allow_change
        
    def update_view(self):
        cell_data = self.data.coords[(self.col, self.row)]
        if cell_data.certain:
            self.certain.text = str(min(cell_data.possible))
            self.certain.bring_to_front()
        else:
            self.update_pips()
            self.uncertain.bring_to_front()
        
    def update_pips(self):
        cell_data = self.data.coords[(self.col, self.row)]
        for i, pip in enumerate(self.uncertain.subviews):
            if i+1 not in cell_data.possible:
                pip.background_color = 'black'
            else:
                pip.background_color = 'transparent'
        
root = ui.View(tint_color='black')

easy = [
    [ 5, 3, 0, 0, 7, 0, 0, 0, 0 ],
    [ 6, 0, 0, 1, 9, 5, 0, 0, 0 ],
    [ 0, 9, 8, 0, 0, 0, 0, 6, 0 ],
    [ 8, 0, 0, 0, 6, 0, 0, 0, 3 ],
    [ 4, 0, 0, 8, 0, 3, 0, 0, 1 ],
    [ 7, 0, 0, 0, 2, 0, 0, 0, 6 ],
    [ 0, 6, 0, 0, 0, 0, 2, 8, 0 ],
    [ 0, 0, 0, 4, 1, 9, 0, 0, 5 ],
    [ 0, 0, 0, 0, 8, 0, 0, 7, 9 ],
]

medium = [
  [0,0,6,0,0,5,0,0,7],
  [8,5,1,0,2,0,3,0,0],
  [4,0,0,0,9,0,2,0,5],
  [2,0,0,5,0,0,0,4,0],
  [7,3,0,0,0,0,5,8,0],
  [0,0,0,4,0,0,1,2,0],
  [0,0,8,9,0,0,0,0,0],
  [3,4,0,0,8,7,0,0,0],
  [1,0,0,0,5,0,0,0,0],
]

hard = [
  [3,0,0,8,7,0,0,0,0],
  [6,0,0,0,5,0,0,4,0],
  [0,0,0,0,0,3,6,9,0],
  [4,6,0,2,0,0,3,0,0],
  [0,0,9,0,0,0,7,0,0],
  [0,0,5,0,0,4,0,6,9],
  [0,4,6,9,0,0,0,0,0],
  [0,1,0,0,3,0,0,0,8],
  [0,0,0,0,4,1,0,0,6],
]

hard2 = [
  [0,0,9,0,0,4,0,0,0],
  [1,0,0,0,0,9,0,5,0],
  [0,4,0,6,1,7,0,0,3],
  [0,0,3,0,0,5,0,7,0],
  [8,9,0,3,0,2,0,4,1],
  [0,7,0,8,0,0,3,0,0],
  [9,0,0,7,4,6,0,8,0],
  [0,5,0,9,0,0,0,0,4],
  [0,0,0,1,0,0,6,0,0],
]

insane = [
    [ 8, 0, 0, 0, 0, 0, 0, 0, 0 ],
    [ 0, 0, 3, 6, 0, 0, 0, 0, 0 ],
    [ 0, 7, 0, 0, 9, 0, 2, 0, 0 ],
    [ 0, 5, 0, 0, 0, 7, 0, 0, 0 ],
    [ 0, 0, 0, 0, 4, 5, 7, 0, 0 ],
    [ 0, 0, 0, 1, 0, 0, 0, 3, 0 ],
    [ 0, 0, 1, 0, 0, 0, 0, 6, 8 ],
    [ 0, 0, 8, 5, 0, 0, 0, 1, 0 ],
    [ 0, 9, 0, 0, 0, 0, 4, 0, 0 ],
]

board = Board(
    insane
)

play_button = ui.ButtonItem(
  tint_color='black',
  image=sfsymbol.SymbolImage('play', 8, weight=sfsymbol.THIN),
  action=board.play
)
root.right_button_items = [
    play_button,
]

root.add_subview(board)

root.present(animated=False)
