# Displays the details on the InkyWhat, run from Cron Every half hour on the hour
# CRONTAB - */30 * * * * sleep 20; /usr/bin/python3 /home/pi/Agile/inkydisplay.py >> /home/pi/Agile/error.log
# enter Octopus account details from Developer page
agile_tariff_code = 'E-1R-AGILE-18-02-21-D'
agile_mpan = 'xxxxxxxxxxxx'
agile_serial = 'xxxxxxxxxx'
agile_GAS_mpan = 'xxxxxxxxxxx'
agile_GAS_serial = 'xxxxxxxxx'
agile_api_key = 'sk_live_Exxxxxxxxxx'
weatherapikey = 'xxxxxxxxxxxxxx'
co_ord_lat = "51.509865"
co_ord_long = "-0.118092"
standing_charge = 21   # Electric Daily Standing charge in pence set as 0 if you don't want it including in daily consumption cost
standing_GAS_charge = 17.85   # Gas Daily Standing charge in pence set as 0 if you don't want it including in daily consumption cost
GAS_cost_kwh = 2.83
GAS_coeff = 1.02264


import os, requests, json, sqlite3, datetime, time 
from inky import InkyWHAT
from font_fredoka_one import FredokaOne 
from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, timezone

os.chdir("/home/pi/Agile")
conn = sqlite3.connect('octoprice.sqlite')
cur = conn.cursor()
inky_display = InkyWHAT("red")
inky_display.set_border(inky_display.BLACK)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# make an list of the next 30 hours of values
prices = []  
for offset in range(0, 60):  #30h = 60 segments
    min_offset = 30 * offset
    #the_now = datetime.datetime.now(datetime.timezone.utc)   #correction trying to fix BST
    the_now = datetime.datetime.now()
    now_plus_offset = the_now + datetime.timedelta(minutes=min_offset)
    the_year = now_plus_offset.year
    the_month = now_plus_offset.month
    the_hour = now_plus_offset.hour
    the_day = now_plus_offset.day
    if now_plus_offset.minute < 30:
        the_segment = 0
    else:
        the_segment = 1
    cur.execute("SELECT * FROM prices WHERE year=? AND month=? AND day=? AND hour=? AND segment=? LIMIT 1",
                (the_year, the_month, the_day, the_hour, the_segment))
    row = cur.fetchone()
    if row is None:
        prices.append(0) # we don't have that price yet!
    else:
        prices.append(row[5])

pricesonly = [i for i in prices[:48] if i != 0 ] # Removing Zero Prices with max 24hrs returned

# write Current Price
current_price = str("{0:.1f}".format(prices[0]))
draw.text((0,-3), (((str(datetime.datetime.now())[11:16])) + " Current Price"), inky_display.BLACK, ImageFont.truetype(FredokaOne, 15))
if float(current_price) > 15:
    draw.text((0,2), current_price + "p", inky_display.RED, ImageFont.truetype(FredokaOne, 60))
else:
    draw.text((0,2), current_price + "p", inky_display.BLACK, ImageFont.truetype(FredokaOne, 60))
 
# getting a list of the sum of the forthcoming 4 prices and finding cheapest 2 hour chunk
pricechunk = []   
for index, price in enumerate(pricesonly):
    if index < (len(pricesonly)-3):
        chunk=pricesonly[index]+pricesonly[index+1]+pricesonly[index+2]+pricesonly[index+3]
        pricechunk.append(chunk)
minimumchunk = min(pricechunk)

cheapestChunkIndexs = []
for index, chunk in enumerate(pricechunk):
    if (chunk == minimumchunk):
        cheapestChunkIndexs.append(index)

# printing cheapest chunk and time
min_offset = pricechunk.index(minimumchunk) * 30
#time_of_cheapest = the_now + datetime.timedelta(minutes=(min_offset+60))        #correction trying to fix BST
#end_time_of_cheapest = the_now + datetime.timedelta(minutes=(min_offset+180))   #correction trying to fix BST
time_of_cheapest = the_now + datetime.timedelta(minutes=(min_offset))  
end_time_of_cheapest = the_now + datetime.timedelta(minutes=(min_offset+120))
draw.text((0,74), "  Cheapest 2hrs - " + ("{0:.1f}".format((minimumchunk)/4)) + "p ave @ " + (str(time_of_cheapest.time())[0:5]) +  "-" + (str(end_time_of_cheapest.time())[0:5]), inky_display.BLACK, ImageFont.truetype(FredokaOne, 20))

