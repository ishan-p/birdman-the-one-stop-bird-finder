#    This file is a part of an app, BirdMan - The One Stop Bird Finder
#    It is an Alexa (Amazon) skill which uses public APIs provided by www.ebird.org, 
#    www.xeno-canto.org, www.iucnredlist.org and www.mediawiki.org to get required information
#    Copyright (C) 2016 Ishan Potbhare (ishanpotbhare@gmail.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
import json
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr
from lxml import etree
import re

# Status code to status mapping
IUCN_STATUS = {
    "DD" : "Data Deficient",
    "LC" : "Least Concern",
    "NT" : "Near Threatened",
    "VU" : "Vulnerable",
    "EN" : "Endangered",
    "CR" : "Critically Endangered",
    "EW" : "Extinct in the wild",
    "EX" : "Extinct",
    "NE" : "Not Evaluated",
    "CD" : "Conservation Dependent",
    "LR/lc" : "Lower Risk - Least Concern",
    "LR/nt" : "Lower Risk - Near Threatened",
    "LR/cd" : "Lower Risk - Conservation Dependent"
}



def build_speechlet_response(title, output, reprompt_text, should_end_session, directives=None, card=None):

    # Build the skill response
    if card != None:
        card = json.loads(card)

    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': card,
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        "directives": directives,
        'shouldEndSession': should_end_session
    }


