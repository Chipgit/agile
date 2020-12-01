![Test Image 7](https://github.com/Chipgit/agile/blob/master/inky1.jpg)



# agile
Display Future Octopus Agile Electricty Prices and Previous Usage and Cost. With a little weather add on.. 

# Octopus Agile Display

Octopus Agile Display displays future electricity prices and previous energy usage for people on the Octopus Agile Tariff - http://share.octopus.energy/pure-cliff-534


## Hardware Required

Raspberry Pi - Any Variant (Requires Network Connection) 
Pimoroni InkyWhat  - https://shop.pimoroni.com/products/inky-what?variant=13590497624147

## Software Required

Standard Raspbian Noobs installation. 
Required Python and SQLLite which are included in this build. 

I've set a user as pi and you should copy the files to  /home/pi/Agile

THe inkyWhat libraries - Retrieve on a command line with -  curl https://get.pimoroni.com/inky | bash

## Usage


There are only two Python Scripts required for this to work and you must set the variables in them. 

After that you can reboot and it should be happy. 
You can manually call the job from a command prompt with - python 3 /home/pi/Agile/inkydisplay.py 
Just remember that the time will be incorrect as it is should be called by the cron job every half hour. 

The store_prices.py will run at boot time and also at 4pm. It will create the Database if it does not exist and populate with the forthcoming prices. At 4pm it will wait until the prices are ready as sometimes they can be delayed. 

Retrieve your tariff, meter details and API key from https://octopus.energy/dashboard/developer/ 

Retrieve a weather API key from - https://openweathermap.org/api

store_prices.py - 
agile_tariff_code = 'E-1R-AGILE-18-02-21-D'

inkydisplay.py - 
agile_tariff_code = 'E-1R-AGILE-18-02-21-D'
agile_mpan = 'pan'
agile_serial = 'serial'
agile_api_key = 'apikey'
weatherapikey = 'from open weather api'
standing_charge = 21 (Currently 21p, can set as 0 if you don't want this added to daily usage)
utc_offset = 1  Recent changes suggest this is now now needed.

## Cron

Update cron (typing crontab -e) and add the following lines

@reboot sleep 1220; /usr/bin/python3 /home/pi/Agile/store_prices.py >> /home/pi/cron.log

*/30 * * * * sleep 20; /usr/bin/python3 /home/pi/Agile/inkydisplay.py >> /home/pi/Agile/error.log

05 16 * * * /usr/bin/python3 /home/pi/Agile/store_prices.py >> /home/pi/cron.log

## Considerations

Usage will not initially show on a fresh database, so don't panic! 
Although the code will pull the usage data -  to caluclate the cost it needs the prices. Previous prices can not be obtained via the API so the calulation will fail resulting in "---" showing. After a couple of days you will see you usage appear on the display. 
The database does not clean itself, and will grow, it is data overhead is relativly small though and should last many years and years. Feel free to simplete delete the database from the Agile folder and restart the device. The boot store_prices.py call will recreate it and get the current prices, but be aware of the above consideration regarding usage. 


## Contributing
Pull requests are welcome. I have no real idea what I am doing. 
