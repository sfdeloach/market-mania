#!/usr/share/python3 python3

import csv
import math
import time
from datetime import date
from datetime import timedelta

# Title:      pyMarket - Stock Simulator
# Created by: sfdeloach@gmail.com
# Date:       March 16, 2016

# Script analyzes one stock symbol at a time, and acts accordingly:
#   - read a years worth of data (or some other specified 'span') and determine the period's 
#     'rollingHigh' and rollingLow'...these values are trailing and are updated daily for the span
#   - The 'priceSpan' is equal to 'rollingHigh' - 'rollingLow'
#   - The 'buySpanPercent' is a set by the user and is immutable for the simulation, it defines the
#     sensitivity to change that will trigger a buy
#   - 

# 52-week price span list:
#   SPY 181.02 - 213.78 = 32.76, span/low = 18%
#   USO 7.67 - 21.50    = 13.83, '''''''' = 180%
#   AGG 107.60 - 111.80 = 4.2,   '''''''' = 4%

# Theory:
#   Buy an equity at a relative low, hold until reserve is met, enter a trailing stop limit

## Helper Functions ################################################################################

def fToA(floatingNumber, precision, unit):
    x = floatingNumber * pow(10, precision)
    if unit is '%':
        x = x * 100
    x = math.trunc(x)
    x = x / pow(10, precision)
    if unit is '%':
        return str(x) + '%'
    if unit is '$':
        return '$' + str(x)
    else:
        return str(x)

def findHigh(listOfRecords):
    h = listOfRecords[0].high
    for x in listOfRecords:
        if x.high > h:
            h = x.high
    return h

def findLow(listOfRecords):
    l = listOfRecords[0].low
    for x in listOfRecords:
        if x.low < l:
            l = x.low
    return l

## Class Definitions ###############################################################################

class record:
    def __init__(self, csvString):
        self.date = self.parseDate(csvString[0])
        self.close = float(csvString[1].replace(',', ''))
        self.volume = float(csvString[2].replace(',', ''))
        self.open = float(csvString[3].replace(',', ''))
        self.high = float(csvString[4].replace(',', ''))
        self.low = float(csvString[5].replace(',', ''))
    def __repr__(self):
        return '{}, close @ ${}'.format(self.date, self.close)
    def parseDate(self, dateString):
        year = int(dateString[0:4])
        month = int(dateString[5:7])
        day = int(dateString[8:10])
        return date(year, month, day)

class investment:
    def __init__(self, target):
        self.status       = 'ready'
        self.targetBuy    = target
        self.buyType      = ''
        self.buyDate      = date(1900, 1, 1)
        self.buyPrice     = 0.0
        self.setDate      = date(1900, 1, 1)
        self.setPrice     = 0.0
        self.trailingStop = 0.0
        self.sellDate     = date(1900, 1, 1)
        self.sellPrice    = 0.0
    def __repr__(self):
        message = 'Status: {}\n'.format(self.status)
        message += '    Target buy price was {}\n'.format(fToA(self.targetBuy, 2, '$'))
        message += '    {} on {} at {}\n'.format(self.buyType, self.buyDate, fToA(self.buyPrice, 2, '$'))
        if self.setDate < date(1910, 1, 1):
            message += '    EQUITY WAS NEVER SET\n'
        else:
            message += '    Set on {} at {}\n'.format(self.setDate, fToA(self.setPrice, 2, '$'))
        message += '    Sold on {} at {}\n'.format(self.sellDate, fToA(self.sellPrice, 2, '$'))
        message += '    Period = {} days\n'.format(self.findTime())
        message += '    ROI = {}\n'.format(fToA(self.findROI(), 3, '%'))
        message += '    APR = {}'.format(fToA(self.findAPR(), 3, '%'))
        return message
    def findTime(self):
        if self.status is 'completed':
            return float((self.sellDate - self.buyDate).days)
        else:
            return 0
    def findROI(self):
        if self.status is 'completed':
            return (self.sellPrice - self.buyPrice) / self.buyPrice
        else:
            return 0
    def findAPR(self):
        if self.status is 'completed':
            return 365.25 / self.findTime() * self.findROI()
        else:
            return 0

## Main Function ###################################################################################

