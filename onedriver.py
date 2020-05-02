#coding: utf-8

"""
Supports accessing OneDrive files, photos and photo albums.

Steps to get the client credentials:

1. Create an application at the following address (use a big screen for this):
    https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
2. Be sure to select "Applications from personal account" if you just want to
access your personal files as a consumer.
This option is hidden behind '...' on small mobile screens.
3. Give the application any name you want, e.g. 'Personal OneDrive access' and
select the last tenant option with "pesonal" in it.
4. Record the Client ID.
5. Go to the option for 'Credentials & secrets' (or similar). Create a new
Client Secret and copy it somewhere.
6. Create a file called `onedrive_ids.py` in an importable location.
7. In the file, record the client ID and secret like this:
    
    client_id = 'ABCD...'
    client_secret = 'DCBA...'

8. Just creating a OneDriver object checks that authetication works.    
9. First-time authentication opens a web browser for you to enter your
Microsoft/OneDrive credentials and approve access to your data. 
Further runs should not request anything unless you change the access
scopes.

Follows the OAuth2 flow as documented here:
    https://docs.microsoft.com/en-us/graph/auth-v2-user
"""

from functools import wraps
import itertools
import os.path
import threading
import time
from typing import Dict, Tuple, Sequence
from urllib.parse import urlencode, quote, unquote
import webbrowser

import bottle
import requests


List_of_Dicts = Sequence[Dict]


