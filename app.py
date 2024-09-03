### This is the full application with flask
### Things needed to be changed so it makes more sense

#Import Libraries
import spotipy
import time
import os
from spotipy import oauth2
from datetime import datetime
from flask import Flask, request, session, redirect, render_template
from credentials import CLIENT_ID,CLIENT_SECRET,SCOPE,REDIRECTURI


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(15).hex()

##################################################################
### FLASK PAGES ###

#index
@app.route("/")
def index():
    return render_template("index.html")

### authorizations ###

# authorization-code-flow Step 1. Have your application request authorization; 
# the user logs in and authorizes access
@app.route("/login")
def verify():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    sp_oauth = oauth2.SpotifyOAuth(CLIENT_ID, CLIENT_SECRET,REDIRECTURI,scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# authorization-code-flow Step 2.
# Have your application request refresh and access tokens;
# Spotify returns access and refresh tokens
@app.route("/callback")
def api_callback():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    sp_oauth = oauth2.SpotifyOAuth(CLIENT_ID, CLIENT_SECRET,REDIRECTURI,scope=SCOPE)
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    # Saving the access token along with all other token related info
    session["token_info"] = token_info

    return redirect("/go")

# authorization-code-flow Step 3.
# Use the access token to access the Spotify Web API;
# Spotify returns requested data
# main work
@app.route("/go")
def go():
    session['token_info'], authorized = get_token(session)
    session.modified = True
    if not authorized:
        return redirect('/')
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
        
    return redirect('/playlist')

#display page
@app.route('/playlist')
def playlist():
    playlisttitle, today = getDate() #gets and formats dates
    
    session['token_info'], authorized = get_token(session)
    session.modified = True
    if not authorized:
        return redirect('/')
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    user = sp.current_user()
    username = user['display_name']
    userid = user['id']
    
    #Methods to run script
    playlisttitle, today = getDate() #gets and formats dates
    playlistid = putAllTogether(today,playlisttitle, sp, userid) #create specific month that was missed
    playlist,songlist,listlen = displayplaylist(sp,playlistid)
    return render_template('playlist.html',songlist=songlist,user=username,date=playlist,listlen=listlen)

##################################################################

### DEFINITIONS ###

def displayplaylist(sp, playlistid):
    songs = []
    getplaylistname = sp.playlist(playlistid)
    playlistname = getplaylistname['name']
    trackresponse = sp.playlist_items(playlistid)
    tracks = trackresponse['items']
    while trackresponse['next']:
        trackresponse = sp.next(trackresponse)
        tracks.extend(trackresponse['items'])

    for track in tracks:
        title = str(track['track']['name'])
        artists = str(track['track']['artists'][0]['name'])
        songs.append(title +" - "+ artists)
    
    listlen = len(songs)
    
    return playlistname, songs, listlen

# Checks to see if token is valid and gets a new token if not
def get_token(session):
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_token_expired):
        # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
        sp_oauth = oauth2.SpotifyOAuth(CLIENT_ID, CLIENT_SECRET,REDIRECTURI,scope=SCOPE)
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid

#gets today's date and converts to YYYY-MM and "Month YYYY"
def getDate():
    todaytime = datetime.fromtimestamp(time.time())
    playlisttitle = datetime.strftime(todaytime,'%B %Y') #Month YYYY
    today = datetime.strftime(todaytime, '%Y-%m') #YYYY-MM

    #Uncomment and change for specific Month and Year
    # playlisttitle = "January 2021"
    # today = "2021-01"
    
    return playlisttitle, today

#get saved tracks - sorts newest to oldest by default.... Thank god
def getSavedTracks(offset, sp):
    savedtracks = sp.current_user_saved_tracks(limit=50, offset=offset) #api limits 50 songs per call
    items = savedtracks['items'] #go deeper into dict...makes while-loop easier
    return items

#Main Loop
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
            offset += 50
    
    addtrackslist = [] #list of all songs added (Title - Artist)
    i=0
    while i < len(allsongs):
        #adjust date formatting
        strdate = allsongs[i]['added_at']
        shortdate = strdate[:len(strdate)-10]
        date = datetime.strptime(shortdate, '%Y-%m-%d').date()
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
        print("Saved no songs from that month")
    else:
        sp.playlist_add_items(playlistid, addtrackslist) #adds remainder of tracks that doesn reach the 100 track limit (end of library)
            
    return playlistid

if __name__ == "__main__":
    app.run(debug=True)