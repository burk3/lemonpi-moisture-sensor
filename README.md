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