# plot the graph
chart_base_loc = 300  # location of the bottom of the chart on screen in pixels
number_of_vals_to_display = 60 # 60 half hours = 30 hours
pixels_per_w = 7  # how many pixels 1/2 hour is worth
lowest_price_next_24h = min(i for i in prices if i != 0)
highest_price_next_24h = max(i for i in prices if i != 0)

if highest_price_next_24h > 25:  #plot the 35p graph with warning
    pixels_per_h = 3  # how many pixels 1p is worth if max is over 25p
else:
    pixels_per_h = 5  # how many pixels 1p is worth if max is less than 25p    

for i in range(0,number_of_vals_to_display):
    scaled_price = prices[i] * pixels_per_h 
    if prices[i] <= (lowest_price_next_24h + 2):   # if within 2p of the lowest price, display in black
        draw.rectangle(((pixels_per_w*i+30),chart_base_loc,(((pixels_per_w*i+30))-pixels_per_w),(chart_base_loc-scaled_price)),inky_display.BLACK)
    else:
        draw.rectangle(((pixels_per_w*i+30),chart_base_loc,(((pixels_per_w*i+30))-pixels_per_w),(chart_base_loc-scaled_price)),inky_display.RED)
    if prices[i] < 0 :   # negative pricing so set outline
        draw.rectangle(((pixels_per_w*i+30),chart_base_loc,(((pixels_per_w*i+30))-pixels_per_w),(chart_base_loc-(scaled_price*-1))),inky_display.BLACK)
        draw.rectangle(((pixels_per_w*i+30-2),chart_base_loc,(((pixels_per_w*i+30+2))-pixels_per_w),(chart_base_loc-(scaled_price*-1)+2)),inky_display.WHITE)
  
# drawing the frame over the graph
if highest_price_next_24h > 25:  #plot the 35p graph with warning
    pixels_per_h = 3  # how many pixels 1p is worth if max is over 25p
    ink_color = inky_display.BLACK
    font = ImageFont.truetype(FredokaOne, 12)
    draw.rectangle((23,285,480,285),ink_color)
    draw.rectangle((23,270,480,270),ink_color)
    draw.rectangle((23,240,480,240),ink_color)
    draw.rectangle((23,210,480,210),ink_color)
    draw.rectangle((23,195,480,195),ink_color)
    draw.rectangle((23,300,23,195),ink_color)
    draw.text((7,278), "5p", ink_color, font)
    draw.text((1,261), "10p", ink_color,font)
    draw.text((1,232), "20p", ink_color,font)
    draw.text((0,203), "30p", inky_display.RED, font)
    draw.text((0,188), "35p", inky_display.RED, font)
    draw.text((60,172), "WARNING - HIGH PEAK PRICES", inky_display.RED, ImageFont.truetype(FredokaOne, 20))
else:
    pixels_per_h = 5  # how many pixels 1p is worth if max is less than 25p
    ink_color = inky_display.BLACK
    font = ImageFont.truetype(FredokaOne, 12)
    draw.rectangle((23,275,480,275),ink_color)
    draw.rectangle((23,250,480,250),ink_color)
    draw.rectangle((23,200,480,200),ink_color)
    draw.rectangle((23,175,480,175),ink_color)
    draw.rectangle((23,300,23,175),ink_color)
    draw.text((7,268), "5p", ink_color, font)
    draw.text((1,241), "10p", ink_color,font)
    draw.text((0,193), "20p", inky_display.RED, font)
    draw.text((0,173), "25p", inky_display.RED, font)

# retriving useage and displaying cost
def updateUsageIntoTable(year, month, day, hour, segment, usage):
    try:
        sqliteConnection = sqlite3.connect('octoprice.sqlite')
        cursor = sqliteConnection.cursor()
        sql_update_usage = """UPDATE prices SET usage = ? where year = ? and month = ? and day = ? and hour = ? and segment = ?"""        
        data = (usage, year, month, day, hour, segment)
        cursor.execute(sql_update_usage, data)
        sqliteConnection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert Python variable into prices table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            
def updateGASUsageIntoTable(year, month, day, hour, segment, gasusage):
    try:
        sqliteConnection = sqlite3.connect('octoprice.sqlite')
        cursor = sqliteConnection.cursor()
        sql_update_usage = """UPDATE prices SET gasusage = ? where year = ? and month = ? and day = ? and hour = ? and segment = ?"""        
        data = (gasusage, year, month, day, hour, segment)
        cursor.execute(sql_update_usage, data)
        sqliteConnection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert Python variable into prices table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