class OneDriver:
    
    graph_root = 'https://graph.microsoft.com/v1.0/me'
    files_root = f'{graph_root}/drive/root'
    item_endpoint = f'{graph_root}/drive/items'
    redirect_uri = 'http://localhost:8090/oauth2callback'
    auth_host = 'login.microsoftonline.com'
    auth_endpoint = f'/common/oauth2/v2.0/authorize'
    token_endpoint = f'/common/oauth2/v2.0/token'
    token_url = f'https://{auth_host}{token_endpoint}'    
            
    def __init__(self,
        client_id,
        client_secret,
        scope = 'offline_access files.readwrite user.read',
        refresh_token_file='~/Documents/onedrive_refresh_token',
        quiet=True):
        self.quiet = quiet
        self.access_token = None
        
        self.refresh_token_filename = os.path.expanduser(
            refresh_token_file+'_'+client_id)
        
        self.auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'response_mode': 'query',
            'scope': scope
        }
        self.auth_url = (f'https://{self.auth_host}{self.auth_endpoint}'
        f'?{urlencode(self.auth_params)}')
        self.token_params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': self.redirect_uri,
            'scope': scope
        }
        user_info = self.get(self.graph_root).json()
        self.user_id = user_info['id']
        self.magic_root = f'{self.graph_root}/drive/items/{self.user_id}!0'
        self.albums_endpoint = f'{self.magic_root}:/SkyDriveCache/Albums:/children'
            
    def get_access_token(self):
        if self.access_token is not None:
            return self.access_token
        try:
            with open(self.refresh_token_filename, 'r') as fp:
                refresh_token = fp.read()
            self.refresh(refresh_token)
            return self.access_token
        except FileNotFoundError:
            self.request_token()
            return self.access_token
        
    class AuthServer(bottle.ServerAdapter):
        server = None
    
        def run(self, handler):
            from wsgiref.simple_server import make_server, WSGIRequestHandler
            if self.quiet:
                class QuietHandler(WSGIRequestHandler):
                    def log_request(*args, **kw): pass
                self.options['handler_class'] = QuietHandler
            self.server = make_server(
                self.host, self.port,
                handler, **self.options)
            self.server.serve_forever()
    
        def stop(self):
            self.server.shutdown()
        
    def request_token(self):
        app = bottle.Bottle()
        
        @app.route('/oauth2callback')
        def index():
            code = bottle.request.query.code
            token_params = self.token_params.copy()
            token_params['code'] = code
            token_params['grant_type'] = 'authorization_code'
            success, result = self.actual_token_request(token_params)
            if success:
                return 'Authentication complete'
            else:
                return result
        
        server = OneDriver.AuthServer(port=8090)
        
        threading.Thread(
            group=None,
            target=app.run,
            name=None, args=(),
            kwargs={'server': server, 'quiet': self.quiet}
        ).start()
        
        time.sleep(1)
        
        try:
            webbrowser.open_new(self.auth_url)
            #vw = ui.WebView()
            #vw.present('fullscreen')
            #vw.load_url(self.auth_url)
            
            while self.access_token is None:
                time.sleep(0.1)
        finally:
            server.stop()
            #vw.close()
        
    def refresh(self, refresh_token):
        token_params = self.token_params.copy()
        token_params['refresh_token'] = refresh_token
        token_params['grant_type'] = 'refresh_token'
        success, result = self.actual_token_request(token_params)
        if success:
            return
        if result['error'] == 'invalid_grant':
            self.access_token = None
            os.remove(self.refresh_token_filename)
            raise FileNotFoundError('Need to log in again')
        raise Exception(f'OneDrive auth error - {result}')
        
    def actual_token_request(self, token_params):
        req = requests.post(self.token_url, data=token_params)
        result = req.json()
        if 'access_token' in result:
            with open(self.refresh_token_filename, 'w') as fp:
                fp.write(result['refresh_token'])
            self.access_token = result['access_token']
            return (True, result)
        return (False, result)
        
    def authenticated(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            headers = kwargs.setdefault('headers', {})
            
            headers['Authorization'] = 'Bearer ' + self.get_access_token()
            result = func(self, *args, **kwargs)
            
            if result.status_code < 400:
                return result
            
            if result.json()['error']['code'] == 'unauthenticated':
                self.access_token = None
                headers['Authorization'] = 'Bearer ' + self.get_access_token()
                result = func(self, *args, **kwargs)
                if result.status_code < 400:
                    return result
            raise Exception(
                f'Error in making a OneDrive request', result)
        return wrapper
            
    # Authenticated versions of request methods
    
    @authenticated
    def get(self, *args, **kwargs):
        return requests.get(*args, **kwargs)
        
    @authenticated
    def post(self, *args, **kwargs):
        return requests.post(*args, **kwargs)
        
    @authenticated
    def patch(self, *args, **kwargs):
        return requests.patch(*args, **kwargs)
        
    @authenticated
    def delete(self, *args, **kwargs):
        return requests.delete(*args, **kwargs)
        
    # Convenience wrapper
    
    def flexible_id(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            item_id = args[0]
            if type(item_id) is dict:
                item_id = item_id['id']
            return func(self, item_id, *args[1:], **kwargs)
        return wrapper
        
    # API
    
    # Single item manipulation
    
    @flexible_id
    def get_item(self, item_id) -> Dict:
        """
        Returns a dict describing the item.
        
        `item_id` can be either a item ID or a dict with an `id` item that is
        used instead.
        """
        return self.get(f'{self.item_endpoint}/{item_id}').json()
        
    def get_item_by_path(self, path):
        path = self.normalize_path(path)
        return self.get(f'{self.files_root}{path}').json()
        
    @flexible_id
    def get_content(self, item_id):
        return self.get(f'{self.item_endpoint}/{item_id}/content').content
        
    def get_content_by_path(self, path):
        path = self.normalize_path(path)
        return self.get(f'{self.files_root}{path}/content').content
        
    @flexible_id
    def move_item(self, item_id, to_folder_id):
        if type(to_folder_id) is dict:
            to_folder_id = to_folder_id['id']
        return self.patch(f'{self.item_endpoint}/{item_id}', data={
            'parentReference': {
                'id': to-folder-id
            },
        }).json()
        
    @flexible_id
    def delete_item(self, item_id):
        self.delete(f'{self.item_endpoint}/{item_id}')
        
    def get_folder(self, path='/', order_by=None) -> Tuple[List_of_Dicts, List_of_Dicts]:
        """
        Returns the contents of the given path (default is your OneDive root)
        as a `([folders], [files])` tuple.
        
        Interesting values per item:
            
            * name
            * id
            
        Interesting values for files:
            
            * @microsoft.graph.downloadUrl (direct download access)
            * size
            * file/mimeType
            * file/hashes/sha1Hash
            
        """
        
        path = self.normalize_path(path)
        
        order_parameter = '' if order_by is None else f'?$orderby={order_by}'
        
        url = f'{self.files_root}{path}/children{order_parameter}'
        
        result = self.get(url).json()['value']
        folders = [item for item in result if 'folder' in item]
        files = [item for item in result if 'file' in item]
        
        return folders, files
        
    def normalize_path(self, path):
        if not path.startswith('/'):
            path = '/'+ path
        path = (
            '' if len(path) == 1
            else f':{quote(path)}:'
        )
        return path
        
    def get_files(self, path, include_subfolders=False, info_callback=None):
        folders, files = self.get_folder(path)
        if include_subfolders:
            while len(folders) > 0:
                folder = folders.pop()
                path = unquote(folder['parentReference']['path'][len('/drive/root:'):])
                full_path = path + '/' + folder['name']
                subfolders, more_files = self.get_folder(full_path)
                if info_callback is not None:
                    info_callback(folder, full_path)
                folders.extend(subfolders)
                files.extend(more_files)
        return files
        
    def get_albums(self) -> List_of_Dicts:
        """
        Returns a list of dicts describing your photo albums.
        
        Interesting values per album:
            
            * name
            * id
            * createdDateTime
            * lastModifiedDateTime
            * bundle/childCount
            
        Albums are items, and their contents can be retrieved with
        `get_children`.
        
        Interesting values per photo in an album:
            
            * @microsoft.graph.downloadUrl (direct download access)
            * name
            * id
            * size
            * image/height, image/width
            * photo/takenDateTime
            * parentReference/path (actual location of photo)
        """
        return self.get(self.albums_endpoint).json() ['value']
        

        
    @flexible_id
    def get_children(self, item_id, order_by=None) -> List_of_Dicts:
        """
        Returns a list of dicts describing the children of a folder or an album.
        
        `item_id` can be either a item ID or a dict with an `id` item that is
        used instead.
        """
        
        order_parameter = '' if order_by is None else f'?$orderby={order_by}'
        
        url = f'{self.item_endpoint}/{item_id}/children{order_parameter}'
        
        result = self.get(url).json()
        return result['value']
        
    # Extra functions
    
    def deduplicate(self,
            root_path, decision_callback, 
            include_subfolders=True, 
            info_callback=None):
        files = self.get_files(
            root_path, 
            include_subfolders,
            info_callback)
        hashes_seen = dict()
        for file in files:
            file_hash = file['file']['hashes']['sha1Hash']
            prev_file = hashes_seen.setdefault(file_hash, file)
            if prev_file == file: continue
            try:
                to_delete = decision_callback(prev_file, file)
                if to_delete is not None:
                    self.delete_item(to_delete)
                    if to_delete == prev_file:
                        hashes_seen[file_hash] = file
            except StopIteration:
                break
        
        
if __name__ == '__main__':
    
    import onedrive_ids
    import logging
    
    driver = OneDriver(
        client_id=onedrive_ids.client_id,
        client_secret=onedrive_ids.client_secret
    )
    
    print('Root folder contents')
    print('--------------------')
    
    folders, files = driver.get_folder()
    
    print('Folders:')
    for folder in folders:
        print('-', folder['name'])
        
    print('Files:')
    for file in files:
        print('-', file['name'])
        
    print()
    print('File dict keys')
    print('--------------')
    for key in file:
        print('-', key)
        value = file[key]
        if type(value) is dict:
            for key2 in value:
                print('  -', key2)
        
    print()     
    print('Photo albums')
    print('------------')
    
    albums = driver.get_albums()
    for album in albums:
        print('-', album['name'])
