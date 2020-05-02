#coding: utf-8
from ui import *
import anchor
import random
from  scripter import *
import dialogs

quotes = [
    ('Olkoon Voima kanssanne', 'Arporaattori'),
    ('Do, or do not. There is no try.', 'Yoda'),
    ('These are not the seats you are looking for', 'Obi-Wan Kenobi'),
    ('Everything is proceeding as I have foreseen','The Emperor'),
    ('Help me Arporaattori, you are my only hope', 'Princess Leia'),
    ('Money leads to tickets; tickets lead to seats; seats lead to prizes', 'Yoda'),
    ('I find your lack of faith disturbing', 'Darth Vader'),
    ('Baby Yoda! Baby Yoda!', 'The Internet'),
    ('I’ve got a bad feeling about this.', 'Han Solo'),
    ('Never tell me the odds', 'Han Solo'),
]

@script
def wait_for_tap(view):
    t = WaitForTap(view)
    while not t.tapped:
        yield
        

class WaitForTap(View):
    
    def __init__(self, target, **kwargs):
        super().__init__(**kwargs)
        self.tapped = False
        self.background_color = (0,0,0,0.0001)
        self.frame=target.bounds
        target.add_subview(self)
            
    def touch_ended(self, touch):
        self.tapped = True
      

class QuoteView(View):
    
    def __init__(self, quote_index, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0,0,0,0.8)
        anchor.enable(self)
        quote = anchor.Label(
            text=quotes[quote_index][0]+'\n',
            font=('Savoye LET', 64),
            text_color='white',
            number_of_lines=0,
            alignment=ALIGN_CENTER
        )
        
        attribution = anchor.Label(
            text='- '+quotes[quote_index][1].upper(),
            font=('Apple SD Gothic Neo', 20),
            text_color='white',
            alignment=ALIGN_RIGHT
        )
        
        self.add_subview(quote)
        self.add_subview(attribution)
        
        quote.at.width == self.at.width * 0.7
        quote.at.center_x == self.at.center_x
        quote.at.center_y == self.at.center_y
        
        attribution.at.trailing == quote.at.trailing
        attribution.at.top == quote.at.bottom_padding
    
    @script
    def touch_ended(self, touch):
        hide(self)
        yield
        self.superview.run_lottery()
        
        
class WinningSeatView(View):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0,0,0,0.8)
        anchor.enable(self)

        row_label = anchor.Label(
            text=f'Rivi'.upper(),
            font=('Apple SD Gothic Neo', 16),
            text_color='white',
            alignment=ALIGN_RIGHT
        )

        row_number = self.row = anchor.Label(
            font=('Apple SD Gothic Neo', 48),
            text_color='white',
            number_of_lines=0,
            alignment=ALIGN_CENTER
        )
        seat_label = anchor.Label(
            text='PAIKKA',
            font=('Apple SD Gothic Neo', 16),
            text_color='white',
            alignment=ALIGN_RIGHT
        )
        seat_number = self.seat = anchor.Label(
            font=('Apple SD Gothic Neo', 48),
            text_color='white',
            alignment=ALIGN_CENTER
        )
        
        for view in (seat_label,seat_number,row_label,row_number):
            self.add_subview(view)
        self.align.center_x(row_number, seat_number)
        
        row_number.at.width >= seat_number.at.width
        seat_number.at.width >= row_number.at.width
        row_number.at.bottom == self.at.center_y
        seat_number.at.top == row_number.at.bottom_padding
        row_label.at.first_baseline == row_number.at.first_baseline
        row_label.at.trailing = row_number.at.leading_padding
        seat_label.at.first_baseline == seat_number.at.first_baseline
        seat_label.at.trailing = seat_number.at.leading_padding
        
    def set_values(self, row, seat):
        self.row.text=f'{row}\n'
        self.seat.text=f'{seat}'


