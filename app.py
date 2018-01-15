#!/usr/bin/python
"""
This script assumes a moisture detector is connected to GPIO17 on a Raspberry Pi. Sensor is below:
http://a.co/21NN4yP

The moisture sensor is activated when removed from water or the moisture level reaches
below the threshold. When this happens an e-mail is sent.

**DEPENDENCIES:**
- Python `2.7.9`
- Raspbian GNU/Linux 8 (jessie)
```bash
$ pip install python-dotenv --user
$ pip install jinja2 --user
```

--------------------

NOTE: GPIO 2/3 are reserved for devices with hard-wired pull-ups.

NOTE: To use Amazon SES a TXT Record must be added to Namecheap's DNS Entries. Also, free-tier
limits the FROM/TO to **verified** e-mails only. To send from `plantbot@my-domain.com`:

1. Create a catch-all redirect e-mail on namecheap and point it to gmail
2. Send verification e-mail to the above from the Amazon SES console
3. ???
4. Profit.

--------------------

- [ ] TODO: better error handling for when device not found on configured GPIO#
- [ ] TODO: wrap `DigitalInputDevice` in a `MoistureSensor` class that exposes events like:
`on_moisture_loss`
- [ ] TODO: calibrate it to soil
- [ ] TODO: can we pull specific moisture levels? (See links below)
- [ ] TODO: upgrade to python 3?

--------------------

See: https://www.modmypi.com/blog/raspberry-pi-plant-pot-moisture-sensor-via-analogue-signals

Also: https://www.raspberrypi.org/forums/viewtopic.php?t=55754

Also: https://www.raspberrypi-spy.co.uk/2013/10/analogue-sensors-on-the-raspberry-pi-using-an-mcp3008/
"""
from __future__ import print_function

import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from colorama import Fore, Style
from gpiozero import DigitalInputDevice
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

PWD_PATH = os.path.dirname( os.path.abspath( __file__ ) )
load_dotenv( os.path.join( PWD_PATH, '.env' ) )

GPIO_PIN = int( os.getenv( 'GPIO_PIN' ) )
MOISTURE_SENSOR = DigitalInputDevice( GPIO_PIN )
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

def handle_moisture_loss():
    print( Fore.YELLOW + 'Moisture loss detected!' + Style.RESET_ALL )
    load_email_content()
    send_email()

def main():
    if not MOISTURE_SENSOR.is_active:
        print(
            Fore.YELLOW + 'WARNING: There is no device active on specified GPIO: ' +
            Style.BRIGHT + str( GPIO_PIN ) +
            Style.RESET_ALL
        )

    MOISTURE_SENSOR.when_activated = handle_moisture_loss

    try:
        handle_moisture_loss()
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

main()