def goForLaunch():
    print('Market - Equity Trading Simulator')
    symbol = input('Enter symbol: ')
    symbol += '.csv'
    span = float(input('Enter span (in weeks): '))
    spanPercent = float(input('Enter span percent (%): '))
    limit = float(input('Enter limit (%): '))
    eject = float(input('Enter eject (%): '))
    initialBalance = float(input('Enter initial balance ($): '))
        
    # Open file with stock info and read each 'record' into an object, all of the historical data
    # is held in an ordered array-like structure named 'records'
    f = open(symbol, 'r')
    csv_f = csv.reader(f)
    
    records = list() # Initialize
    for row in csv_f:
        newRecord = record(row)
        records.append(newRecord)
        
    records = sorted(records, key=lambda x: x.date) # Sort by ascending date

    simStartDate = records[0].date + timedelta(weeks = span) # Must advance the length of span
    print('\nSimulation will start on ' + str(simStartDate))

    # Determine the list size of the 'movingRecord' list
    sizeOfMovingRecordList = 0
    for r in records:
        if r.date > simStartDate:
            break
        else:
            sizeOfMovingRecordList += 1

    # Create a 'movingRecordList' which will advance during the simulation
    movingRecordList = records[0:sizeOfMovingRecordList]

    rollingHigh = findHigh(movingRecordList)
    rollingLow  = findLow(movingRecordList)
    priceSpan = rollingHigh - rollingLow
    targetBuy = spanPercent * priceSpan + rollingLow
    
    # Create a list of investments and place an open 
    investments = list() # Initialize
    investments.append(investment(targetBuy))
    
    # Simulation loop
    for r in records:
        print(str(r.date) +':')
        print('  beginning   = ' + str(investments[-1].status))
        print('  dayHigh     = ' + str(r.high))
        print('  dayLow      = ' + str(r.low))
        print('  rollingHigh = ' + str(rollingHigh))
        print('  rollingLow  = ' + str(rollingLow))
        print('  targetBuy   = ' + str(targetBuy))
                
        # eject! eject! eject!
        if  investments[-1].buyPrice * (1 - eject) > r.low and investments[-1].status is 'open':
            investments[-1].status = 'completed'
            investments[-1].sellDate = r.date
            investments[-1].sellPrice = investments[-1].buyPrice * (1 - eject)
            investments[-1].findTime()
            investments[-1].findROI()
            investments[-1].findAPR()
            print('* EJECTED! bought at ' + str(investments[-1].buyPrice) + ' sold at ' + str(investments[-1].sellPrice))
            investments.append(investment(targetBuy))
        # equity has increased value, trailingStop increased
        elif r.high * (1 - limit) > investments[-1].trailingStop and investments[-1].status is 'set':
            message = '* trailingStop increased from {}'.format(investments[-1].trailingStop)
            investments[-1].trailingStop = r.high * (1 - limit)
            message += ' to {}'.format(investments[-1].trailingStop)
            print(message)
        # equity is sold due to a drop in price below the trailingStop    
        elif investments[-1].trailingStop > r.low and investments[-1].status is 'set':
            investments[-1].status = 'completed'
            investments[-1].sellDate = r.date
            investments[-1].sellPrice = investments[-1].trailingStop
            investments[-1].findTime()
            investments[-1].findROI()
            investments[-1].findAPR()
            print('* investment complete, bought at ' + str(investments[-1].buyPrice) + ' sold at ' + str(investments[-1].sellPrice))
            investments.append(investment(targetBuy))
        # reserve is met    
        elif r.high > investments[-1].setPrice and investments[-1].status is 'open':
            investments[-1].status = 'set'
            investments[-1].setDate = r.date
            investments[-1].trailingStop = investments[-1].buyPrice
            print('* investment is set, trailingStop = ' + str(investments[-1].buyPrice))
        # looking for a good time to buy    
        elif r.date > simStartDate and investments[-1].status is 'ready':
            if targetBuy > r.high:
                investments[-1].buyType = 'Superbuy'
                investments[-1].buyPrice = r.high
                investments[-1].setPrice = r.high * (1 + limit)
                investments[-1].buyDate = r.date
                investments[-1].status = 'open'
                print('* Superbuy occurred')
            elif r.high > targetBuy > r.low:
                investments[-1].buyType = 'Buy'
                investments[-1].buyPrice = targetBuy
                investments[-1].setPrice = targetBuy * (1 + limit)
                investments[-1].buyDate = r.date
                investments[-1].status = 'open'
                print('* Buy occurred')
                
        # Advance the span
        movingRecordList = movingRecordList[1:]
        movingRecordList.append(r)
        rollingHigh = findHigh(movingRecordList)
        rollingLow  = findLow(movingRecordList)
        priceSpan = rollingHigh - rollingLow
        targetBuy = spanPercent * priceSpan + rollingLow
        print('  ending      = ' + str(investments[-1].status))
        print('- - - - - - - - - - - - - - - - - - - - -')
        
    print('\nResults...')
    investNo = 1
    for i in investments:
        print('#' + repr(investNo))
        investNo += 1
        print('Initial: ' + fToA(initialBalance, 2, '$'))
        tempBalance = initialBalance - 14 + initialBalance * i.findROI()
        print(i)
        change = tempBalance - initialBalance
        print('Change: ' + fToA(change, 2, '$'))
        initialBalance = tempBalance
        print('Final:  ' + fToA(initialBalance, 2, '$'))
        print('- - - - - - - - - - - - - - - - - - - - -')
        
    priceChange = records[-1].close - records[1].close
    percentChange = priceChange / records[1].close
    print('\nIf equity was held for the entire period: ')
    print('  Initial price: ' + repr(records[1].close))
    print('    Final price: ' + repr(records[-1].close))
    print('       %-change: ' + fToA(percentChange, 3, '%'))
    print('  Final balance: ' + fToA(percentChange * initialBalance + initialBalance, 2, '$'))

goForLaunch() # Start
