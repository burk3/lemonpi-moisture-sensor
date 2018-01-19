#!/usr/bin/env python
"""
This script assumes a moisture detector is connected to GPIO17 on a Raspberry Pi. Sensor is below:
http://a.co/21NN4yP

The moisture sensor is activated when removed from water or the moisture level reaches
below the threshold. When this happens an e-mail is sent.

**DEPENDENCIES:**
- Python `2.7.9`
- Raspbian GNU/Linux 8 (jessie)
```bash
$ sudo pip install python-dotenv
$ sudo pip install jinja2
$ sudo pip install adafruit-mcp3008
```

**Globally available as a script**
```bash
sudo -i
PROJECT_ROOT=/home/pi/Projects/moisture-sensor
ln -s $PROJECT_ROOT/app.py /usr/local/bin/moisture-sensor
chmod +x /usr/local/bin/moisture-sensor
exit
```

--------------------

**NOTE:** GPIO 2/3 are reserved for devices with hard-wired pull-ups.

**NOTE:** To use Amazon SES a TXT Record must be added to Namecheap's DNS Entries. Also, free-tier limits the FROM/TO to **verified** e-mails only. To send from `plantbot@my-domain.com`:

1. Create a catch-all redirect e-mail on namecheap and point it to gmail
2. Send verification e-mail to the above from the Amazon SES console
3. ???
4. Profit.

--------------------

To read specific moisture levels the sensor's analog signal must be used. Unfortunately, Raspberry PI doesn't support analog ootb so the following are needed:
- Adafruit MCP3008 (ADC): https://www.adafruit.com/product/856
- Half/Full breadboard: http://a.co/7MVedwJ
- Adafruit RPi cobbler: ~~https://www.adafruit.com/product/914~~ WRONG ONE

Adafruit provides an easy to use library to interact with the MCP3008 and get readings from its channels. Along with examples:
https://github.com/adafruit/Adafruit_Python_MCP3008

--------------------

**Wire up the MCP3008**
https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/mcp3008#wiring

NOTE: I used hardware SPI which needs to be enabled:
http://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/

--------------------

- See: https://www.modmypi.com/blog/raspberry-pi-plant-pot-moisture-sensor-via-analogue-signals
- Also: https://www.raspberrypi.org/forums/viewtopic.php?t=55754
- Also: https://www.raspberrypi-spy.co.uk/2013/10/analogue-sensors-on-the-raspberry-pi-using-an-mcp3008/
- Also: https://computers.tutsplus.com/tutorials/build-a-raspberry-pi-moisture-sensor-to-monitor-your-plants--mac-52875

--------------------

- [ ] **TODO:** better error handling for when device not found on configured GPIO#
- [ ] **TODO:** wrap `DigitalInputDevice` in a `MoistureSensor` class that exposes events like:
`on_moisture_loss`
- [ ] **TODO:** calibrate it to soil
- [ ] **TODO:** can we pull specific moisture levels? (See links below)
- [ ] **TODO:** upgrade to python 3?
- [ ] **TODO:** keep count of warnings. if reached threshold send an e-mail
- [ ] **TODO:** limit e-mails via configuration variables
"""
from __future__ import print_function

import os
import smtplib
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from colorama import Fore, Style
from gpiozero import DigitalInputDevice, SmoothedInputDevice
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

PWD_PATH = os.path.dirname( os.path.realpath( __file__ ) )
load_dotenv( os.path.join( PWD_PATH, '.env' ) )

POLLING_RATE = 0.5
CHANNEL = 0
SPI_PORT = 0
SPI_DEVICE = 0
MCP3008 = Adafruit_MCP3008.MCP3008( spi=SPI.SpiDev( SPI_PORT, SPI_DEVICE ) )

GPIO_PIN = int( os.getenv( 'GPIO_PIN' ) )
MOISTURE_SENSOR = DigitalInputDevice( GPIO_PIN )
LOSS_COUNT = 0
GAIN_COUNT = 0
MESSAGE_OBJ = MIMEMultipart( 'alternative' ) # contains text/plain and text/html

EMAIL_SUBJECT = str( os.getenv( 'EMAIL_SUBJECT' ) )
EMAIL_TMPL_FILENAME = str( os.getenv( 'EMAIL_TMPL_FILENAME' ) )

SMTP_HOST = str( os.getenv( 'SMTP_HOST' ) )
SMTP_PORT = int( os.getenv( 'SMTP_PORT' ) )
SMTP_USER = str( os.getenv( 'SMTP_USER' ) )
SMTP_PASS = str( os.getenv( 'SMTP_PASS' ) )
SMTP_FROM = str( os.getenv( 'SMTP_FROM' ) )
SMTP_TO = str( os.getenv( 'SMTP_TO' ) )

MESSAGE_OBJ[ 'Subject' ] = EMAIL_SUBJECT
MESSAGE_OBJ[ 'From' ] = SMTP_FROM
MESSAGE_OBJ[ 'To' ] = SMTP_TO

def load_email_content():
    env = Environment( loader=FileSystemLoader( PWD_PATH ), trim_blocks=True )
    msg = env.get_template( EMAIL_TMPL_FILENAME ).render()
    MESSAGE_OBJ.attach( MIMEText( msg, 'html', 'utf-8' ) )

def send_email():
    try:
        smtp_obj = smtplib.SMTP( SMTP_HOST, SMTP_PORT )
        smtp_obj.starttls()
        smtp_obj.login( SMTP_USER, SMTP_PASS )
        smtp_obj.sendmail( SMTP_FROM, SMTP_TO, MESSAGE_OBJ.as_string() )
        smtp_obj.quit()

        print( Fore.GREEN + 'Successfully sent email.' + Style.RESET_ALL )
    except smtplib.SMTPException:
        print( Fore.RED + 'ERROR: Unable to send email!' + Style.RESET_ALL )

def handle_moisture_gain():
    global GAIN_COUNT
    GAIN_COUNT += 1
    print(
        Fore.YELLOW + 'Moisture gain detected! (#' + str( GAIN_COUNT ) + ')' +
        Style.RESET_ALL
    )

def handle_moisture_loss():
    global LOSS_COUNT
    LOSS_COUNT += 1
    print(
        Fore.CYAN + 'Moisture loss detected! (#' + str( LOSS_COUNT ) + ')' +
        Style.RESET_ALL
    )
    # load_email_content()
    # send_email()

def main():
    MOISTURE_SENSOR.when_activated = handle_moisture_loss # led inactive on microcontroller
    MOISTURE_SENSOR.when_deactivated = handle_moisture_gain # led active on microcontroller

    try:
        raw_input(
            Fore.RESET + 'Press ' +
            Fore.YELLOW + 'ENTER ' +
            Fore.RESET + 'or ' +
            Fore.YELLOW + 'Ctrl + C ' +
            Fore.RESET + 'to exit' + "\n"
        )
    except ( KeyboardInterrupt, EOFError ):
        pass
    finally:
        MOISTURE_SENSOR.close()
        print( Fore.GREEN + 'Exiting...' + Style.RESET_ALL )

def mcp3008_main():
    prev_value = -1

    while True:
        value = MCP3008.read_adc( CHANNEL )

        if value != prev_value:
            print(
                'Value: ' + Fore.YELLOW + str( value ) +
                Fore.RESET
            )

        prev_value = value
        time.sleep( POLLING_RATE )

# main()
try:
    mcp3008_main()
except ( KeyboardInterrupt, EOFError ):
    pass
finally:
    print( Fore.GREEN + 'Exiting...' + Style.RESET_ALL )
