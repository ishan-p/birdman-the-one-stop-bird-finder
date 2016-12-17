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
import requests
from Helpers import *
import random
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from lxml import etree
import re


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_type = 'Simple'
    card_title = 'BirdMan'
    directives = None

    speech_output = "Hi! Welcome to Bird Man. You can ask me to play any bird's call by specifying it's common name." \
                    " Or, you can explore the discover mode by asking me to discover bird life." \
                    " I can also tell you notable sightings of birds in any region. Happy birding!" 
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me a question like tell me about some bird, " \
                    "or ask to discover bird life."
    should_end_session = False
    card_content = "Examples - Ask BirdMan to play Bald Eagle," \
                   " ask Birdman to discover the bird life," \
                   " ask BirdMan to tell me about Penguin or" \
                   " ask BirdMan recent sightings in United States"
    card = generate_card(card_type, card_title, card_content)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session, directives, json.dumps(card)))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the bird man"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def unexpected_intent():
    card_title = "Session Ended"
    speech_output = "Coulnd't understand your request. Try bird man help"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_recorded_birds_attributes(recorded_birds, last_bird_details=0):
    return {"recorded_birds": recorded_birds, "last_bird_details": last_bird_details}


def play_bird_sound_intent(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    sound_file = None
    proxy_file = None
    directives = None

    card_type = 'Simple'
    card_title = 'Bird Call'
    card_image = None
    card = None

    if 'BirdName' in intent['slots']:
        #check if value for slot BirdName is received
        if 'value' in intent['slots']['BirdName']:
            bird_name = intent['slots']['BirdName']['value']
            # request to get bird call's mp3 file path
            response = play_call(bird_name)
            if response['card'] != None:
                card_title = response['card']['card_title']
                card_type = response['card']['card_type']
                card_content = response['card']['card_content']
                card_image = response['card']['card_image']
                card = generate_card(card_type, card_title, card_content, card_image)
            speech_output = response['speech_output']
            reprompt_text = response['reprompt_text']
            # set directiver for audio player
            directives = response['directives'] 
        else:
            speech_output = "I did not understand which bird's call do you want me to play."
            reprompt_text = "Which bird's call do you want me to play?"
            card_content = "Did not understand the bird name or couldn't find the recording"
    else:
        speech_output = "Tell any bird's name whose call you will like to listen or try discover mode."
        reprompt_text = "Try bird man help"
        card_content = "Did not understand the bird name or couldn't find the recording"

    if card == None:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    else:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session, directives, json.dumps(card)))


def create_bird_info_session_attributes(bird_name):
    return {"bird_name": bird_name}

def bird_info_intent(intent, session):
    session_attributes = {}
    should_end_session = True

    card_type = 'Simple'
    card_title = 'Bird Info'
    card_image = None
    directives = None
    card = None

    if 'BirdName' in intent['slots']:
        #check if value for slot BirdName is received
        if 'value' in intent['slots']['BirdName']:
            bird_name = intent['slots']['BirdName']['value']
            # request to get card and speech response
            response = get_bird_info(bird_name)
            should_end_session = response['should_end_session']
            session_attributes = response['session_attributes']
            speech_output = response['speech_output']
            reprompt_text = response['reprompt_text']
            if 'card_type' in response:
                card_type = response['card_type']
                card_title = response['card_title']
                card_content = response['card_content']
                card_image = response['card_image']
                card = generate_card(card_type, card_title, card_content, card_image)
            else:
                card = None
        else:
            speech_output = "Which bird are you interested in?"
            reprompt_text = "Which bird are you interested in?"
            card_content = "Did not understand the bird name or couldn't find any information."
    else:
        speech_output = "Which bird are you interested in?"
        reprompt_text = "Which bird are you interested in?"
        card_content = "Did not understand the bird name or couldn't find any information."

    if card == None:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    else:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session, directives, json.dumps(card)))


def extra_info_call(intent, session):
    #This is called if users wants to hear a call after listening to bird description
    session_attributes = {}
    reprompt_text = None
    should_end_session = False
    card_title = 'Bird Call'
    directives = None
    if 'Response' in intent['slots']:
        if 'value' in intent['slots']['Response']:
            response = intent['slots']['Response']['value'].lower()
            if response == 'no':
                return handle_session_end_request()
            elif response == 'yes':
                # get bird name from previous session
                if session.get('attributes', {}) and "bird_name" in session.get('attributes', {}):
                    bird_name = session['attributes']['bird_name']
                    response = play_call(bird_name)
                    session_attributes = response['session_attributes']
                    if response['card'] != None:
                        card_title = response['card']['card_title']
                    else:
                        card_title = None
                    speech_output = response['speech_output']
                    reprompt_text = response['reprompt_text']
                    should_end_session = response['should_end_session']
                    directives = response['directives']
                else:
                    return handle_session_end_request()
            else:
                return handle_session_end_request()
        else:
            speech_output = "Answer as yes or no"
    else:
        speech_output = "Answer as yes or no"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session, directives))


