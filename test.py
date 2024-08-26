#Import Libraries
import spotipy
import time
from spotipy import SpotifyOAuth
from datetime import datetime
from credentials import CLIENT_ID,CLIENT_SECRET,SCOPE,REDIRECTURI,CACHE,SECRET_KEY,TOKEN_CODE

#gets today's date and converts to YYYY-MM and "Month YYYY"
def getDate():
    todaytime = datetime.fromtimestamp(time.time())
    playlisttitle = datetime.strftime(todaytime,'%B %Y') #Month YYYY
    today = datetime.strftime(todaytime, '%Y-%m') #YYYY-MM

    return playlisttitle, today

#assign parameters for authorization
def authorize():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(CLIENT_ID,CLIENT_SECRET,REDIRECTURI,scope=SCOPE,cache_path=CACHE))
    user = sp.current_user()
    userid = user['id']
    print(sp.playlist_tracks())
    return sp, userid

#get all playlists
def getAllPlaylists():
    playlists = sp.current_user_playlists()
    playlistitems = playlists['items']
    return playlistitems

#get ID of a playlist by name
def getPlaylistID(searchplaylistname):
    playlistitems = getAllPlaylists()
    searching = True
    i = 0
    while searching:
        playlisttitle = playlistitems[i]['name']
        if searchplaylistname == playlisttitle:
            playlistid = playlistitems[i]['id']
            searching = False
            return playlistid
        else:
            i += 1

#checks if playlist name exists (ex. June 2022)
def ifPlaylistExists(playlistitems, playlisttitle, userid):
    allplaylistnames = []
    i = 0
    while i < len(playlistitems):
        alreadyinplaylist = playlistitems[i]['name']
        allplaylistnames.append(alreadyinplaylist)
        i += 1
    if playlisttitle not in allplaylistnames:
        createPlaylist(userid, playlisttitle)
        playlistid = getPlaylistID(playlisttitle)
        return playlistid
    else:
        print(f"'{playlisttitle}' already created, will use that")
        playlistid = getPlaylistID(playlisttitle)
        return playlistid

#creates playlist if it does not exists (ex. June 2022)
def createPlaylist(userid, playlisttitle):
    sp.user_playlist_create(userid, playlisttitle, public=False)
    print('Created playlist: ' + playlisttitle)

#get saved tracks - sorts newest to oldest by default.... Thank god
def getSavedTracks(offset):
    savedtracks = sp.current_user_saved_tracks(limit=20, offset=offset) #api limits 20 songs per call
    items = savedtracks['items'] #go deeper into dict...makes while-loop easier
    return items

#get playlistID that matches current month and adds list of track uri's to that playlist
#api post limit is 100 tracks
def addtracks(playlistid, tracklist):
    sp.playlist_add_items(playlistid, tracklist)

#Main Loop
def putAllTogether(today,playlistid):
    offset = 0
    moretogo = True
    allsongs = []
    while moretogo == True:
        items = getSavedTracks(offset)
        if items is None:
            moretogo = False
            print("No items in saved library.")
        elif len(items) < 20: #add remainder of songs < next api call limit
            for song in items:
                allsongs.append(song)
            moretogo = False
        else:
            for song in items:
                allsongs.append(song)
            offset += 20
    
    addtrackslist = []
    i=0
    numofsongs = 0
    while i < len(allsongs):
        
        strdate = allsongs[i]['added_at']
        shortdate = strdate[:len(strdate)-10]
        date = datetime.strptime(shortdate, '%Y-%m-%d').date()
        monthadded = datetime.strftime(date, '%Y-%m') #YYYY-MM

        if monthadded == today:
            trackuri = allsongs[i]['track']['uri']
            addtrackslist.append(trackuri)
            numofsongs += 1
            if len(addtrackslist) == 100: #adding tracks api call limits 100 tracks at a time
                addtracks(playlistid, addtrackslist)
                addtrackslist = []
            i += 1
        else:
            i += 1
            
    addtracks(playlistid, addtrackslist) #adds remainder of tracks that doesn reach the 100 track limit (end of library)
    
    print('Number of tracks added: ' + str(numofsongs))
    print('Playlist "' + playlisttitle + '", is ready')

#Methods to run script
playlisttitle, today = getDate() #gets and formats dates
sp, userid = authorize() #creates and authorize tokens
playlistitems = getAllPlaylists() #gets name of all saved playlists
playlistid = ifPlaylistExists(playlistitems, playlisttitle, userid) #if month does not exist, create
putAllTogether(today,playlistid) #create specific month that was missed
