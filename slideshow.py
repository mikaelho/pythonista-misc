import os.path
import pathlib
import random
import threading

import arrow
import requests

import ui
import objc_util
import console

from tinysync import track
from scripter import *
from genr import genr
import sfsymbol
import gestures
import anchor

import onedriver
import onedrive_ids


UIScreen = objc_util.ObjCClass('UIScreen')
UIWindow = objc_util.ObjCClass('UIWindow')
UIColor = objc_util.ObjCClass('UIColor')
    
class SlideShow(ui.View):
    
    def __init__(self, folder='~/Documents/slideshow', keep=True, **kwargs):
        super().__init__(**kwargs)
        self.slide_delay = 5 # seconds
        self.label_display_time = 3 # seconds
        self.label_font = 'Source Sans Pro'
        self.transition = self.transition_slide_and_fade
        self.airplaying = False
        self.keep = keep
        self.target_strategy = self.quadrant_targets
        self.position_jigger = 10
        self.rotation_jigger = 3
        
        fix_set_idle_timer_disabled(True)
        
        self.quadrants = [0,0,0,0]
        # Order: top-left, top-right, bottom-left, bottom-right
        
        self.screen_switch_lock = threading.Lock()
        
        self.photo_index = 0
        self.loaders = {}
        self.prev_album = None
        
        self.driver = onedriver.OneDriver(
            onedrive_ids.client_id,
            onedrive_ids.client_secret)

        self.folder = pathlib.Path(folder).expanduser()
        self.folder.mkdir(parents=True, exist_ok=True)
        
        self.status = ui.Label(
            text_color='white',
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.status)
        
        self.display = ui.ImageView(
            frame=self.bounds, flex='WH',
        )
        self.add_subview(self.display)
        
        self.control = ui.View(
            frame=self.bounds, flex='WH',
        )
        self.add_subview(self.control)
        
        self.old = ui.ImageView(
            frame=self.bounds,
            flex='WH',
            content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
        self.display.add_subview(self.old)
        
    def will_close(self):
        fix_set_idle_timer_disabled(False)
        #for loader in self.loaders:
        #    loader.cancel()    
        
    def start(self):
        self.initialize_local()
        self.setup_controls()
        self.watch_for_airplay()
        self.show = self.run_slideshow()
        self.refresh_album_data()
    
    def initialize_local(self):
        self.albums = track({}, str(self.folder / 'slideshow_album_data'))
        self.state = track({
            'current_photo': None
        }, str(self.folder / 'slideshow_state'))
        self.continuum = {}
        
    def show_and_hide_menu(self, data):
        self.menu.hidden = not self.menu.hidden
        find_scripter_instance(self).pause_play_all()
    
    def setup_controls(self):
        self.menu = ui.TableView(
            flex='WH',
            background_color=(0,0,0,0.5)
        )
        self.menu.data_source = AlbumSource(self, self.menu)
        
        self.menu.hidden = True
        self.control.add_subview(self.menu)
        
        border = 50
        self.menu.frame = (
            border, border,
            self.control.width-2*border,
            self.control.height-2*border)
        
        gestures.tap(self.control, self.show_and_hide_menu)
    
    @script
    def watch_for_airplay(self):
        while True:
            if not self.airplaying and len(UIScreen.screens()) > 1:
                self.airplaying = True
                second_screen = UIScreen.screens()[1]
                second_bounds = second_screen.bounds()
                second_window = UIWindow.alloc().initWithFrame_(second_bounds)
                second_window.setScreen(second_screen)
                second_window.setHidden(False)
                second_view = ui.ImageView()
                second_view.objc_instance.setFrame(second_window.bounds())
                second_window.addSubview(second_view.objc_instance)
                with self.screen_switch_lock:
                    self.display = second_view
            elif self.airplaying and len(UIScreen.screens()) == 1:
                with self.screen_switch_lock:
                    self.display = ui.ImageView(
                        frame=self.bounds,
                        flex='WH'
                    )
                    self.add_subview(self.display)
                    self.display.send_to_back()
            yield 0.3
    
    @script
    def run_slideshow(self):
        while self.state.current_photo is None:
            yield
        while True:
            timer(self, self.slide_delay)
            self.update_show()
            yield
            self.photo_index += 1
            self.state.current_photo = self.update_spec(
                self.state.current_photo, +1)
    
    @script
    def update_show(self):
        self.start_loading()
        self.present_when_ready()
        yield
        
    def start_loading(self):
        keys = set(self.continuum)
        for offset in range(5):
            photo = self.locate_photo(self.state.current_photo, offset)
            photo_index = self.photo_index+offset
            keys.discard(photo_index)
            if self.continuum.get(photo_index, None) != photo:
                self.continuum[photo_index] = photo
                self.loaders[photo.id] = self.load(photo)
        for key in keys:
            if key < photo_index - 1:
                photo = self.continuum[key]
                del self.continuum[key]
    
    @script
    def present_when_ready(self):
        photo = self.continuum[self.photo_index]
        loader = self.loaders[photo.id]
        try:
            photo_data = loader.result()
        except Exception as e:
            print(e)
            return
        
        with self.screen_switch_lock:
            target_frame = ui.Rect(*self.target_strategy(photo))
            new = ui.ImageView(
                border_width=4,
                border_color='white',
                frame=self.size_photo(photo, target_frame),
                content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
            new.center = target_frame.center()
            new.x += self.display.width
            new.image = ui.Image.from_data(photo_data)
            self.display.add_subview(new)
            set_shadow(new)
        
        @script
        def wait_and_fade(view):
            yield self.label_display_time
            hide(view)
        
        if self.prev_album != photo.album_id:
            album_name = self.albums[photo.album_id].name
            label = ui.Label(
                text=album_name,
                frame=(
                    0, new.height-75,
                    new.width/2, 50),
                alignment=ui.ALIGN_CENTER,
                text_color='white',
                font=(self.label_font, 36),
                background_color=(0,0,0,0.5))
            new.add_subview(label)
            wait_and_fade(label)
            self.prev_album = photo.album_id
        
        self.transition(self.old, new, target_frame)
        yield
        self.display.remove_subview(self.old)
        self.old = new
    
    def layout(self):
        self.old.center = self.display.center
        
    def quadrant_targets(self, photo):
        aspect = photo.width/photo.height
        dw, dh = self.display.bounds.size
        q = self.quadrants
        if aspect > dw/dh:
            if sum(q[:2]) <= sum(q[2:]):
                self.update_use_count(range(0,2))
                return (0, 0, dw, dh/2)
            else:
                self.update_use_count(range(2,4))
                return (0, dh/2, dw, dh/2)
        elif aspect < (dw/2)/dh:
            if sum(q[0::2]) <= sum(q[1::2]):
                self.update_use_count(range(0, 4, 2))
                return (0, 0, dw/2, dh)
            else:
                self.update_use_count(range(1, 4, 2))
                return (dw/2, 0, dw/2, dh)
        else:
            i = q.index(min(q))
            self.update_use_count(range(i, i+1))
            return (
                (i%2) * dw/2,
                (i//2) * dh/2,
                dw/2, dh/2
            )
            
    def update_use_count(self, r):
        for i in r:
            self.quadrants[i] += 1            
    
    def size_photo(self, photo, target_frame):
        pw = photo['width']
        ph = photo['height']
        tf = target_frame.inset(20,20)
        tw = tf[2]
        th = tf[3]
        if pw/ph > tw/th:
            w = tw
            h = tw/pw*ph
        else:
            w = th/ph*pw
            h = th
        return (0, 0, w, h)
        
    def update_spec(self, photo_spec, offset):
        album_id, photo_index = photo_spec
        album = self.albums[album_id]
        index_actual = photo_index + offset
        while index_actual >= len(album.photos):
            index_actual -= len(album.photos)
            album_id_list = list(map(
                lambda a: a[0],
                sorted(filter(
                    lambda a: a[1]['active'],
                    self.albums.items()), 
                    key=lambda a: a[1]['name'])))
            #album_id_list = list(self.albums).sort(key=lambda a: a['name'])
            album_index = album_id_list.index(album_id)
            next_album_index = (album_index + 1) % len(self.albums)
            album_id = album_id_list[next_album_index]
        return (album_id, index_actual)
        
    def locate_photo(self, photo_spec, offset=0):
        album_id, photo_index = self.update_spec(photo_spec, offset)
        album = self.albums[album_id]
        photo = album.photos[photo_index]
        return track(photo)
        
    @genr
    def load(self, photo):
        return self.driver.get_content(photo.id)

    def transition_appear(self, old, new, target_frame):
        new.center = target_frame.center()
        old.hidden = True
    
    @script    
    def transition_slide_and_fade(self, old, new, target_frame):
        self.display.image = snapshot(self.display)
        old.hidden = True
        jigger = self.position_jigger
        offset = (
            random.randint(-jigger, jigger),
            random.randint(-jigger, jigger))
        center(new, target_frame.center()+offset)
        jigger = self.rotation_jigger
        rotation = random.randint(-jigger, jigger)
        rotate(new, rotation)
        yield
        
    def refresh_album_data(self):
        albums = self.driver.get_albums()
        for i, album in enumerate(albums):
            album = track(album)
            #self.status.text = f'{i+1}/{len(albums)} - {album.name}'
            #self.status.size_to_fit()
            #self.status.center = #self.bounds.center()
            if album.id not in self.albums:
                photos = [{
                        'id': photo['id'],
                        'album_id': album.id,
                        #'name': photo['name'],
                        'taken': str(self.get_datetime(photo)),
                        #'size': photo['size'],
                        'height': photo['image']['height'],
                        'width': photo['image']['width'],
                        #'url': photo['@microsoft.graph.downloadUrl'],
                    }
                    for photo in self.driver.get_children(album.id)
                    if 'file' in photo and not 'video' in photo
                ]
                photos.sort(
                    key=lambda p: p['taken'])
                self.albums[album.id] = {
                    'name': album.name,
                    'id': album.id,
                    'active': True,
                    'photos': photos
                }
                self.menu.data_source.refresh()
            if self.state.current_photo is None:
                self.state.current_photo = (album.id, 0)
    
    def get_datetime(self, photo):
        try:
            if 'video' in photo['file']['mimeType']: return None
        except KeyError: pass
        try:
            return arrow.get(photo['photo']['takenDateTime'])
        except KeyError: pass
        try:
            return arrow.get(photo['name'][:15], 'YYYYMMDD_HHmmss')
        except arrow.parser.ParserError: pass
        try:
            return arrow.get(photo['fileSystemInfo']['createdDateTime'])
        except KeyError: pass
        
        raise Exception('Could not determine datetime for photo', photo)
            
            
class AlbumSource:
    
    symbol_active = sfsymbol.SymbolImage(
        'checkmark.circle.fill', 8, weight=sfsymbol.THIN)
    symbol_inactive = sfsymbol.SymbolImage(
        'circle', 8, weight=sfsymbol.THIN)

    def __init__(self, root, tableview):
        self.root = root
        self.tableview = tableview
        tableview.row_height = 40
        self.album_list = []
        self.refresh()
        
    def refresh(self):
        self.album_list = sorted(
            self.root.albums.values(),
            key=lambda a: a['name']
        )
        self.tableview.reload()
        
    def tableview_number_of_rows(self, tableview, section):
        return len(self.album_list)

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.selectable = False
        cell.background_color = (0,0,0,0.5)
        
        container = anchor.View(
          frame=cell.content_view.bounds, 
          flex='WH')
        cell.content_view.add_subview(container)
        
        def choose_album(sender):
            self.root.state.current_photo = (self.album_list[row]['id'], 0)
            self.root.show_and_hide_menu(None)
        
        label = anchor.Button(
            title=self.album_list[row]['name'],
            font=(self.root.label_font, 16),
            tint_color='white',
            alignment=ui.ALIGN_CENTER,
            action=choose_album,
        )
        container.add_subview(label)
        label.dock.leading()
        
        '''
        airplay_button = ui.Button(
            tint_color='white',
            background_color=(0,0,0,0.5),
            corner_radius=5,
            image=sfsymbol.SymbolImage(
                'airplayvideo', 8, weight=sfsymbol.THIN
            ),
        )
        '''
        def choose_symbol():
            return (self.symbol_active
                if self.album_list[row]['active']
                else self.symbol_inactive)
        
        def toggle_active(sender):
            self.album_list[row]['active'] = not self.album_list[row]['active']
            sender.image = choose_symbol()
        
        button = anchor.Button(
            tint_color='white',
            image=choose_symbol(),
            action=toggle_active
        )
        container.add_subview(button)
        button.dock.trailing()
        button.at.width == 40
        label.at.trailing == button.at.leading_padding

        return cell
        
        
def snapshot(view):
  with ui.ImageContext(view.width, view.height) as ctx:
    view.draw_snapshot()
    return ctx.get_image()
    
def set_shadow(view, color='black'):
    layer = view.objc_instance.layer()
    layer.setShadowOpacity_(0.8)
    layer.setShadowColor_(UIColor.colorWithRed_green_blue_alpha_(
        *ui.parse_color(color)).CGColor())
    layer.setShadowRadius_(10)
    #layer.setShadowOffset_(objc_util.CGSize(4, 4))

def fix_set_idle_timer_disabled(flag=True):
    return
    objc_util.on_main_thread(
        console.set_idle_timer_disabled)(flag)
                
slideshow = SlideShow(background_color='black')
slideshow.present(
    'fullscreen',
    hide_title_bar=True)
slideshow.start()

