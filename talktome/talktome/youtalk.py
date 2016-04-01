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
import glob
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn
import random
import datetime
import re

from talktome import segment
from talktome import audio as a
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
from features import mfcc
from features import logfbank
import scipy.io.wavfile as wav

[scriptDir,scriptName]=os.path.split(__file__)

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
apiConfig = ConfigParser.ConfigParser()
apiConfig.readfp(open('api_keys.cfg'))
DEVELOPER_KEY = apiConfig.get('google','youtubeDataKey')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
FREEBASE_SEARCH_URL = "https://www.googleapis.com/freebase/v1/search?%s"
VIDEO_WATCH_URL = "https://www.youtube.com/watch?v="
CONFIG_FILENAME='locals.cfg'
# youtube apis: https://developers.google.com/youtube/v3/docs/search/list

configOutput = ConfigParser.ConfigParser()
configOutput.readfp(open(CONFIG_FILENAME))
outputDir = configOutput.get('locations','outputDir')
audioTargetFormat='wav'

# size of a 1 s for 10 cepstral per sampling rate of 22050
seconds=10000
sr=22050
ncoefficients=50
#print('MB: {:.2f}'.format(np.array([1.]).nbytes*seconds*sr*ncoefficients/1024/1024))

def analyzeAudios():
    # librosa API reference: http://bmcfee.github.io/librosa/
    audioNumber=4
    filename=sorted(glob.glob(outputDir+'/*.'+audioTargetFormat))[audioNumber]
    print('"'+filename+'"')
    sys.exit(0)

    y,sr=librosa.load(filename)
    onsets=librosa.onset.onset_detect(y,sr)

    fileoutName=filename.replace('.'+audioTargetFormat,'.png')
    fileoutName='test.png'
    #%matplotlib inline
    seaborn.set(style='ticks')
    S = librosa.feature.melspectrogram(y,sr=sr,n_mels=128)
    log_S = librosa.logamplitude(S, ref_power=np.max)

    fig = plt.figure(figsize=(12,4))
    ax = fig.add_subplot(211)
    ax.contourf(log_S)
    plt.title('mel power spectrogram')

    #ax.annotate('$->$',xy=(2.,-1),xycoords='data',
    #xytext=(-150, -140), textcoords='offset points',
    #bbox=dict(boxstyle="round", fc="0.8"),
    #arrowprops=dict(arrowstyle="->",patchB=el, connectionstyle="angle,angleA=90,angleB=0,rad=10"),)

    ax = fig.add_subplot(212)
    ax.plot(onsets)
    #plt.colorbar(format='%+02.0f dB')
    plt.tight_layout()
    #plt.show()
    plt.savefig(fileoutName,format='png',dpi=900)
    print(fileoutName)

def _speechFeatures():
    
    filename=sorted(glob.glob(outputDir+'/*.'+audioTargetFormat))[2]
    (rate,sig) = wav.read(filename)

    sig = sig[0:(rate*10)]

    mfcc_feat = mfcc(sig,rate)
    fbank_feat = logfbank(sig,rate)
    print(fbank_feat[1:3,:])
    print(fbank_feat.shape)
    print(mfcc_feat.shape)

    fileoutName=filename.replace('.'+audioTargetFormat,'.png')
    fileoutName='test.png'
    print(fileoutName)
    fig = plt.figure(figsize=(12,4))
    ax = fig.add_subplot(211)
    ax.contourf(np.transpose(mfcc_feat))
    plt.tight_layout()

    ax = fig.add_subplot(212)
    mfcc_sum = np.sum(np.transpose(np.sqrt(mfcc_feat*mfcc_feat)),0)
    
    n=6
    mfcc_sum_ref = mfcc_sum[:]
    for i in range(len(mfcc_sum_ref)):
        minidx=max(0,i-int(n/2))
        maxidx=min(len(mfcc_sum_ref),i+(n-int(n/2)))
        mfcc_sum[i]=np.sum(mfcc_sum_ref[minidx:maxidx])/(maxidx-minidx)

    ax.plot(mfcc_sum)
    #ax.set_yscale('log')
    plt.tight_layout()

    plt.savefig(fileoutName,format='png',dpi=300)