# get electric usage from Octopus
usage = requests.get('https://api.octopus.energy/v1/electricity-meter-points/'+agile_mpan+'/meters/'+agile_serial+'/consumption/?page_size=240', auth=(agile_api_key, ''))
usagedata = usage.json()
for result in usagedata['results']:
    use_price = result['consumption']
    raw_from = str(result['interval_start'])[0:19]
#    time_zone = (result['interval_start'])[21:22]
    date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S")
#    if time_zone == str(1):   #summer time
#        date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S")  + timedelta(hours=1)
#        print ("A")
#        print (raw_from)
#        print (date)
#    else:
#        date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S")
#        print ("B")
#        print (raw_from)
#        print (date)
#    print (date)
    use_year = (date.year)
    use_month = (date.month)
    use_day = (date.day)
    use_hour = (date.hour) 
    if date.minute == 00:
        use_offset = 0
    else:
        use_offset = 1
    updateUsageIntoTable(use_year, use_month, use_day, use_hour, use_offset, use_price)
  

# get GAS usage from Octopus
usage = requests.get('https://api.octopus.energy/v1/gas-meter-points/'+agile_GAS_mpan+'/meters/'+agile_GAS_serial+'/consumption/?page_size=240', auth=(agile_api_key, ''))
usagedata = usage.json()
for result in usagedata['results']:
    gas_price = result['consumption']
    raw_from = str(result['interval_start'])[0:19]
#    time_zone = (result['interval_start'])[21:22]
    date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S")
#    if time_zone == str(1):   #summer time
#        date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S") # + timedelta(hours=1)
#    else:
#        date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%S")
    use_year = (date.year)
    use_month = (date.month)
    use_day = (date.day)
    use_hour = (date.hour)
    if date.minute == 00:
        use_offset = 0
    else:
        use_offset = 1
    updateGASUsageIntoTable(use_year, use_month, use_day, use_hour, use_offset, gas_price)
    
def is_dst(date):
    return bool(time.localtime(date).tm_isdst)

def dailycost(day):
    usagecost = []
    usagekwh = []
    for offset in range(0, 48):  #24h = 48 segments
        rounded_date = (datetime.datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=0) - timedelta(days=day))
        dst_date = (datetime.datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=6) - timedelta(days=day))
        dayofweek = (rounded_date.strftime('%a'))
        if is_dst(time.mktime(dst_date.timetuple())) == True:
            offset_dst = 60
        else:
            offset_dst = 0
        min_offset = (30 * offset) + offset_dst 
        now_plus_offset = rounded_date + datetime.timedelta(minutes=min_offset) 
        the_year = now_plus_offset.year
        the_month = now_plus_offset.month
        the_hour = (now_plus_offset.hour)
        the_day = now_plus_offset.day
        if now_plus_offset.minute < 30:
            the_segment = 0
        else:
            the_segment = 1
        cur.execute("SELECT * FROM prices WHERE year=? AND month=? AND day=? AND hour=? AND segment=? LIMIT 1",
                (the_year, the_month, the_day, the_hour, the_segment))
        row = cur.fetchone()
        try:
            usagecost.append((row[5]*row[6]))
            usagekwh.append(row[6])
        except TypeError:
            return dayofweek, "----", "----"
            break
    total = sum(usagecost) + standing_charge
    totalkwh = sum(usagekwh)
    return dayofweek, (str("{0:.1f}".format(total)+"p")), (str("{0:.1f}".format(totalkwh)+"kw"))

