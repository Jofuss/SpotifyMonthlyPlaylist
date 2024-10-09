### This is the full application with flask

### IMPORT LIBRARIES ###
import os
import time
import base64
import spotipy
import hashlib
import requests
from datetime import datetime
from important import CLIENT_ID, SCOPE, REDIRECTURI,TOKEN_URL
from flask import Flask, request, session, redirect, render_template

#################################################
#create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(20).hex()

#################################################
### BEGIN FLASK PAGES ###

#Begin Page
@app.route('/')
def home():
    return render_template('index.html')

#asks for authorization then redirects
@app.route('/login')
def login():
    code_verifer = os.urandom(32).hex()
    session['code_verifier'] = code_verifer
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifer.encode()).digest()
    ).decode().rstrip('=')
    
    auth_url = (
        f"https://accounts.spotify.com/authorize?response_type=code&"
        f"client_id={CLIENT_ID}&redirect_uri={REDIRECTURI}&"
        f"code_challenge={code_challenge}&code_challenge_method=S256&"
        f"scope={SCOPE}"
        )
    return redirect(auth_url)

#receives token
@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    code_verifier = session['code_verifier']
    
    payload = {
        'grant_type':'authorization_code',
        'code':auth_code,
        'redirect_uri':REDIRECTURI,
        'client_id':CLIENT_ID,
        'code_verifier':code_verifier
    }
    
    token_headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    
    response = requests.post(TOKEN_URL,data=payload,headers=token_headers)
    token_json = response.json()
    session['token_info'] = token_json
    return redirect('/playlist')

@app.route('/playlist')
def playlist():
    token_json = session['token_info']    
    access_token = token_json.get('access_token')
    if access_token:
        playlisttitle, today = getDate()
        sp = spotipy.Spotify(auth=access_token)
        user = sp.current_user()
        username = user['display_name']
        userid = user['id']
        
        playlistid = putAllTogether(today,playlisttitle, sp, userid)
        playlist, songlist, listlen = displayplaylist(playlistid, sp)
        return render_template('playlist.html',songlist=songlist,user=username,playlist=playlist,listlen=listlen)
    else:
        return f'error:{token_json}'

#################################################
### BEGIN PYTHON METHODS ###

#Gets current month or year
def getDate():
    todaytime = datetime.fromtimestamp(time.time())
    playlisttitle = datetime.strftime(todaytime,'%B %Y') #Month YYYY
    today = datetime.strftime(todaytime, '%Y-%m') #YYYY-MM

    #Uncomment and change for specific Month and Year
    # playlisttitle = "January 2021"
    # today = "2021-01"
    
    return playlisttitle, today

def getSavedTracks(offset, sp):
    savedtracks = sp.current_user_saved_tracks(limit=50,offset=offset) #api limits 50 songs per call
    items = savedtracks['items'] #go deeper into dict, makes while-loop easier
    
    return items
    

def putAllTogether(today,playlisttitle, sp, userid):
    #create playlist
    newplaylist = sp.user_playlist_create(userid, playlisttitle, public=False)
    playlistid = newplaylist['id']
    
    #get all saved tracks
    offset = 0
    moretogo = True
    allsongs = []
    displayaddedsongs = []
    
    while moretogo == True:
        items = getSavedTracks(offset, sp)
        if items is None:
            moretogo = False
        elif len(items) < 50: #add remainder of songs that doesn't hit the api limit
            for song in items:
                allsongs.append(song)
            moretogo = False
        else: #add full api limit
            for song in items:
                allsongs.append(song)
            offset +=50
    
    addtrackslist = [] #list of all songs added (Title - Artist)
    i = 0
    while i < len(allsongs):
        #adjust date formatting
        strdate = allsongs[i]['added_at']
        shortdate = strdate[:len(strdate)-10]
        date = datetime.strptime(shortdate,'%Y-%m-%d').date() #YYYY-MM-DD
        monthadded = datetime.strftime(date, '%Y-%m') #YYYY-MM
        
        #date validation
        if monthadded == today:
            trackuri = allsongs[i]['track']['uri']
            addtrackslist.append(trackuri)
            displayaddedsongs.append(allsongs[i]['track']['name'] + " - " + allsongs[i]['track']['artists'][0]['name'])
            if len(addtrackslist) == 100:
                sp.playlist_add_items(playlistid, addtrackslist) #add full api limit
                addtrackslist = []
            i += 1
        else:
            i += 1
    if len(addtrackslist) == 0:
        print('Saved No songs from that month')
    else:
        sp.playlist_add_items(playlistid,addtrackslist) #adds remainder of tracks taht doesn't reach the 100 track limit (end of library)
    return playlistid

def displayplaylist(playlistid, sp):
    songs = []
    getplaylistname = sp.playlist(playlistid)
    playlistname = getplaylistname['name']
    gettracks = sp.playlist_items(playlistid)
    tracks = gettracks['items']
    
    while gettracks['next']:
        gettracks = sp.next(gettracks)
        tracks.extend(gettracks['items'])
        
    for track in tracks:
        title = str(track['track']['name'])
        artist = str(track['track']['artists'][0]['name'])
        songs.append(title + " - " + artist)
    
    listlen = len(songs)
    
    return playlistname, songs, listlen
    

if __name__ == "__main__":
    app.run(debug = True)