def analyzeAudios2():
    filenames=sorted(glob.glob(outputDir+'/*.'+audioTargetFormat))
    for filename in filenames:
        for isuffix in ['harmonic','percussive','mfcc']:
            if re.search('\.'+isuffix+'\.'+audioTargetFormat+'$',filename):
                continue

        print(filename)
        y, sr = librosa.load(filename)

        #lenY=len(y)
        #idx1=min(int(20*sr),lenY)
        #idx2=min(int(24*sr),lenY)
        #y = y[idx1:idx2]

        #y_harmonic, y_percussive = librosa.effects.hpss(y)
        S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
        log_S = librosa.logamplitude(S, ref_power=np.max)

        seaborn.set(style='ticks')

        fileoutName=filename.replace('.'+audioTargetFormat,'.melpower.png')
        plt.figure(figsize=(12,4))
        librosa.display.specshow(log_S, sr=sr, x_axis='time', y_axis='mel')
        plt.title('mel power spectrogram')
        plt.colorbar(format='%+02.0f dB')
        plt.tight_layout()
        plt.savefig(fileoutName,format='png',dpi=300)


        # Next, we'll extract the top 13 Mel-frequency cepstral coefficients (MFCCs)
        mfcc        = librosa.feature.mfcc(S=log_S, n_mfcc=13)
        delta_mfcc  = librosa.feature.delta(mfcc)
        delta2_mfcc = librosa.feature.delta(mfcc, order=2)

        fileoutName=filename.replace('.'+audioTargetFormat,'.melcoeff.png')
        plt.figure(figsize=(12, 6))
        plt.subplot(3,1,1)
        librosa.display.specshow(mfcc)
        plt.ylabel('MFCC')
        plt.colorbar()
        plt.subplot(3,1,2)
        librosa.display.specshow(delta_mfcc)
        plt.ylabel('MFCC-$\Delta$')
        plt.colorbar()
        plt.subplot(3,1,3)
        librosa.display.specshow(delta2_mfcc, sr=sr, x_axis='time')
        plt.ylabel('MFCC-$\Delta^2$')
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(fileoutName,format='png',dpi=300)

        # For future use, we'll stack these together into one matrix
        M = np.vstack([mfcc, delta_mfcc, delta2_mfcc])


        #fileoutHarmonicName=filename.replace('.'+audioTargetFormat,'.harmonic.'+audioTargetFormat)
        #fileoutPercussiveName=filename.replace('.'+audioTargetFormat,'.percussive.'+audioTargetFormat)
        #S_harmonic   = librosa.feature.melspectrogram(y_harmonic, sr=sr)
        #S_percussive = librosa.feature.melspectrogram(y_percussive, sr=sr)
        #librosa.output.write_wav(fileoutHarmonicName,y_harmonic,sr)
        #librosa.output.write_wav(fileoutPercussiveName,y_percussive,sr)
        # # Convert to log scale (dB). We'll use the peak power as reference.
        # log_Sh = librosa.logamplitude(S_harmonic, ref_power=np.max)
        # log_Sp = librosa.logamplitude(S_percussive, ref_power=np.max)
        # plt.figure(figsize=(12,6))
        # plt.subplot(2,1,1)
        # librosa.display.specshow(log_Sh, sr=sr, y_axis='mel')
        # plt.title('mel power spectrogram (Harmonic)')
        # plt.colorbar(format='%+02.0f dB')
        # plt.subplot(2,1,2)
        # librosa.display.specshow(log_Sp, sr=sr, x_axis='time', y_axis='mel')
        # plt.title('mel power spectrogram (Percussive)')
        # plt.colorbar(format='%+02.0f dB')
        # plt.tight_layout()
        # #plt.show()
        # plt.savefig(fileoutName,format='png',dpi=300)

def getCleanOutputName(info):
    name=info['title']
    name=youtube_dl.utils.sanitize_filename(name)
    name=name+'-'+info['id']+'.mp4'
    name=name.encode('utf-8')
    return name

