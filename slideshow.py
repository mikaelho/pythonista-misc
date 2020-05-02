import os.path
import pathlib

import arrow
import requests

import ui
import objc_util

from tinysync import track
from scripter import *
from genr import genr

import onedriver
import onedrive_ids

    
class SlideShow(ui.View):
    
    def __init__(self, folder='~/Documents/slideshow', **kwargs):
        super().__init__(**kwargs)
        
        self.slide_delay = 5 # seconds
        
        self.driver = onedriver.OneDriver(
            onedrive_ids.client_id,
            onedrive_ids.client_secret)
            
        self.photo_index = 0
        self.loaders = {}

        self.folder = pathlib.Path(folder).expanduser()
        self.folder.mkdir(parents=True, exist_ok=True)
        
        self.status = ui.Label(
            text_color='white',
            alignment=ui.ALIGN_CENTER,
        )
        self.add_subview(self.status)
        
        self.iv = ui.ImageView(
            frame=self.bounds,
            flex='WH',
            content_mode=ui.CONTENT_SCALE_ASPECT_FIT,
            hidden=True)
        self.add_subview(self.iv)
        
    def start(self):
        self.initialize_local()
        self.run_slideshow()
        self.refresh_album_data()
    
    def initialize_local(self):
        self.albums = track({}, str(self.folder / 'slideshow_album_data'))
        self.state = track({
            'current_photo': None
        }, str(self.folder / 'slideshow_state'))
        self.continuum = {}
    
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
        '''
        photo_file = self.photo_full_path(photo)
        while not photo_file.exists() or photo_file.stat().st_size < photo.size:
            yield 0.3
        '''
        self.iv.image = ui.Image.from_data(loader.result())
        #self.iv.image = ui.Image(str(photo_file))
        self.iv.hidden = False
        yield
        
    def update_spec(self, photo_spec, offset):
        album_id, photo_index = photo_spec
        album = self.albums[album_id]
        index_actual = photo_index + offset
        while index_actual >= len(album.photos):
            index_actual -= len(album.photos)
            album_id_list = list(self.albums)
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
        #result = requests.get(photo.url)
        return self.driver.get_content(photo.id)
        
        '''
        photo_file = self.photo_full_path(photo)
        with photo_file.open('wb') as fp:
            fp.write(
                self.driver.get_content(photo.id))
        '''
    
    '''        
    def photo_full_path(self, photo):
        return self.folder / f'{photo.id}{pathlib.Path(photo.name).suffix}'
    '''
    
    def refresh_album_data(self):
        albums = self.driver.get_albums()
        for i, album in enumerate(albums):
            album = track(album)
            self.status.text = f'{i+1}/{len(albums)} - {album.name}'
            self.status.size_to_fit()
            self.status.center = self.bounds.center()
            if album.id not in self.albums:
                photos = [{
                        'id': photo['id'],
                        'album_id': album.id,
                        'name': photo['name'],
                        'taken': str(self.get_datetime(photo)),
                        'size': photo['size'],
                        'url': photo['@microsoft.graph.downloadUrl'],
                    }
                    for photo in self.driver.get_children(album.id)
                    if 'file' in photo
                ]
                photos.sort(
                    key=lambda p: p['taken'])
                self.albums[album.id] = {
                    'name': album.name,
                    'photos': photos
                }
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
    
    def will_close(self):
        return
        for loader in self.loaders:
            loader.cancel()    

                
slideshow = SlideShow(background_color='black')
slideshow.present(
    'fullscreen',
    hide_title_bar=True,
    animated=False)
slideshow.start()

