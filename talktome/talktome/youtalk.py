#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Help will be here :)
"""
from __future__ import division, print_function, absolute_import
from __future__ import unicode_literals

import argparse
import sys
import logging
import youtube_dl
import shutil
import os

from talktome import __version__

__author__ = "poijqwef"
__copyright__ = "poijqwef"
__license__ = "none"

_logger = logging.getLogger(__name__)

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import json
import urllib
import sys
import ConfigParser

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
config = ConfigParser.ConfigParser()
config.readfp(open('api_keys.cfg'))
DEVELOPER_KEY = config.get('google','youtubeDataKey')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
FREEBASE_SEARCH_URL = "https://www.googleapis.com/freebase/v1/search?%s"
VIDEO_WATCH_URL = "https://www.youtube.com/watch?v="
# youtube apis: https://developers.google.com/youtube/v3/docs/search/list

outputDir=os.environ['HOME']+'/Downloads/Youtubes'

def get_youtube_video(url):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        info=ydl.extract_info(url,download=False)
        title=info['title']
        id=info['id']
        filename=title+'-'+id+'.mp4'
        downloaded=ydl.download([url])
        if os.path.exists(filename):
            shutil.move(filename,outputDir+'/'+filename)
        else:
            raise Exception('Expected downloaded video not found')

    #ydl.add_default_info_extractors()
    #for i in sorted(dir(ydl)):
    #    print(i)
    #ydl._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
    #_logger.info("End of search")

          

def get_topic_id(options):

    freebase_params = dict(query=options.query,key=DEVELOPER_KEY)
    freebase_params['type']='video'
    freebase_params['videoDuration']='short'
    freebase_params['maxResults']=5
    freebase_params['publishedAfter']='2017-01-01T00:00:00Z'
    freebase_url = FREEBASE_SEARCH_URL % urllib.urlencode(freebase_params)
    freebase_response = json.loads(urllib.urlopen(freebase_url).read())

    if len(freebase_response["result"]) == 0:
        exit("No matching terms were found in Freebase.")

    results=freebase_response["result"]

    # Display the list of matching Freebase topics.
    mids = []
    index = 1
    print("The following topics were found:")
    for result in freebase_response["result"]:
        mids.append(result["mid"])
        print("  %2d. %s (%s)" % (index, result.get("name", "Unknown"),
            result.get("notable", {}).get("name", "Unknown")))
        index += 1

    # Display a prompt for the user to select a topic and return the topic ID
    # of the selected topic.
    mid = None
    while mid is None:
        index = raw_input("Enter a topic number to find related YouTube %ss: " %
            options.type)
        try:
            mid = mids[int(index) - 1]
        except ValueError:
            pass
    return mid

def youtube_search(mid, options):
    youtube = build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results associated with the
    # specified Freebase topic.
    search_response = youtube.search().list(
        topicId=mid,
        type=options.type,
        part="id,snippet",
        maxResults=options.max_results
    ).execute()

    # Print the title and ID of each matching resource.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            url=VIDEO_WATCH_URL+search_result["id"]["videoId"]
            print( "%s (%s)" % (search_result["snippet"]["title"],url))
            get_youtube_video(url)

        elif search_result["id"]["kind"] == "youtube#channel":
            print( "%s (%s)" % (search_result["snippet"]["title"],
              search_result["id"]["channelId"]))
        elif search_result["id"]["kind"] == "youtube#playlist":
            print( "%s (%s)" % (search_result["snippet"]["title"],
              search_result["id"]["playlistId"]))

def parse_args(args):
    """
    Parse command line parameters
    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`airgparse.Namespace`
    """
    parser = argparse.ArgumentParser(description="Machine learning lie detector")
    parser.add_argument('-v','--version',action='version',version='talktome {ver}'.format(ver=__version__))
    parser.add_argument("--query",required=True,help="Freebase search term")
    parser.add_argument("--max-results",help="Max YouTube results",default=25)
    parser.add_argument("--type",help="YouTube result type: video, playlist, or channel", default="channel")
    return parser.parse_args(args)

def main(args):
    args = parse_args(args)
    mid = get_topic_id(args)
    try:
        youtube_search(mid, args)
    except HttpError, e:
        print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    _logger.info("End of searching youtubes")

def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
