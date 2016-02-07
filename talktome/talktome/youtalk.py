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
import subprocess
import shlex

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
import re

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

[scriptDir,scriptName]=os.path.split(__file__)
#outputDir=os.environ['HOME']+'/Downloads/Youtubes'
config.readfp(open('locals.cfg'))
outputDir = config.get('locations','outputDir')

def getCleanOutputName(info):
    name=info['title']
    name=youtube_dl.utils.sanitize_filename(name)
    name=name+'-'+info['id']+'.mp4'
    name=name.encode('utf-8')
    return name

def getYoutubeVideo(url,overwrite=False):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        info=ydl.extract_info(url,download=False)
        filename=getCleanOutputName(info)
        os.chdir(outputDir)
        print(filename)
        fullFilename=outputDir+'/'+filename
        doDownload=True
        if os.path.exists(filename):
            print('file '+filename+' exists in '+outputDir)
            if not overwrite:
                print('Not overwriting download')
                doDownload=False

        if doDownload:
            ydl.download([url])
            with open(filename+'.json','w') as fn:
                json.dump(info,fn)
            if not os.path.exists(filename):
                raise Exception('Expected downloaded video not found:\n'+filename)
        os.chdir(scriptDir)

    return fullFilename


def convertVideoToAudio(name,overwrite=False):
    targetFormat='mp3'
    filename=name.split('.')
    filename.pop()
    filename.append(targetFormat)
    filename='.'.join(filename)

    doConversion=True
    if os.path.exists(filename):
        print('file '+filename+' exists in '+outputDir)
        if not overwrite:
            print('Not overwriting audio')
            doConversion=False

    if doConversion:
        cmd='avconv -y -i "'+name.encode('utf-8')+'" -vn -f '+targetFormat+' "'+filename.encode('utf-8')+'"'
        print(cmd)
        subprocess.check_call(shlex.split(cmd))
        cmd='mp3gain -c -r "'+filename+'"'
        subprocess.check_call(shlex.split(cmd))

    return filename

def youtubeSearch(options):

    youtube = build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

    options.__setattr__('type','video')
    options.__setattr__('videoDuration','short')
    options.__setattr__('maxResults','50')
    options.__setattr__('publishedAfter','2010-01-01T00:00:00Z')

    # Call the search.list method to retrieve results associated with the
    # specified Freebase topic.
    search_response = youtube.search().list(
        q=options.query,
        maxResults=options.maxResults,
        type=options.type,
        videoDuration=options.videoDuration,
        part="id,snippet",
    ).execute()

    # Print the title and ID of each matching resource.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            url=VIDEO_WATCH_URL+search_result["id"]["videoId"]
            print( "%s (%s)" % (search_result["snippet"]["title"],url))
            name=getYoutubeVideo(url)
            audioName=convertVideoToAudio(name)

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
    runCmd=open(outputDir+'/cmd','w')
    runCmd.write(' '.join(args))
    runCmd.write('\n')
    runCmd.close()
    args = parse_args(args)
    #mid = get_topic_id(args)
    try:
        youtubeSearch(args)
    except HttpError, e:
        print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

    _logger.info("End of searching youtubes")

def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
