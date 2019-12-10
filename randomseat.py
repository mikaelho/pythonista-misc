#coding: utf-8
from ui import *
import random
from  scripter import *
import dialogs

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
    def run_lottery(self):
        while True:
            dialogs.alert('Arporaattori', '', 'Olkoon Voima kanssanne', hide_cancel_button=True)
            (row,seat) = self.random_seat()
            (x,y) = self.seat_coords(row,seat)
            spot = View(
              #background_color=(.81, .35, .35, 0.9),
              border_color='red',
              border_width=4,
              corner_radius=10,
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
            timer(spot, 2.0)
            yield
            dialogs.alert(f'Rivi {row+1}, paikka {seat+1}', '', 'OK', hide_cancel_button=True)
            self.remove_subview(spot)

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

    c.run_lottery()