"""
TO DO - this function is not used yet
"""
def sighting_details(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "recorded_birds" in session.get('attributes', {}):
        recorded_birds = json.loads(session['attributes']['recorded_birds'])
        if "last_bird_details" in session.get('attributes', {}):
            index = session['attributes']['last_bird_details']
        else:
            index = 0
        session_attributes = create_recorded_birds_attributes(recorded_birds=json.dumps(recorded_birds), last_bird_details=1)
        if 'BirdName' in intent['slots']:
            data = None
            bird = intent['slots']['BirdName']['value']
            for i in recorded_birds:
                if bird == i['comName'].lower() or bird == i['sciName'].lower():
                    data = i
                    break
            if data:
                speech_output = data['comName'] + " was recorded at " + data['locName'] + " on " + data['obsDt']
                should_end_session = True
            else:
                speech_output = "I was not able to understand which bird. " + recorded_birds[index]['comName'] + " was recorded at " + recorded_birds[index]['locName'] + " on " + recorded_birds[index]['obsDt']
                should_end_session = False    
        else:
            speech_output = "I was not able to understand which bird. " + recorded_birds[index]['comName'] + " was recorded at " + recorded_birds[index]['locName'] + " on " + recorded_birds[index]['obsDt']
            should_end_session = False
    else:
        speech_output = "I'm not sure what you mean. You can ask about bird sightings at any location or any bird call"
        should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))
    

def get_notable_sightings(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('birdman_regions')
    card = None
    card_type = 'Simple'
    card_title = 'Notable Sightings'
    directives = None    

    if 'Region' in intent['slots']:
        region = (intent['slots']['Region']['value'])
        region = region.lower()
        print(region)
        # get the region code from dynamo db
        response = table.scan( FilterExpression=Attr('region').eq(region) )
        if response['Items']:
            region_code = response['Items'][0]['region_code']
            data = requests.get('http://ebird.org/ws1.1/data/notable/region/recent?r=%s&back=10&maxResults=10&locale=en_US&fmt=json'%(region_code))
            data = data.json()
            if data:
                session_attributes = create_recorded_birds_attributes(recorded_birds=json.dumps(data))
                random.shuffle(data)
                if len(data) >= 5:
                    speech_output = "The top 5 notable sightings recently recorded in %s include "%(region) + \
                                data[0]['comName'] + ", " + data[1]['comName'] + ", " + data[2]['comName'] + ", " + data[3]['comName'] + " and " + data[4]['comName']
                    card_content = speech_output
                if len(data) == 4:
                    speech_output = "The top 4 notable sightings recently recorded in %s include "%(region) + \
                                data[0]['comName'] + ", " + data[1]['comName'] + ", " + data[2]['comName'] + " and " + data[3]['comName']
                    card_content = speech_output
                if len(data) == 3:
                    speech_output = "The top 3 notable sightings recently recorded in %s include "%(region) + \
                                data[0]['comName'] + ", " + data[1]['comName'] + " and " + data[2]['comName']
                    card_content = speech_output
                if len(data) == 2:
                    speech_output = "The top 2 notable sightings recently recorded in %s include "%(region) + \
                                data[0]['comName'] + " and " + data[1]['comName']
                    card_content = speech_output
                if len(data) == 1:
                    speech_output = "The notable sighting recently recorded in %s is "%(region) + \
                                data[0]['comName']
                    card_content = speech_output

                card = generate_card(card_type, card_title, card_content)
                reprompt_text = "Are you interested in finding them? Gottcha find the all!"
            else:
                speech_output = "Sorry couldn't find any sightings in this region"
                reprompt_text = "Discover birdlife with bird man"               
        else:
                speech_output = "Sorry couldn't find the region you are interested in"
                reprompt_text = None
    else:
        speech_output = "I'm not sure which region you are considering "
        reprompt_text = "I'm not sure which region you are considering" \
                        "You can tell me the region you are interested"
    if card == None:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    else:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session, directives, json.dumps(card)))


def discover(intent=None, session=None, loop_flag=None):
    index = random.randint(1, 10865)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('bird_taxa')
    response = table.scan( FilterExpression=Attr('id').eq(index) )
    
    bird_name = response['Items'][0]['common_name']
    directives = None
    response = get_bird_info(bird_name)
    should_end_session = False
    session_attributes = response['session_attributes']
    if loop_flag == 1:
        speech_output = response['speech_output']
    else:
        speech_output = "Welcome to discover mode. You can loop through by saying next or ask to stop. " + response['speech_output']
    reprompt_text = response['reprompt_text']
    if 'card_type' in response:
        card_type = response['card_type']
        card_title = response['card_title']
        card_content = response['card_content']
        card_image = response['card_image']
        card = generate_card(card_type, card_title, card_content, card_image)
    else:
        card = None

    if card == None:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    else:
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session, directives, json.dumps(card)))


def discover_next(intent=None, session=None):
    return discover(loop_flag=1)

def discover_stop(intent=None, session=None):
    return handle_session_end_request()