class CustomView(View):

    seat_map = [
        (2,13),
        (1,15),
        (1,15),
        (1,15),
        (2,14),
        (1,15),
        (2,14),
        (2,14),
        (2,14),
        (1,15),
    ]

    def __init__(self, image, **kwargs):
        super().__init__(**kwargs)
        self.seat_count = sum([last - first + 1 for (first, last) in self.seat_map])
        self.image = image
        self.quote_index = 0
        self.results_view = WinningSeatView(
            frame=self.bounds, flex='WH',
            alpha = 0
        )
        self.add_subview(self.results_view)

    def layout(self):
        (iw, ih) = self.image.size

        if self.width < self.height:
            img_width = self.width
            img_height = self.width/iw*ih
        else:
            img_width = self.height/ih*iw
            img_height = self.height

        self.cover_x = (self.width - img_width)/2 + img_width/5.6
        self.cover_y = (self.height - img_width)/2 + img_width/12
        cover_width = img_width*0.61
        cover_height = img_width*0.77
        self.x_incr = cover_width/15
        self.y_incr = cover_height/10

    def seat_coords(self, row, seat):
        lead = self.seat_map[row][0]
        return (
            (15-seat-lead)*self.x_incr+self.cover_x,
            (9-row)*self.y_incr+self.cover_y
        )

    def random_seat(self):
        row = random.randint(0,9)
        seat = random.randint(0,self.seat_map[row][1]-1)
        return (row, seat)

    def next_seat(self, row, seat):
        seat += 1
        if seat == self.seat_map[row][1]:
            seat = 0
            row += 1
        if row == 10:
            row = 0
        return (row,seat)

    @script
    def kick_off(self):
        wait_for_tap(self)
        yield
        self.show_quote()

    @script
    def show_quote(self):
        quote_index = 0
        '''
        dialogs.alert('Arporaattori', '', quotes[quote_index], hide_cancel_button=True)
        '''

        quote_view = QuoteView(self.quote_index,
            frame=self.bounds,
            flex='WH',
            alpha=0.0)
        self.quote_index += 1
        self.add_subview(quote_view)
        show(quote_view)
        '''
        quote_view.present('full_screen', 
            hide_title_bar=True, 
            animated=False)
        quote_view.wait_modal()
        '''

    @script
    def run_lottery(self):
        (row,seat) = self.random_seat()
        (x,y) = self.seat_coords(row,seat)
        spot = Label(
            #background_color=(.81, .35, .35, 0.9),
            border_color='red',
            text_color=(0,0,0,0),
            border_width=4,
            corner_radius=10,
            alignment=ALIGN_CENTER,
            number_of_lines=0,
            font=('Apple SD Gothic Neo', 48),
            frame=(-10,-10,self.width+20,self.height+20))
        self.add_subview(spot)
        move(spot, x, y)
        slide_value(spot, 'width', self.x_incr)
        slide_value(spot, 'height', self.y_incr)
        yield

        seats_left = seats_to_move = int((1.0 + random.random() * 2.0) * self.seat_count)
        slow_down_threshold = random.randint(self.seat_count//4, self.seat_count//2)

        step_time = 1/120
        while seats_left > 0:
            seats_left -= 1
            if seats_left < slow_down_threshold:
                fraction = seats_left/slow_down_threshold
                step_time = 1/120 + (1.0-ease_out(fraction)) * 22/45
            prev_row = row
            (row,seat) = c.next_seat(row,seat)
            (x,y) = c.seat_coords(row,seat)
            if prev_row == row:
                move(spot,x,y, duration=step_time)
                yield
            else:
                spot.x = x
                spot.y = y
            #if random.random() < step_time:
            #    step_time += 1/30
        timer(spot, 1.0)
        yield
        self.remove_subview(spot)
        '''
        spot.text = f'rivi\n{row+1}\n\npaikka\n{seat+1}'
        slide_color(spot, 'text_color', 'white')
        slide_value(spot, 'width', self.width)
        slide_value(spot, 'height', self.height)
        center(spot, self.bounds.center())
        slide_color(spot, 'background_color', (0,0,0,0.8))
        slide_color(spot, 'border_color', (0,0,0,0))
        slide_value(spot, 'corner_radius', 0)
        yield
        '''
        self.results_view.set_values(row+1, seat+1)
        show(self.results_view)
        wait_for_tap(self)
        yield
        hide(self.results_view)

        '''
        seat_view = WinningSeatView(row+1, seat+1,
            frame=self.bounds,
            flex='WH',
            alpha=0.0)
        self.add_subview(seat_view)
        show(seat_view)
        '''
        #dialogs.alert(f'Rivi {row+1}, paikka {seat+1}', '', 'OK', hide_cancel_button=True)
        self.show_quote()
        

if __name__ == '__main__':
    img = Image('sali9.jpg')
    v = ImageView()
    v.content_mode = CONTENT_SCALE_ASPECT_FIT
    v.image = img

    v.background_color = 'black'
    v.present('full_screen', hide_title_bar=True)

    c = CustomView(img, frame=v.bounds, flex='WH')
    v.add_subview(c)

    c.layout()

    (row,seat) = c.random_seat()
    (x,y) = c.seat_coords(row,seat)

    c.kick_off()
