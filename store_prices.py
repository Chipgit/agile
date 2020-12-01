# This creates a Database and updates it with released data from Octopus (Run at Startup and Cron from 4pm daily)
# CRONTAB - @reboot sleep 1220; /usr/bin/python3 /home/pi/Agile/store_prices.py >> /home/pi/cron.log
# CRONTAB - 05 16 * * * /usr/bin/python3 /home/pi/Agile/store_prices.py >> /home/pi/cron.log


agile_tariff_code = 'E-1R-AGILE-18-02-21-D'  # Area Specific, Check your developer dashboard at Octopus

import os
os.chdir("/home/pi/Agile")
import sqlite3
import requests
import datetime
import time
import urllib
from urllib.request import pathname2url


def createdatabase():
    conn = sqlite3.connect('octoprice.sqlite')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE prices (year INTEGER, month INTEGER, day INTEGER, hour INTEGER, segment INTEGER, price REAL, usage REAL, gasusage REAL)')
    conn.commit()
    conn.close()
    response = requests.get('https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/'+agile_tariff_code+'/standard-unit-rates/')
    pricedata = response.json()
    for result in pricedata['results']:
        mom_price = result['value_inc_vat']
        raw_from = result['valid_from']
        date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ") # We need to reformat the date to a python date from a json date
        mom_year = (date.year)
        mom_month = (date.month)
        mom_day = (date.day)
        mom_hour = (date.hour)
        if date.minute == 00:
            mom_offset = 0
        else:
            mom_offset = 1 #half hour
        insertVariableIntoTable(mom_year, mom_month, mom_day, mom_hour, mom_offset, mom_price)
    print("Database Created")

def insertVariableIntoTable(year, month, day, hour, segment, price):
    try:
        sqliteConnection = sqlite3.connect('octoprice.sqlite')
        cursor = sqliteConnection.cursor()
        sqlite_insert_with_param = """INSERT INTO 'prices'
            ('year', 'month', 'day', 'hour', 'segment', 'price') 
            VALUES (?, ?, ?, ?, ?, ?);"""
        data_tuple = (year, month, day, hour, segment, price)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqliteConnection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert Python variable into prices table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()

def retrieveTariffs():
    try:
        response = requests.get('https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/'+agile_tariff_code+'/standard-unit-rates/')
        pricedata = response.json()
    except:
        print("Error retrieving tariff data")
        return False
    #Check date of first row to see if tomorrows prices have been returned
    firstrow=pricedata['results'][0]
    firstrawdate=firstrow['valid_from']
    firstdate=datetime.datetime.strptime(firstrawdate, "%Y-%m-%dT%H:%M:%SZ").date()
    print("Date of first row ", firstdate)
    if datetime.date.today() < firstdate: # date of first row is in the future so new prices are available
        print("New prices are available, inserting into database")
        print(pricedata)
        for result in pricedata['results']:
            mom_price = result['value_inc_vat']
            raw_from = result['valid_from']
            date = datetime.datetime.strptime(raw_from, "%Y-%m-%dT%H:%M:%SZ") # We need to reformat the date to a python date from a json date
            mom_year = (date.year)
            mom_month = (date.month)
            mom_day = (date.day)
            mom_hour = (date.hour)
            if date.minute == 00: 
                    mom_offset = 0
            else:
                    mom_offset = 1 
            insertVariableIntoTable(mom_year, mom_month, mom_day, mom_hour, mom_offset, mom_price)
        return True
    else:
        return False

#check to see if database has been created
try:
    dburi = 'file:{}?mode=rw'.format("/home/pi/Agile/octoprice.sqlite")
    conn = sqlite3.connect(dburi, uri=True)
except sqlite3.OperationalError:
    createdatabase()

#retrive values, retry every 12 minutes if not available
count = 0
while (count < 100):
    if retrieveTariffs(): 
        print("Updated Prices Retrieved!")
        break
    else:
        print("Prices not yet available, retrying in 12 minutes")
        time.sleep(720)
