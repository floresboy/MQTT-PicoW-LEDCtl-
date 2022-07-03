import rp2
import network
import ubinascii
import machine
import time
import utime
from secrets import secrets
import socket
from umqtt.simple import MQTTClient
from machine import Pin

last_message = 0
message_interval = 5
counter = 0


button1 = Pin(16, Pin.IN)   #connect Button 1 on GP16

led1 = Pin(18, Pin.OUT)     #connect Led 1 on GP18
led2 = Pin(19, Pin.OUT)     #connect Led 2 on GP19
led3 = Pin(20, Pin.OUT)     #connect Led 3 on GP20
led4 = Pin(21, Pin.OUT)     #connect Led 4 on GP21

buz = Pin(17, Pin.OUT)      #connect Buzzer 4 on GP17


#
# Set country to avoid possible errors / https://randomnerdtutorials.com/micropython-mqtt-esp32-esp8266/
rp2.country('NL')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
print('mac = ' + mac)

# Other things to query
print(wlan.config('channel'))
print(wlan.config('essid'))
print(wlan.config('txpower'))

# Load login data from different file for safety reasons
ssid = secrets['ssid']
pw = secrets['pw']
broker = secrets['broker']
sub_topic = secrets['subtopic']
pub_topic = secrets['pubtopic']
#client_id = ubinascii.hexlify(machine.unique_id())
#client_id = mac
client_id = secrets['client_id']

wlan.connect(ssid, pw)

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)
    
# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth
if wlan.status() != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    led = machine.Pin('LED', machine.Pin.OUT)
    for i in range(wlan.status()):
        led.on()
        time.sleep(.1)
        led.off()
    print('Connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    
### Topic Setup ###

def sub_cb(topic, msg):
  print((topic, msg))
  if msg == b'LEDon':
    print('Device received LEDon message on subscribed topic')
    led.value(1)
  if msg == b'LEDoff':
    print('Device received LEDoff message on subscribed topic')
    led.value(0)
  if msg == b'ToggleLed1':
    print('Device received ToggleLed1 message on subscribed topic %s',topic)
    led1.toggle()


def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, broker)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(sub_topic)
  print('Connected to %s MQTT broker as client ID: %s, subscribed to %s topic' % (broker, client_id, sub_topic))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    client.check_msg()
    
    if button1.value() :
      print('Button 1 pressed!')
      utime.sleep(1)
      client.publish(pub_topic, 'Button1')
     
      
#    if (time.time() - last_message) > message_interval:
#      pub_msg = b'Hello #%d' % counter
#      client.publish(pub_topic, pub_msg)
#      last_message = time.time()
#      counter += 1
  except OSError as e:
    restart_and_reconnect()
