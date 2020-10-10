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
Project Name    :       ledzeppelin
Description     :       Listens for specific hashtag at Twitter specified at `TERMS` variable
                        Switches on/off LED connected to Raspberry PI 3 and Phillips Hue lights 
                        Replies to twitter user
                        Posts activity log at a Slack channel
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''


#Change log:
#       20201006 @bencarpena    :       Initial creation and deployment

# Search terms
TERMS = '#ledzep2345'

# GPIO pin number of LED
led = LED(17)

# Twitter application authentication
APP_KEY = 'Twitter APP Key'
APP_SECRET = 'Twitter APP Secret'
OAUTH_TOKEN = 'xxxxx-Token'
OAUTH_TOKEN_SECRET = 'Token Secret'

def led_illuminate():
    ctr = 0
    while ctr <= 24:
        led.on()
        sleep(1.5)
        ctr += 1

# FUNCTION : Setup callbacks from Twython Streamer
class BlinkyStreamer(TwythonStreamer):
        def on_success(self, data):
                if 'text' in data:
                        print (data['text'].encode('utf-8'))
                        print
                        tweetcommand = str(data['text'].encode('utf-8'))
                        ########### Get Operator and Execute ##################
                        tweetoperator = int(tweetcommand.find('illuminate'))
                        if tweetoperator != -1:
                            led.on()
                            tweetaction = 'ILLUMINATE'
                            #Office Light 1
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
                        else:
                            led.off()
                            tweetaction = 'DELUMINATE'
                            #Office Light 1
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
                         ########### Post Log at Slack Channel #slackpy ################
                        dtstamp = datetime.now()
                        tweet = data['text'].encode('utf-8')
                        username = data['user']['screen_name']
                        slackmsg = data['user']['screen_name'] + ' | ' + str("@{}: {}".format(username, tweet))
                        slack_msg = {'text' : 'alphacentauri (ledzeppelin) | ACTION : ' + str(tweetaction) + ' CODE : ' + str(tweetoperator) +  ' | ' + str(dtstamp) + ' | ' + str(slackmsg) }
                        webhook_url = 'https://hooks.slack.com/services/yourslackwebhookhere'
                        requests.post(webhook_url, data=json.dumps(slack_msg))
                        sleep(2)
                        ###################
                        #Post Tweet replies
                        reply_messages = [
                                "[ledzeppelin routine] : Action executed!  " + str(tweetaction) + ' code: ' + str(tweetoperator),
                                "[ledzeppelin routine] : Done master! " + str(tweetaction) + ' code: ' + str(tweetoperator),
                                "[ledzeppelin routine] : I obey. " + str(tweetaction) + ' code: ' + str(tweetoperator), 
                                "[ledzeppelin routine] : Wish granted! " + str(tweetaction) + ' code: ' + str(tweetoperator)
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
                        print('Replied : ' + str(message))
                        if tweetoperator != -1:
                            led_illuminate()
                        else:
                            led.off()





# Create streamer
try:
        stream = BlinkyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        stream.statuses.filter(track=TERMS)
except KeyboardInterrupt:
        GPIO.cleanup()
