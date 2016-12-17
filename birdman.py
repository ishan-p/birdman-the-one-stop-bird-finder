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
from IntentHandlers import *
import json
# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to skill's intent handlers
    if intent_name == "GetNotableSpecies":
        return get_notable_sightings(intent, session)
    elif intent_name == "BirdSound":
        return play_bird_sound_intent(intent, session)
    elif intent_name == "BirdInfo":
        return bird_info_intent(intent, session)
    elif intent_name == "Discover":
        return discover(intent, session)
    elif intent_name == "DiscoverNext":
        return discover_next(intent, session)
    elif intent_name == "DiscoverStop":
        return discover_stop(intent, session)
    elif intent_name == "Help":
        return get_welcome_response()
    elif intent_name == "BinaryResponseQuestion":
        return extra_info_call(intent, session)
    elif intent_name == "KnowMoreAboutTheSighting":
        return sighting_details(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        return unexpected_intent()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return handle_session_end_request()
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print('Received event: ' + json.dumps(event['request'], indent=2))

    """
    Validate skill's application ID to prevent someone else from 
    configuring a skill that sends requests to this function.
    """
    if 'session' in event:
        if (event['session']['application']['applicationId'] != "amzn1.ask.skill.83d71d43-b26d-4a97-9d1d-45675a0ee893"):
            raise ValueError("Invalid Application ID")

        if event['session']['new']:
            on_session_started({'requestId': event['request']['requestId']},
                               event['session'])

        #Route the incoming request based on type (LaunchRequest, IntentRequest,etc.)
        if event['request']['type'] == "LaunchRequest":
            return on_launch(event['request'], event['session'])
        elif event['request']['type'] == "IntentRequest":
            return on_intent(event['request'], event['session'])
        elif event['request']['type'] == "SessionEndedRequest":
            return on_session_ended(event['request'], event['session'])
