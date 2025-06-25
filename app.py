### This is the full application with flask 

### IMPORT LIBRARIES ###
import os
import time
import base64
import spotipy
import hashlib
import requests
from datetime import datetime
from credentials import CLIENT_ID, SCOPE, REDIRECTURI,TOKEN_URL
from flask import Flask, request, session, redirect, render_template
from flask_session import Session

#################################################
#create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(20).hex()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = False
Session(app)
#################################################
### BEGIN FLASK PAGES ###

#Begin Page
@app.route('/')
def home():
    return render_template('index.html')

#################################################
#################################################
#SPLIT CHECK CALCULATOR
@app.route('/calc', methods=['GET', 'POST'])
def calc():
    if request.method == 'POST':
        eaters = int(request.form['eaters'])
        prices = [float(request.form[f'price_{i}']) for i in range(1, eaters + 1)]
        subtotal = sum(prices)
        sub = float(request.form['subtotal'])
        rtotal = float(request.form['total'])
        
        if subtotal != sub:
            return render_template('calc.html', error=f'Prices entered do not match subtotal on check. Calc-{subtotal} vs Check-{sub}',int = int)
        
        taxrate = ((rtotal - sub) / sub) * 100
        taxamt = rtotal - subtotal
        taxsplit = taxamt / eaters
        
        tip_percentage = float(request.form['tip']) / 100
        tipamount = subtotal * tip_percentage
        tipsplit = tipamount / eaters
        
        results = {
            'taxamt': round(taxamt, 2),
            'taxrate': round(taxrate, 2),
            'tipamount': round(tipamount, 2),
            'total_with_tip': round(rtotal + tipamount, 2),
            'splits': [round(price + tipsplit + taxsplit, 2) for price in prices]
        }
        
        return render_template('calc.html', results=results, eaters=eaters, int = int)

    return render_template('calc.html', eaters = None, int = int)

#################################################
### BEGIN PYTHON METHODS ###




#################################################
#################################################
#SPOTIFY MONTHLY PLAYLIST GENERATOR
#asks for authorization then redirects
@app.route('/login')
def login():
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
    session['code_verifier'] = code_verifier
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    print("Generated Code Verifier:", code_verifier)
    print("Generated Code Challenge:", code_challenge)
    print('')
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
    print("Authorization Code:", auth_code)
    if not auth_code:
        return "Authorization code not found in the callback URL.", 400
    
    code_verifier = session.get('code_verifier')
    print("Code Verifier:", code_verifier)
    if not code_verifier:
        return "Code verifier not found in session.",400
    print('')
    payload = {
        'grant_type':'authorization_code',
        'code':auth_code,
        'redirect_uri':REDIRECTURI,
        'client_id':CLIENT_ID,
        'code_verifier':code_verifier
    }
    print("Payload:", payload)
    token_headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    
    response = requests.post(TOKEN_URL,data=payload,headers=token_headers)
    if response.status_code != 200:
        return f"Failed to retrieve access token: {response.text}",400
    
    token_json = response.json()
    token_json['expires_at'] = time.time() + token_json['expires_in']
    session['token_info'] = token_json
    return redirect('/playlist')

@app.route('/playlist', methods=['GET','POST'])
def playlist():
    token_json = session['token_info']
    if not token_json:
        return redirect('/')
    
     # Handle form submission
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        print(f"Selected Month: {month}, Year: {year}")  # Debugging

        # Validate year input
        if not year.isdigit() or len(year) != 4:
            return "Invalid year. Please enter a valid year in YYYY format.", 400

        # Create the date string in the format YYYY-MM
        date = f"{year}-{month}"
        
        # Initialize Spotify client
        access_token = token_json.get('access_token')
        if not access_token:
            return "Access token not found in token information.", 400
        
        sp = spotipy.Spotify(auth=access_token)
        user = sp.current_user()
        username = user['display_name']
        userid = user['id']

        # Create and display the playlist
        playlisttitle, today = getDate(date)  # Pass the selected date
        playlistid = putAllTogether(today, playlisttitle, sp, userid)
        playlistname, songlist, listlen = displayplaylist(playlistid, sp)
        return render_template('playlist.html', songlist=songlist, user=username, playlist=playlistname, listlen=listlen)
    return render_template('playlist.html')
    

#Logout - Clears Session
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
#################################################
### BEGIN PYTHON METHODS ###

#Gets current month or year
def getDate(formdate):
    if not formdate:
        todaytime = datetime.fromtimestamp(time.time())
        playlisttitle = datetime.strftime(todaytime,'%B %Y') #Month YYYY
        today = datetime.strftime(todaytime, '%Y-%m') #YYYY-MM

        #Uncomment and change for specific Month and Year
        # playlisttitle = "January 2021"
        # today = "2021-01"
        
        return playlisttitle, today
    else:
        dateobj = datetime.strptime(formdate,'%Y-%m')
        playlisttitle = dateobj.strftime('%B %Y')
        return playlisttitle, formdate

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
        print('Saved no songs from that month')
    else:
        sp.playlist_add_items(playlistid,addtrackslist) #adds remainder of tracks that doesn't reach the 100 track limit (end of library)
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
    app.run(port=8888, debug = True)