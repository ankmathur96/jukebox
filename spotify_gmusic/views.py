import urllib.parse
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
# from logic.util import *
client_id = '6846427bd95949cfa5b89ec4205d9606'
client_secret = 'fb0f8e63157146858d267dd0e93dffdd'
import random
def random_string(n):
	return ''.join([chr(random.randint(33,127)) for x in range(n)])
# Create your views here.
def index(request):
	return render(request, 'spotify_gmusic/index.html', {})

def authenticate(request):
	redirect_uri = settings.HOST_URL + reverse('transfer:process');
	print(redirect_uri)
	scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative'
	auth_url = 'https://accounts.spotify.com/authorize?'
	sid = random_string(16)
	auth_query = {'response_type' : 'code', 'client_id' : client_id, \
				'scope' : scope, 'redirect_uri' : redirect_uri, 'sid' : sid}
	auth_url += urllib.parse.urlencode(auth_query)
	print(auth_url)
	return HttpResponseRedirect(auth_url)

def process(request):
	print(request)
	return render(request, 'spotify_gmusic/process_auth.html')