def dailycostgas(day):
    nonecheck = []
    usagem3 = []
    for offset in range(0, 48):  #24h = 48 segments
        rounded_date = (datetime.datetime.now().replace(microsecond=0, second=0, minute=0, hour=0) - timedelta(days=day)) #, hours=utc_offset))
        #        real_date = (datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, second=0, minute=0, hour=0) - timedelta(days=day))
        dayofweek = (rounded_date.strftime('%a')) # - timedelta(hours=utc_offset))
        min_offset = 30 * offset
        now_plus_offset = rounded_date + datetime.timedelta(minutes=min_offset)
        the_year = now_plus_offset.year
        the_month = now_plus_offset.month
        the_hour = now_plus_offset.hour
        the_day = now_plus_offset.day
        if now_plus_offset.minute < 30:
            the_segment = 0
        else:
            the_segment = 1
        cur.execute("SELECT * FROM prices WHERE year=? AND month=? AND day=? AND hour=? AND segment=? LIMIT 1",
                (the_year, the_month, the_day, the_hour, the_segment))
        row = cur.fetchone()
        try:
            nonecheck.append((row[5]*row[7]))
            usagem3.append(row[7])
        except TypeError:
            return dayofweek, "----", "----"
            break
    totalm3 = sum(usagem3)
    totalGkwh = (((totalm3 * GAS_coeff) * 40) / 3.6)
    total = (totalGkwh * GAS_cost_kwh) + standing_charge 
    return dayofweek, (str("{0:.1f}".format(total)+"p")), (str("{0:.1f}".format(totalGkwh)+"kw"))

        
# draw the useage
def drawcost(day, cost, kwh, costG, kwhG, xco):
    font = ImageFont.truetype(FredokaOne, 16)
    colour = inky_display.BLACK
    draw.text((xco+3,100), day, colour, font)
    draw.text((xco,120), costG, colour, font)
    draw.text((xco,138), cost, colour, font)
    draw.text((xco,154), kwh, colour, font)
 
# call to generate previous costs 
period = 1
x_ref = 58
while (period!=7):
    data = dailycost(period)
    dataG = dailycostgas(period)
    day = data[0]
    cost = data[1]
    kwh = data[2]
    costG = dataG[1]
    kwhG = dataG[2]
    drawcost (day, cost, kwh, costG, kwhG, x_ref)
    period+=1
    x_ref+=58

    
    
#WEATHER

icons = {
  "01d": "B",
  "02d": "H",
  "03d": "H",
  "04d": "Y",
  "09d": "Q",
  "10d": "R",
  "11d": "P",
  "13d": "V",
  "50d": "L",
  "01n": "2",
  "02n": "I",
  "03n": "I",
  "04n": "Y",
  "09n": "Q",
  "10n": "R",
  "11n": "P",
  "13n": "V",
  "50n": "L",
}        


def degrees_to_cardinal(d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


response = requests.get('https://api.openweathermap.org/data/2.5/onecall?lat='+co_ord_lat+'&lon='+co_ord_long+'&exclude=minute,hourly&units=metric&appid='+weatherapikey) 
responce = response.json()
now = responce["current"]
current_temp = now["temp"]
current_feelslike = now["feels_like"]
current_summary = now["weather"]
current_direction = now["wind_deg"]
current_speed = now["wind_speed"]
current_humidity = now["humidity"]
current_icon = current_summary[0]["icon"]
str_val = "Speed "
int_val = current_speed
str_val3 = "ms"
str_val2 = (degrees_to_cardinal(current_direction))
wind_speed = f'{str_val} {int_val}{str_val3} {str_val2}'
ink_colour = inky_display.BLACK
font = ImageFont.truetype(FredokaOne, 20)
x_coord = 164
draw.text((x_coord+65, -5), wind_speed, ink_colour, font)
draw.text((x_coord+65, 19), "Humidity " + (str(current_humidity)) + "%", ink_colour, font)
draw.text((x_coord, 47), ("Temp " + (str(round(current_temp)))) + ("   Feels Like " + (str(round(current_feelslike)))), ink_colour, font)
#draw.text((100,97), "Cost & Usage History", ink_colour, font)
draw.rectangle((0,97,480,97),ink_colour) #1
draw.rectangle((0,76,480,76),ink_colour)
draw.rectangle((0,175,480,175),ink_colour) #2
draw.rectangle((155,76,155,0),ink_colour) #3
font = ImageFont.truetype(FredokaOne, 16)
#draw.text((1,100), "USAGE", ink_colour, font)
draw.text((1,120), "Gas £", ink_colour, font)
draw.text((1,138), "Elec £", ink_colour, font)
draw.text((1,154), "Elec w", ink_colour, font)
font = ImageFont.truetype("/home/pi/Fonts/meteocons.ttf", 50)
if current_icon == "01d": 
    draw.text((x_coord,0), icons[current_icon], inky_display.RED, font)
else: 
    draw.text((x_coord,0), icons[current_icon], inky_display.BLACK, font)

# render the actual image onto the display
inky_display.set_image(img)
inky_display.show()
