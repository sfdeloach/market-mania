#!/usr/share/python3 python3

"""
Title:      pyMarket - Stock Simulator
Created by: sfdeloach@gmail.com
Date:       March 16, 2016

Script analyzes one stock symbol at a time, and acts accordingly:
  - read a years worth of data (or some other specified 'span') and determine 
    the period's 'rolling_hi' and rolling_lo'...these values are trailing and 
    are updated daily for the span
  - The 'price_span' is equal to 'rolling_hi' - 'rolling_lo'
  - The 'span_percent' is a set by the user and is immutable for the
    simulation, it defines the sensitivity to change that will trigger a buy

52-week price span list:
  SPY 181.02 - 213.78 = 32.76, span/low = 18%
  USO 7.67 - 21.50    = 13.83, '''''''' = 180%
  AGG 107.60 - 111.80 = 4.2,   '''''''' = 4%

Theory:
  Buy an equity at a relative low, hold until reserve is met, enter a trailing
  stop limit
"""

import csv
import math
from datetime import date
from datetime import timedelta

## Helper Functions ##

def ftoa(float_num, precision, unit):
    """Returns a formatted string as either a percent or dollar amount."""
    x = float_num * pow(10, precision)
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

def find_high(record_list):
    """Returns the highest price within a list of records"""
    h = record_list[0].high
    for x in record_list:
        if x.high > h:
            h = x.high
    return h

def find_low(record_list):
    """Returns the lowest price wihtin a list of records"""
    l = record_list[0].low
    for x in record_list:
        if x.low < l:
            l = x.low
    return l

## Class Definitions ##

class Record:
    """Represents all the data available on an equity for a given date."""
    def __init__(self, csv_line):
        self.date = self.parse_date(csv_line[0])
        self.close = float(csv_line[1].replace(',', ''))
        self.volume = float(csv_line[2].replace(',', ''))
        self.open = float(csv_line[3].replace(',', ''))
        self.high = float(csv_line[4].replace(',', ''))
        self.low = float(csv_line[5].replace(',', ''))
    def __repr__(self):
        return '{}, close @ ${}'.format(self.date, self.close)
    def parse_date(self, date_str):
        """Returns a date object from a string, 
        must fit the format yyyy-mm-dd"""
        year = int(date_str[0:4])
        month = int(date_str[5:7])
        day = int(date_str[8:10])
        return date(year, month, day)

class Investment:
    """Represents an investment from the time it was purshased to its sale."""
    def __init__(self, target):
        self.status       = 'ready'
        self.target_buy    = target
        self.buy_type      = ''
        self.buy_date      = date(1900, 1, 1)
        self.buy_price     = 0.0
        self.set_date      = date(1900, 1, 1)
        self.set_price     = 0.0
        self.trailing_stop = 0.0
        self.sell_date     = date(1900, 1, 1)
        self.sell_price    = 0.0
    def __repr__(self):
        message = 'Status: {}\n'.format(self.status)
        message += '    Target buy price was {}\n'.format\
        (ftoa(self.target_buy, 2, '$'))
        message += '    {} on {} at {}\n'.format(self.buy_type, \
                                                 self.buy_date, \
                                                 ftoa(self.buy_price, \
                                                                     2, '$'))
        if self.set_date < date(1910, 1, 1):
            message += '    EQUITY WAS NEVER SET\n'
        else:
            message += '    Set on {} at {}\n'.format(self.set_date, \
                                                      ftoa(self.set_price, \
                                                           2,  '$'))
        message += '    Sold on {} at {}\n'.format(self.sell_date, \
                                                   ftoa(self.sell_price, 2, \
                                                        '$'))
        message += '    Period = {} days\n'.format(self.find_days())
        message += '    ROI = {}\n'.format(ftoa(self.find_roi(), 3, '%'))
        message += '    APR = {}'.format(ftoa(self.find_apy(), 3, '%'))
        return message
    def find_days(self):
        """Returns the length of an investment in days"""
        if self.status is 'completed':
            return float((self.sell_date - self.buy_date).days)
        else:
            return 0
    def find_roi(self):
        """Returns the return on investment - non-annualized"""
        if self.status is 'completed':
            return (self.sell_price - self.buy_price) / self.buy_price
        else:
            return 0
    def find_apy(self):
        """Returns the annualized return on investment
        (annual percentage yield)"""
        if self.status is 'completed':
            return 365.25 / self.find_days() * self.find_roi()
        else:
            return 0

## Main Function ##