def getYoutubeVideo(url,options,overwrite=False):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        info=ydl.extract_info(url,download=False)
        filename=getCleanOutputName(info)

        if options.__contains__('tags'):
            haveTag=False
            tags=options.tags.replace(',','|')
            for itag in info['tags']:
                if re.search(tags,itag,re.IGNORECASE):
                    haveTag=True
            if not haveTag:
                print('warning: no tags found: '+tags)
                print('tags were:')
                print(', '.join(info['tags']))
                return None

        os.chdir(outputDir)
        try:
            fullFilename=outputDir+'/'+filename
        except:
            print('File name encoding issue with url: '+url)
            return None
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
    filename=name.split('.')
    filename.pop()
    filenameBase='.'.join(filename)
    filename=filenameBase+'.'+audioTargetFormat

    doConversion=True
    if os.path.exists(filename):
        print('file '+filename+' exists in '+outputDir)
        if not overwrite:
            print('Not overwriting audio')
            doConversion=False

    if doConversion:
        cmd='avconv -y -i "'+name.encode('utf-8')+'" -vn -f '+audioTargetFormat+' "'+filename.encode('utf-8')+'"'
        subprocess.check_call(shlex.split(cmd))
        #cmd='mp3gain -c -r "'+filename+'"'
        #subprocess.check_call(shlex.split(cmd))

    return filename

def _audiosProperties(options):
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIG_FILENAME))
    outputDir = config.get('locations','outputDir')
    dataDir = config.get('locations','dataDir')
    assert not os.path.isfile(dataDir),"I need a dir here, not a file: "+dataDir
    if not os.path.exists(dataDir):
        os.mkdir(dataDir)
    dataFileName = config.get('locations','dataFileName')
    fileOutName = dataDir+'/'+dataFileName
    hopLength = config.getint('audio','hopLength')
    talkMaxAutocorrStd = config.getfloat('audio','talkMaxAutocorrStd')
    talkMinAutocorrMean = config.getfloat('audio','talkMinAutocorrMean')
    talkMaxAutocorrMean = config.getfloat('audio','talkMaxAutocorrMean')
    filesProcessed = pd.read_pickle(fileOutName) if os.path.isfile(fileOutName) else pd.DataFrame()
    fileList = sorted(glob.glob(outputDir+'/*.'+audioTargetFormat))

    if options.addAudioProperties:
        doneFileList = [] if options.rebuildAudioProperties else filesProcessed['fileName'].values
        indexStart = len(doneFileList)
        fileList = list(set(fileList)-set(doneFileList))
        # # test code
        # randomSeed = config.getint('random','seed')
        # random.seed(randomSeed)
        # fileList = random.sample(fileList,3)
        # # end test code
        filesToProcess=pd.DataFrame()
        filesToProcess['fileName']=fileList
        filesToProcess.set_index(filesToProcess.index.values+indexStart,inplace=True)
        audioFeatures=['autocorrelationMean','autocorrelationStd',
        'hopLength','onsetEnv','tempo']
        for iFeature in audioFeatures:
            filesToProcess[iFeature]=np.nan

        for i in filesToProcess.index:
            name=filesToProcess.loc[i,'fileName']
            print(i,'Processing file: '+name)
            audio=a.Audio(name,hopLength=hopLength)
            audio.load()
            audio.setTempo(plot=True)
            filesToProcess.loc[i,'tempo']=audio.tempo
            filesToProcess.loc[i,'autocorrelationMean']=audio.autocorrelationMean
            filesToProcess.loc[i,'autocorrelationStd']=audio.autocorrelationStd
            filesToProcess.loc[i,'hopLength']=audio.hopLength
            filesToProcess.loc[i,'onsetEnv']=pd.Series(audio.onsetEnv).to_json()

        files = filesProcessed.append(filesToProcess)
        files.to_pickle(fileOutName)
        print('Created: '+fileOutName)

    elif options.readAudioProperties:
        filesProcessed['isTalk']=0
        for i in filesProcessed.index:
            onsetEnv=pd.read_json(filesProcessed.loc[i,'onsetEnv'],orient='index',dtype=float,typ='series')
            #if filesProcessed['autocorrelationStd'][i] <= talkMaxAutocorrStd and \
            #    filesProcessed['autocorrelationMean'][i] >= talkMinAutocorrMean and \
            #    filesProcessed['autocorrelationMean'][i] <= talkMaxAutocorrMean:
            #    filesProcessed['isTalk'][i]=1

        #selected = filesProcessed[filesProcessed['isTalk']==1]
        #for i in range(len(selected)):
        #    print(('vlc '+"'"+selected['fileName'].iloc[i]+"' &").replace('wav','mp4'))
        #    print('eog '+"'"+selected['fileName'].iloc[i]+".png' &")
        #    print('--------------------------------------------------------')
        print('Read: '+fileOutName)

