import os.path
import sys
from urllib.parse import urlparse
from pprint import pprint

import appex

import spoter
import spotify_ids

url = appex.get_url()
url = 'https://open.spotify.com/track/1ueOEwIxlCAivSC8ZrA5xW?si=UX8sqKi-RgeUk_Vn40-N1g'

playlist_name = sys.argv[1]

track_id = os.path.basename(urlparse(url).path)
print(track_id)

spot = spoter.Spoter(
    spotify_ids.client_id, spotify_ids.client_secret
)

print(spot.track(track_id))

the_playlist = None
playlists = spot.get_all('items', spot.user_playlists, limit=50)
for playlist in playlists:
    print(playlist['name'])
    if playlist['name'] == playlist_name:
        the_playlist = playlist
        break
else:
    print(f'Playlist {playlist_name} not found')
    
if the_playlist:
    pprint(the_playlist)
    positions = []
    for i, track in enumerate(spot.get_all('items', 
        spot.playlist_tracks, the_playlist, limit=50)):
        if track['track']['id'] == track_id:
            positions.append(i)
            
    spot.delete_tracks_from_playlist(the_playlist, [(track_id, positions)])
