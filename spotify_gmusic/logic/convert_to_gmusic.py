import gmusicapi
from gmusicapi import Mobileclient
from spotifyInfo import playlist_map
import re
import sys
import datetime
import getpass
import time
import traceback
reload(sys)
sys.setdefaultencoding('UTF8')
# is t1 in t2 +- 1
def plusminus(t1, t2, delta):
    return t2 - delta < t1 and t1 < t2 + delta

def computeMatchHash(matches):
    sHash, counter = len(matches), 1
    for match in matches:
        sHash += (hash(match['title']) + hash(match['artist']) + hash(match['album'])) * counter
        counter += 1
    return sHash

def getUString(match, counter = None):
    start = ''
    if counter is not None:
        start = str(counter) + '. '
    return start + match['title'] + ' by ' + match['artist'] + ' - ' + \
            str(datetime.timedelta(milliseconds=int(match['durationMillis']))) + \
            ' - album: ' + match['album'] + '\n'

def canonicalizeArtist(a):
    return a.lower().strip()

def canonicalizeSong(delims, trackTitle):
    trackTitle = trackTitle.lower()
    canon = [x.decode('utf-8') if isinstance(x, str) else x \
                    for x in re.split(delims, trackTitle) if x != '' and x != ' ']
    feat = [u'featuring', u'Featuring', u'Feat', u'feat.']
    for i in range(len(canon)):
        if canon[i] in feat:
            canon[i] = u'feat'
    return canon

def presentOptions(originalSong, matches, matchHistory):
    options, counter = 'Could not make a definitive guess. For the following track: ' + originalSong + '\n', 1
    for match in matches:
        options += getUString(match, counter)
        counter += 1
    try:
        userin = raw_input(options.encode(sys.stdout.encoding))
        if userin != 'none':
            try:
                intuserin = int(userin)
                if intuserin > len(matches):
                    print 'invalid numerical input. Please try again.'
                    return presentOptions(originalSong, matches, matchHistory)
            except ValueError:
                print 'invalid string input. Please try again.'
                return presentOptions(originalSong, matches, matchHistory)
        matchHistory[(originalSong, computeMatchHash(matches))] = userin
        return userin
    except UnicodeEncodeError:
        for match in matches:
            print match['title']
        raise Exception()

def findMatch(results, song, duration, explicit_mode, matchHistory):
    tokens = song.split('~')
    songName, artistTokens = tokens[0], tokens[1]
    artists = [canonicalizeArtist(a.decode('utf-8')) if isinstance(a, str) else canonicalizeArtist(a) for a in artistTokens.split('|') if a != '' and a != ' ']
    delims = re.compile(ur'[-().\s\[\]]', flags=re.UNICODE)
    canonSong = canonicalizeSong(delims, songName)
    nameFilter = []
    for result in results:
        canonResult = canonicalizeSong(delims, result['track']['title'])
        shorter = canonSong if len(canonSong) < len(canonResult) else canonResult
        ismatch = True
        for elem in shorter:
            if elem not in canonResult:
                ismatch = False
        if ismatch:
            nameFilter.append((result['track'], canonResult))
    nameArtistFilter = []
    if len(nameFilter) > 0:
        for match in nameFilter:
            if canonicalizeArtist(match[0]['artist']) in artists:
                nameArtistFilter.append(match)
    # added the following because artist names are tough to standardize - don't want to risk nuking
    # the whole result list.
    if len(nameArtistFilter) == 0:
        finalMatches = nameFilter
    else:
        finalMatches = []
    if len(nameArtistFilter) > 0:
        for s in nameArtistFilter:
            if plusminus(int(s[0]['durationMillis']), duration, 3000):
                finalMatches.append(s)
    # this filter is potentially to costly.
    if len(finalMatches) == 0:
        finalMatches = nameArtistFilter
    preExplicit = list(finalMatches)
    if explicit_mode:
        for x in finalMatches:
            canon = x[1]
            if 'edited' in canon:
                finalMatches.remove(x)
    if len(finalMatches) == 0:
        finalMatches = preExplicit
    finalMatches = [x[0] for x in finalMatches]
    allartists = ''
    for artist in artists:
        allartists += artist + ','
    allartists = allartists[:-1]
    song = songName.decode('utf-8') + ' by ' + allartists.decode('utf-8') + ' - ' + str(datetime.timedelta(milliseconds=duration)) + '\n'
    matchHash = computeMatchHash(finalMatches)
    if (song, matchHash) in matchHistory:
        print 'no choice needed for ' + song + ' because you have already made a decision on this.'
        return None if matchHistory[(song, matchHash)] == 'none' else matchHistory[(song, matchHash)]
    if len(finalMatches) > 1:
        choice = presentOptions(song, finalMatches, matchHistory)
        if choice == 'none':
            return None
        else:
            return finalMatches[int(choice)-1]['nid']
    else:
        if len(finalMatches) == 0:
            return None
        return finalMatches[0]['nid']

api = Mobileclient()
errcount = 0
uname = raw_input('What is your Google username?\n')
pword = getpass.getpass('Please enter your password. If you have 2-factor enabled, you will need to create a app-specific password and enter that here.\n')
logged_in = api.login(uname, pword, Mobileclient.FROM_MAC_ADDRESS) #      qrwxkctezunyuuiq
del pword
if not logged_in:
    raise Exception('login failed')
else:
    print 'Login successful!'
y = ['yes', 'y', 'Yes', 'YES', 'Ye', 'ye', 'yeeeeeeee']
sModeYN = raw_input('Do you want to enable explicit mode (which, in cases of ambiguity, will select the explicit versions of songs.\n')
if sModeYN in y:
    explicit_mode = True
else:
    explicit_mode = False
print "If the program cannot uniquely determine which song to import, based on results," + \
      "it will present a list of options. To pick, just enter the number of the choice" + \
      "you want imported. If none of them properly match, just type in 'none'."
matchHistory = {}
for k in playlist_map:
    print '**********************************'
    print 'now importing ' + k
    print '**********************************'
    newPID = api.create_playlist(k)
    playlist_songs = playlist_map[k]
    for song in playlist_songs:
        special_char = song.find('\\')
        while special_char >= 0:
            song = song[:special_char] + song[special_char+1:]
            special_char = song.find('\\')
        sTokens = song.split('`')
        song, duration = sTokens[0], int(sTokens[1])
        results = api.search_all_access(song, 10)['song_hits']
        song_id = findMatch(results, song, duration, explicit_mode, matchHistory)
        if song_id is None:
            results = api.search_all_access(song.split('~')[0], 10)['song_hits']
            song_id = findMatch(results, song, duration, explicit_mode, matchHistory)
        if song_id is not None:
            if errcount >= 20:
                raise Exception('Too many errors have occurred - the server is not responding properly.')
            while errcount < 20:
                try:
                    api.add_songs_to_playlist(newPID, song_id)
                    break
                except gmusicapi.exceptions.CallFailure:
                    traceback.print_exc()
                    print
                    print 'was trying to look up ' + song
                    print 'it seems the api has failed to respond properly - waiting for some time.'
                    time.sleep(2)
                    errcount += 1
        else:
            print 'could not find ' + song