def generate_card(card_type, card_title, card_content, card_image=None):
    card = {}
    card['type'] = card_type
    card['title'] = card_title
    if card_type == 'Simple':
        card['content'] = card_content
    else:
        card['text'] = card_content
    if card_image:
        card['image'] = {}
        card['image']['smallImageUrl'] = card_image
        card['image']['largeImageUrl'] = card_image
    return card

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def get_sci_name(bird_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('bird_taxa')
    bird_name = bird_name.lower()
    print(bird_name)
    response = table.scan( FilterExpression=Attr('common_name').eq(bird_name) )
    if response['Items']:
        sci_name = response['Items'][0]['sci_name']
    else:
        sci_name = None
    return sci_name

def verify_bird(bird_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('bird_taxa')
    bird_name = bird_name.lower()
    print(bird_name)
    response = table.scan( FilterExpression=Attr('common_name').eq(bird_name) )
    if response['Items']:
        status = True
    else:
        status = False
    return status

def get_card_content(bird_name):
    # Get description of the bird and image from wikipedia
    wiki_url = "https://en.wikipedia.org/w/api.php?action=opensearch&search=%s&limit=1&format=xml"%(bird_name)
    data = requests.get(wiki_url)
    root = etree.fromstring(data.content)
    card = {}
    card['title'] = bird_name
    card['description'] = 'Could not find the ' + bird_name
    card['image_url'] = 'https://s3.amazonaws.com/placeholder-image/placeholder.png'
    # parse the xml response
    if len(root[1]) >= 1:
        if len(root[1][0]) > 1:
            card['title'] = root[1][0][0].text
            # get scientific name from dynamo db
            sci_name = get_sci_name(bird_name)
            if sci_name != None:
                # iucn api call to get iucn status
                iucn_url = "http://apiv3.iucnredlist.org/api/v3/species/%s?token=9bb4facb6d23f48efbf424bb05c0c1ef1cf6f468393bc745d42179ac4aca5fee"%(sci_name)
                iucn = requests.get(iucn_url)
                iucn_data = iucn.json()
                if iucn_data['result']:
                    iucn_status = iucn_data['result'][0]['category']
                else:
                    iucn_status = ""
                if iucn_status in IUCN_STATUS:
                    iucn_status_long = IUCN_STATUS[iucn_status]
                else:
                    iucn_status_long = ""
                # get iucn web page for the specie
                iucn_url = "http://apiv3.iucnredlist.org/api/v3/weblink/%s"%(sci_name)
                iucn = requests.get(iucn_url)
                iucn_data = iucn.json()
                if iucn_data:
                    if 'rlurl' in iucn_data:
                        iucn_web_link = iucn_data['rlurl']
                    else:
                        iucn_web_link = ""
                else:
                    iucn_web_link = ""
                card['description'] = root[1][0][2].text + '\n' + 'IUCN Conservation Status - ' + iucn_status_long + " (" + iucn_status + ")" + " .\n For more info check - " + iucn_web_link
            else:
                card['description'] = root[1][0][2].text
            if len(root[1][0]) > 3:
                image = root[1][0][3].values()[0]
                temp = (image.replace("thumb/","",1)).split('/')
                card['image_url'] = "/".join(temp[:-1])
        else:
            card = None
    else:
        card = None
    return card



def play_call(bird_name):
    session_attributes = {}
    should_end_session = True
    sound_file = None
    proxy_file = None
    directives = None
    card_title = 'Bird Call'
    card = {}
    card['card_type'] = 'Simple'
    card['card_title'] = 'Bird Call'
    card['card_image'] = None
    card = None
    # request xeno-canto api with bird name
    data = requests.get('http://www.xeno-canto.org/api/2/recordings?query=%s'%(bird_name))
    data = data.json()
    if not data['recordings']:
        bird_name = bird_name.split()[-1]
        data = requests.get('http://www.xeno-canto.org/api/2/recordings?query=%s'%(bird_name))
        data = data.json()
    if data['recordings']:
        sound_file_temp = data['recordings'][0]['file']
        sound_file_ = requests.get(sound_file_temp)
        sound_file = sound_file_.url
        temp = sound_file.split('/')
        # the mp3 link provided by xeno-canto was http. So had to set up a proxy as alexa audio player dosen't support http
        proxy_file = 'https://sounds.toolz.shoptimize.in'
        for i in range (3, len(temp)):
            proxy_file = proxy_file + '/' + temp[i]
        speech_output = "Playing call for " + bird_name
        reprompt_text = None
 
        # generate directives for audio player
        directives = [
                {
                    "type": "AudioPlayer.Play",
                    "playBehavior": "REPLACE_ALL",
                    "audioItem": {
                    "stream": {
                    "token": "this-is-the-audio-token",
                    "url": proxy_file,
                    "offsetInMilliseconds": 0
                  }
                }
              }
            ]
        card_data = get_card_content(bird_name)
        if card_data != None:
            card = {}
            card['card_type'] = 'Standard'
            card['card_title'] = card_data['title']
            card['card_content'] = card_data['description']
            card['card_image'] = card_data['image_url']
    else:
        speech_output = "Sorry I could not find " + bird_name + "'s recording"
        reprompt_text = None
        card = None
        status = verify_bird(bird_name)
        if status == True:
            card_data = get_card_content(bird_name)
            if card_data != None:
                card = {}
                card['card_type'] = 'Standard'
                card['card_title'] = card_data['title']
                card['card_content'] = card_data['description']
                card['card_image'] = card_data['image_url']

    response = {}
    response['session_attributes'] = {}
    response['card'] = card
    response['speech_output'] = speech_output
    response['reprompt_text'] = reprompt_text
    response['should_end_session'] = should_end_session
    response['directives'] = directives

    return response

def create_bird_info_session_attributes(bird_name):
    return {"bird_name": bird_name}


def get_bird_info(bird_name):
    response = {}
    response['should_end_session'] = False
    response['session_attributes'] = create_bird_info_session_attributes(bird_name)
    card_data = get_card_content(bird_name)
    if card_data != None:
        response['speech_output'] = card_data['description'].split('\n')[0] + ". Would you like to listen it's call? Answer yes or no"
        response['reprompt_text'] = "do you want me to play it's call?"
        response['card_type'] = 'Standard'
        response['card_title'] = card_data['title']
        response['card_content'] = card_data['description']
        response['card_image'] = card_data['image_url']
    else:
        response['speech_output'] = 'Could not find the ' + bird_name
        response['reprompt_text'] = "Try birdman help."

    return response
