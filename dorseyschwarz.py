import time
import RPi.GPIO as GPIO
from twython import TwythonStreamer
from twython import Twython

from gpiozero import LED
from time import sleep

import requests
import json
from datetime import datetime
import random 

'''
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Project Name    :       dorseyschwarz
Description     :       Listens for specific hashtag at Twitter specified at `TERMS` variable
                        Blinks LED connected to Raspberry PI 3 and Phillips Hue lights 
                        Replies to twitter user
                        Posts activity log at a Slack channel
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''




#Reference : https://learn.sparkfun.com/tutorials/raspberry-pi-twitter-monitor/all
#Change log:
#       20200926 @bencarpena    :       Initial creation and deployment
#                               :       Features include controlling LED, Office Lights (Hue) and Slack log

# Search terms
TERMS = '#shhsPython'

# GPIO pin number of LED
led = LED(17)

# Twitter application authentication
APP_KEY = 'Twitter APP Key here'
APP_SECRET = 'Twitter APP Secret here'
OAUTH_TOKEN = 'Token'
OAUTH_TOKEN_SECRET = 'app-secret'


# FUNCTION : Setup callbacks from Twython Streamer
class BlinkyStreamer(TwythonStreamer):
        def on_success(self, data):
                if 'text' in data:
                        print (data['text'].encode('utf-8'))
                        print
                        ########### Turn ON lights ################
                        #0 Turn on LED alphacentauri
                        led.on()
                        ####Turn on Home Office Lights
                        #1 Office Light 1
                        url = "http://yourlocalip/api/Phillips-Hue-api-token/lights/8/state"
                        payload = "{\"on\":true, \"bri\":254}"
                        headers = {
                        'Content-Type': 'text/plain'
                        }
                        response = requests.request("PUT", url, headers=headers, data = payload)
                        #2 Office Light 2
                        url = "http://yourlocalip/api/Phillips-Hue-api-token/lights/9/state"
                        payload = "{\"on\":true, \"bri\":254}"
                        headers = {
                        'Content-Type': 'text/plain'
                        }
                        response = requests.request("PUT", url, headers=headers, data = payload)
                        ########### Post Log at Slack Channel #slackpy ################
                        dtstamp = datetime.now()
                        tweet = data['text'].encode('utf-8')
                        username = data['user']['screen_name']
                        slackmsg = data['user']['screen_name'] + ' | ' + str("@{}: {}".format(username, tweet))
                        slack_msg = {'text' : 'alphacentauri (dorseyschwarz) | ' + str(dtstamp) + ' | ' + str(slackmsg) }
                        webhook_url = 'https://hooks.slack.com/services/yourslackwebhook' 
                        requests.post(webhook_url, data=json.dumps(slack_msg))
                        sleep(2)
                        ########### Turn OFF lights again ################
                        #0 LED
                        led.off()
                         #1 Office Light 1
                        url = "http://yourlocalip/api/Phillips-Hue-api-token/lights/8/state"
                        payload = "{\"on\":false, \"bri\":254}"
                        headers = {
                        'Content-Type': 'text/plain'
                        }
                        response = requests.request("PUT", url, headers=headers, data = payload)
                        #2 Office Light 2
                        url = "http://yourlocalip/api/Phillips-Hue-api-token/lights/9/state"
                        payload = "{\"on\":false, \"bri\":254}"
                        headers = {
                        'Content-Type': 'text/plain'
                        }
                        response = requests.request("PUT", url, headers=headers, data = payload)
                        sleep(2)
                        ###################
                        #Post Tweet replies
                        reply_messages = [
                                "[Hashtag read] : You rock! Thank you and Good day! #PythonPower ",
                                "[Hashtag read] : Cool! Thank you and Good day! Keep learning #Python! ",
                                "[Hashtag read] : I am an automated #Python program hosted in a Raspberry Pi. Thank you and good day!",
                                "[Hashtag read] : I am a #Python-powered bot. Good day and thanks for the class participation!"
                        ]
                        name = data['user']
                        screen_name = name['screen_name']
                        twitter_handle = '@' + screen_name
                        message = twitter_handle + ' ' + random.choice(reply_messages)
                        twitter = Twython(
                                APP_KEY,
                                APP_SECRET,
                                OAUTH_TOKEN,
                                OAUTH_TOKEN_SECRET
                                )
                        twitter.update_status(status=message, in_reply_to_status_id=twitter_handle)
                        led.on()
                        sleep(3)
                        led.off()
                        print('Replied : ' + str(message))


# Create streamer
try:
        stream = BlinkyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        stream.statuses.filter(track=TERMS)
except KeyboardInterrupt:
        GPIO.cleanup()
