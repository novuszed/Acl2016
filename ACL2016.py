__author__ = 'zihaozhu'
import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from socket import timeout
import re
import sqlite3
import sys
import os
import httplib2
import subprocess
import argparse
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyCE-6B_lFgOgVpsf-XAlLuKlVtk2ppiwh0"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search(options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(
    q=options.q,
    part="id,snippet",
    maxResults=options.max_results
  ).execute()

  videos = []
  channels = []
  playlists = []
  vidId=[]
  # Add each result to the appropriate list, and then display the lists of
  # matching videos, channels, and playlists.
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                 search_result["id"]["videoId"]))
      vidId.append("%s" %(search_result["id"]["videoId"]))
    elif search_result["id"]["kind"] == "youtube#channel":
      channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                   search_result["id"]["channelId"]))
    elif search_result["id"]["kind"] == "youtube#playlist":
      playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                    search_result["id"]["playlistId"]))

  #print ("Videos:\n", "\n".join(videos), "\n")
  #print ("Channels:\n", "\n".join(channels), "\n")
  #print ("Playlists:\n", "\n".join(playlists), "\n")
  #print(vidId)
  return vidId
def checkSite(link):
    try:
        page=urlopen(link)
        print("Page Opened Successfully")
    except urllib.error.HTTPError:
        print("Link error...Exiting now")
        return 0
    except urllib.error.URLError:
        print("Link error...Exiting now")
        return 0
    return 1
def pullNames(link):
    performers = set()
    page = urlopen(link)
    soup = bs(page.read(),"html.parser")
    artists = soup.find_all('div',class_="layout__item u-1-of-4-desk js-artist-wrap")
    for artist in artists:
        rows = artist.find_all('p')
        performerName = rows[0].text.strip()
        performers.add(performerName)
        #print("1: "+performerName)
    return performers
def say(text):
    subprocess.call('say '+text, shell=True)
def addVideos(youtube, videoID, playlistID):
    add_video_request=youtube.playlistItems().insert(
        part="snippet",
        body={'snippet':{
                'playlistId':playlistID,
                'resourceId':{
                    'kind':'youtube#video',
                    'videoId': videoID
                }
            }
    #'position':0
        }
    ).execute()
def authenService():
    CLIENT_SECRETS_FILE = "client_secrets.json"
    #display following message if file not found
    MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,message=MISSING_CLIENT_SECRETS_MESSAGE,scope=YOUTUBE_READ_WRITE_SCOPE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = argparser.parse_args()
        credentials = run_flow(flow, storage, flags)

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,http=credentials.authorize(httplib2.Http()))
    return youtube
def createPlayList(youtube):
    playlists_insert_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
        snippet=dict(
        title="ACL 2016",
        description="A playlist for ACL 2016 performers"
    ),
        status=dict(
        privacyStatus="private"
    )
  )
).execute()

    print ("New playlist id: %s" % playlists_insert_response["id"])
    return playlists_insert_response["id"]
def main():
    link ="http://www.aclfestival.com/lineup/interactive-lineup/"
    if(not checkSite(link)):
        print("Exiting...")
        exit(0)
    else:
        youtube = authenService()
        performers=sorted(pullNames(link))

    #searching up each performer on youtube
    #for names in performers:
    #    say("Playing %s" %(names))

    #below creates the playlist. I've stored the temporary key
    #playList=createPlayList(youtube)
    playList="PLxbEuEE__vnDthBF86MxrxV8AYDFFvupN"
    for names in performers:
        parser = argparse.ArgumentParser()
        parser.add_argument("--q", help="Search term", default="%s" % (names))
        parser.add_argument("--max-results", help="Max results", default=5)
        parser.add_argument("--order", help="Order", default="viewCount")
        args = parser.parse_args()

        try:
            vidId=youtube_search(args)
        except HttpError:
            print ("An HTTP error %d occurred...")
            exit(0)
        for Id in vidId:
            #print (Id)
            addVideos(youtube,Id,playList)

main()