def youtubeSearch(options):

    youtube = build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)
    configQuery = ConfigParser.ConfigParser()
    configQuery.readfp(open(CONFIG_FILENAME))

    optionList=[
    'part',
    'maxResults',
    'publishedAfter',
    'publishedBefore',
    'q',
    'safeSearch',
    'type',
    'videoDuration',
    'relevanceLanguage',
    'regionCode',
    'videoDimension',
    'videoDefinition',
    'eventType',
    ]

    for i in optionList:
        iv=configQuery.get('youtubeQuery',i)
        if iv!=None:
            options.__setattr__(i,iv)

    # https://developers.google.com/youtube/v3/docs/search/list
    # https://developers.google.com/apis-explorer/#search/youtube/youtube/v3/youtube.search.list

    dateFormat='%Y-%m-%dT00:00:00Z'
    startDate=datetime.datetime.strptime(options.publishedAfter,dateFormat)
    endDate=datetime.datetime.strptime(options.publishedBefore,dateFormat)
    idate=startDate

    while idate < endDate:
        options.__setattr__('publishedAfter',idate.strftime(dateFormat))
        idate+=datetime.timedelta(days=1)
        options.__setattr__('publishedBefore',idate.strftime(dateFormat))
        print('\nDownloading for publishedAfter: '+options.publishedAfter+' '+
        'publishedBefore: '+options.publishedBefore+'\n\n')

        search_response = youtube.search().list(
            part=options.part,
            maxResults=options.maxResults,
            publishedAfter=options.publishedAfter,
            publishedBefore=options.publishedBefore,
            q=options.q,
            safeSearch=options.safeSearch,
            type=options.type,
            videoDuration=options.videoDuration,
            relevanceLanguage=options.relevanceLanguage,
            regionCode=options.regionCode,
            videoDimension=options.videoDimension,
            videoDefinition=options.videoDefinition,
            eventType=options.eventType,
        ).execute()

        iv=configQuery.get('youtubeTags','tags')
        if iv!=None:
            options.__setattr__('tags',iv)

        # Print the title and ID of each matching resource.
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                url=VIDEO_WATCH_URL+search_result["id"]["videoId"]
                title=search_result["snippet"]["title"]
                print('\nTitle:\n')
                print( "%s (%s)\n" % (search_result["snippet"]["title"],url))

                try:
                    name=getYoutubeVideo(url,options)
                except:
                    name=None

                if name != None:
                    audioName=convertVideoToAudio(name)
            else:
                print("Not getting the video")
                print("id, kind: "+search_result["id"]["kind"])

def parse_args(args):
    """
    Parse command line parameters
    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`airgparse.Namespace`
    """
    parser = argparse.ArgumentParser(description="Machine learning lie detector")
    parser.add_argument('-v','--version',action='version',version='talktome {ver}'.format(ver=__version__))
    parser.add_argument("--q",help="Freebase search term")
    parser.add_argument("--maxResults",help="Max YouTube results")
    parser.add_argument("--type",help="YouTube result type")
    parser.add_argument("--addAudioProperties",action='store_true',help="Scans all wav files and adds properties of the new ones")
    parser.add_argument("--rebuildAudioProperties",action='store_true',help="Scans all wav files and rebuilds properties")
    parser.add_argument("--readAudioProperties",action='store_true',help="Reads audio properties previously built")

    return parser.parse_args(args)

def main(args):
    runCmd=open(outputDir+'/cmd','w+')
    runCmd.write(' '.join(args))
    runCmd.write('\n')
    runCmd.close()
    args = parse_args(args)
    return args

def searchTubes():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args=main(sys.argv[1:])
    try:
        youtubeSearch(args)
    except HttpError, e:
        print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    _logger.info("End of searching youtubes")

def analyzeTubes():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args=main(sys.argv[1:])
    analyzeAudios2()
    _logger.info("End of analyzing youtubes")

def speechFeatures():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args=main(sys.argv[1:])
    analyzeAudios()
    #_speechFeatures()
    _logger.info("End of analyzing youtubes")

def audiosProperties():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args=main(sys.argv[1:])
    _audiosProperties(args)
    _logger.info("Done with audiosProperties")

if __name__ == "__main__":
    print("Sorry, no main here")


