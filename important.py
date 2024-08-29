###rename this file to credentials.py so app.py can import it

# CLIENT_ID=os.environ.get('CLIENT_ID')
CLIENT_ID='clientid'
# CLIENT_SECRET=os.environ.get('CLIENT_SECRET')
CLIENT_SECRET='clientscret'
SCOPE='user-library-read playlist-read-private playlist-modify-private'
CACHE='.spotipyoauthcache'
REDIRECTURI='http://anyurl.com/callback' #put your redirecturi in Spotify Developer settings!!
AUTH_URL='https://accounts.spotify.com/authorize'
TOKEN_URL='https://accounts.spotify.com/api/token'