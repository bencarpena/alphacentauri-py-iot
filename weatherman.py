'''
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Project name    :   Alphacentauri Temp + Humidity program
Description     :   Reads temp and humidity at my local area 
                :   and posts data/readings at Slack 
                :   and Cloud-based services (IoT Hub + Stream Analytics + Azure SQL DB)
@bencarpena     :   20190301 : 	initial codes created
                :   20190518 :  Added Slack feature
                :   20190727 :  Changed sensor to DHT from AM2302
                :   20200103 :  Added timestamp at each message and round half up sensor data
				:	20201219 :  Added MQTT and Azure IoT Hub integration
                :   20201226 :	Reformatted JSON payload to IoT Hub

Credits:

#SwitchDoc Labs May 2016

# MQTT personal notes:
https://onedrive.live.com/view.aspx?resid=BE42616FC86F2AB8%2119663&id=documents&wd=target%28IoT.one%7C2C2A8BC3-E1B8-2541-9366-F6F8E984C1BF%2FIntegrating%20MQTT%20and%20Azure%20IoT%20Hub%7CCB2F4618-D393-034D-95F5-04A5DFAE8239%2F%29

# ML and Sol Arch notes:
https://onedrive.live.com/view.aspx?resid=BE42616FC86F2AB8%2119663&id=documents&wd=target%28IoT.one%7C2C2A8BC3-E1B8-2541-9366-F6F8E984C1BF%2FWeather%20Forecasting%7CD10FD7FF-D1FF-E94C-B448-3282388C2EF1%2F%29

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''

#!/usr/bin/python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import sys

import Adafruit_DHT

import ssl, os
import requests
import json

from gpiozero import LED
from time import sleep
from datetime import datetime
import math

import RPi.GPIO as GPIO

from paho.mqtt import client as mqtt


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): 
			ssl._create_default_https_context = ssl._create_unverified_context

# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
    sensor = sensor_args[sys.argv[1]]
    pin = sys.argv[2]
else:
    print('Usage: sudo ./Adafruit_DHT.py [11|22|2302] <GPIO pin number>')
    print('Example: sudo ./Adafruit_DHT.py 2302 4 - Read from an AM2302 connected to GPIO pin #4')
    sys.exit(1)

# Try to grab a sensor reading.  Use the read_retry method which will retry up
# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

# Un-comment the line below to convert the temperature to Fahrenheit.
# temperature = temperature * 9/5.0 + 32

# Note that sometimes you won't get a reading and
# the results will be null (because Linux can't
# guarantee the timing of calls to read the sensor).
# If this happens try again!

try:
    if humidity is not None and temperature is not None:
        #20190727 @bencarpena : Added feature to turn on/off LED
        led = LED(17)
        led.on()
        
        def round_half_up(n, decimals=0):
            multiplier = 10 ** decimals
            return math.floor(n*multiplier + 0.5) / multiplier
        
        print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
        

        dtstamp = datetime.now()
        slack_msg = {'text' : 'alphacentauri (iothub bypass dht) | ' + str(dtstamp) + ' | Temperature : ' + str(round_half_up(temperature, 1)) + ' C | Humidity : ' + str(round_half_up(humidity, 1)) + ' %'}
        
        webhook_url = '<slack web hook token here>'

        #post to Slack
        requests.post(webhook_url, data=json.dumps(slack_msg))
        print ("Success : Posted data to Slack!")

        #20201226 : Updated to send JSON payload
        #slack_msg_mqtt = 'alphacentauri(iot/w01) | ' + str(dtstamp) + ' | Temperature : ' + str(round_half_up(temperature, 1)) + ' C | Humidity : ' + str(round_half_up(humidity, 1)) + ' %'
        slack_msg_mqtt = '{"iot_msg_from" : "alphacentauri(iot/w01)", "iot_dt" : "' + str(dtstamp) + '", "iot_rd" : "sensor = am2302 | Temperature = ' + str(round_half_up(temperature, 1)) + ' C | Humidity = ' + str(round_half_up(humidity, 1)) + ' %"}'

        # @bencarpena 20201219 : Send message to IoT Hub via MQTT
        # START : MQTT < #############################
        path_to_root_cert = "/path_to_cert/Baltimore.pem"
        device_id = "<your device id here>"
        sas_token = "<SharedAccessSignature here>"
        iot_hub_name = "<name of iot hub here>"


        def on_connect(client, userdata, flags, rc):
            print("alphacentauri (mode: iot/w01) connected with result code: " + str(rc))


        def on_disconnect(client, userdata, rc):
            print("alphacentauri (mode: iot/w01) disconnected with result code: " + str(rc))


        def on_publish(client, userdata, mid):
            print("alphacentauri (mode: iot/w01) sent message!")
            print("JSON payload sent: ", slack_msg_mqtt)


        def on_message(client, userdata, message):
            print("message received " ,str(message.payload.decode("utf-8")))
            print("message topic=",message.topic)
            print("message qos=",message.qos)
            print("message retain flag=",message.retain)

        def on_log(client, userdata, level, buf):
            print("log: ",buf)


        client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)
        client.on_message=on_message 
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_publish = on_publish

        client.username_pw_set(username=iot_hub_name+".azure-devices.net/" +
                            device_id + "/?api-version=2018-06-30", password=sas_token)

        client.tls_set(ca_certs=path_to_root_cert, certfile=None, keyfile=None,
                    cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        client.tls_insecure_set(False)

        client.connect(iot_hub_name+".azure-devices.net", port=8883)

        #start the loop
        client.loop_start() 

        #subscribe to topic
        client.subscribe("devices/" + device_id + "/messages/events/")

        #publish message
        client.publish("devices/" + device_id + "/messages/events/", slack_msg_mqtt, qos=1) 

        #give time to process subroutines
        sleep(5)

        #display log
        client.on_log=on_log


        #end the loop
        client.loop_stop()

        # END MQTT > #############################
    else:
        print('Failed to get reading. Try again!')


except:
    slack_msg = {'text' : 'alphacentauri (weather_man | iot/w01) : Exception occurred! ' + str(datetime.now())}
    requests.post(webhook_url, data=json.dumps(slack_msg))
    
    #Catch and print exception: 
    _exception = sys.exc_info()[0]
    print(_exception)
    #os.execv(__file__, sys.argv) 
finally:
   print("System " + str(datetime.now()) + " : Cleaning up GPIOs.") 
   #sys.exit(1)