def start_simulation():
    """This is the main function for the program"""
    print('Market - Equity Trading Simulator')
    symbol = input('Enter symbol: ')
    symbol = 'equities/' + symbol + '.csv'
    span = float(input('Enter span (in weeks): '))
    span_percent = float(input('Enter span percent (%): '))
    limit = float(input('Enter limit (%): '))
    eject = float(input('Enter eject (%): '))
    ini_balance = float(input('Enter initial balance ($): '))
        
    # Open file with stock info and read each 'record' into an object, all of
    # the historical data is held in an ordered array-like structure named
    # 'records'
    f = open(symbol, 'r')
    csv_f = csv.reader(f)
    
    records = list() # Initialize
    for row in csv_f:
        new_record = Record(row)
        records.append(new_record)
        
    records = sorted(records, key=lambda x: x.date) # Sort by ascending date

    #Must advance the length of span
    sim_start_date = records[0].date + timedelta(weeks = span)
    print('\nSimulation will start on ' + str(sim_start_date))

    # Determine the list size of the 'movingRecord' list
    moving_record_size = 0
    for r in records:
        if r.date > sim_start_date:
            break
        else:
            moving_record_size += 1

    # Create a 'moving_records' which will advance during the simulation
    moving_records = records[0:moving_record_size]

    rolling_hi = find_high(moving_records)
    rolling_lo  = find_low(moving_records)
    price_span = rolling_hi - rolling_lo
    target_buy = span_percent * price_span + rolling_lo
    
    # Create a list of investments and place an open 
    investments = list() # Initialize
    investments.append(Investment(target_buy))
    
    # Simulation loop
    for r in records:
        print(str(r.date) +':')
        print('  beginning   = ' + str(investments[-1].status))
        print('  dayHigh     = ' + str(r.high))
        print('  dayLow      = ' + str(r.low))
        print('  rolling_hi = ' + str(rolling_hi))
        print('  rolling_lo  = ' + str(rolling_lo))
        print('  target_buy   = ' + str(target_buy))
                
        # eject! eject! eject!
        if  investments[-1].buy_price * (1 - eject) > r.low and \
        investments[-1].status is 'open':
            investments[-1].status = 'completed'
            investments[-1].sell_date = r.date
            investments[-1].sell_price = investments[-1].buy_price * \
            (1 - eject)
            investments[-1].find_days()
            investments[-1].find_roi()
            investments[-1].find_apy()
            print('* EJECTED! bought at ' + str(investments[-1].buy_price) + \
                  ' sold at ' + str(investments[-1].sell_price))
            investments.append(Investment(target_buy))
        # equity has increased value, trailing_stop increased
        elif r.high * (1 - limit) > investments[-1].trailing_stop and \
        investments[-1].status is 'set':
            message = '* trailing_stop increased from \
            {}'.format(investments[-1].trailing_stop)
            investments[-1].trailing_stop = r.high * (1 - limit)
            message += ' to {}'.format(investments[-1].trailing_stop)
            print(message)
        # equity is sold due to a drop in price below the trailing_stop    
        elif investments[-1].trailing_stop > r.low and \
        investments[-1].status is 'set':
            investments[-1].status = 'completed'
            investments[-1].sell_date = r.date
            investments[-1].sell_price = investments[-1].trailing_stop
            investments[-1].find_days()
            investments[-1].find_roi()
            investments[-1].find_apy()
            print('* investment complete, bought at ' + \
                  str(investments[-1].buy_price) + ' sold at ' + \
                  str(investments[-1].sell_price))
            investments.append(Investment(target_buy))
        # reserve is met    
        elif r.high > investments[-1].set_price and \
        investments[-1].status is 'open':
            investments[-1].status = 'set'
            investments[-1].set_date = r.date
            investments[-1].trailing_stop = investments[-1].buy_price
            print('* investment is set, trailing_stop = ' +
                  str(investments[-1].buy_price))
        # looking for a good time to buy    
        elif r.date > sim_start_date and investments[-1].status is 'ready':
            if target_buy > r.high:
                investments[-1].buy_type = 'Superbuy'
                investments[-1].buy_price = r.high
                investments[-1].set_price = r.high * (1 + limit)
                investments[-1].buy_date = r.date
                investments[-1].status = 'open'
                print('* Superbuy occurred')
            elif r.high > target_buy > r.low:
                investments[-1].buy_type = 'Buy'
                investments[-1].buy_price = target_buy
                investments[-1].set_price = target_buy * (1 + limit)
                investments[-1].buy_date = r.date
                investments[-1].status = 'open'
                print('* Buy occurred')
                
        # Advance the span
        moving_records = moving_records[1:]
        moving_records.append(r)
        rolling_hi = find_high(moving_records)
        rolling_lo  = find_low(moving_records)
        price_span = rolling_hi - rolling_lo
        target_buy = span_percent * price_span + rolling_lo
        print('  ending      = ' + str(investments[-1].status))
        print('- - - - - - - - - - - - - - - - - - - - -')
        
    print('\nInvestment results...')
    investment_num = 1
    moving_balance = ini_balance
    for i in investments:
        print('#' + repr(investment_num))
        investment_num += 1
        print('Initial: ' + ftoa(moving_balance, 2, '$'))
        temp_balance = moving_balance - 14 + moving_balance * i.find_roi()
        print(i)
        change = temp_balance - moving_balance
        print('Change: ' + ftoa(change, 2, '$'))
        moving_balance = temp_balance
        print('Final:  ' + ftoa(moving_balance, 2, '$'))
        print('- - - - - - - - - - - - - - - - - - - - -')
        
    price_change = records[-1].close - records[1].close
    percent_change = price_change / records[1].close
    print('\nIf equity was held for the entire period: ')
    print('  Initial price: ' + repr(records[1].close))
    print('    Final price: ' + repr(records[-1].close))
    print('       %-change: ' + ftoa(percent_change, 3, '%'))
    print('  Final balance: ' + ftoa(percent_change * ini_balance + \
                                     ini_balance, 2, '$'))

start_simulation() # Start
