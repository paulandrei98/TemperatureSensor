import time
import calendar
import random
import sqlite3
from threading import Thread
from firebase import firebase
from datetime import datetime, timedelta
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import os.path
from os import path

FIREBASE_ROOT = 'https://temperaturesensorproject-fc0ef.firebaseio.com/'
firebase = firebase.FirebaseApplication(FIREBASE_ROOT, None)
FEVER_VALUE = 37.2

response_temp_data = {}


class Sensor(Thread):
    def __init__(self, threadID, name, counter):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def create_table(self):
        conn = sqlite3.connect("Data.db")
        c = conn.cursor()
        # Create table
        c.execute(
            """CREATE TABLE IF NOT EXISTS Temperature_Data(timestamp TEXT, value REAL)""")
        conn.commit()
        conn.close()

    def insert_into_db(self, data):
        conn = sqlite3.connect("Data.db")
        c = conn.cursor()

        params = (data['timestamp'], data['value'])
        c.execute("INSERT INTO Temperature_Data(timestamp,value) VALUES (?,?)", params)
        conn.commit()
        conn.close()
        print('Data Inserted')

    def run(self):
        self.create_table()
        while True:
            data = {}
            data['timestamp'] = calendar.timegm(time.gmtime())
            data['value'] = round(random.uniform(20.0, 50.0), 1)
            self.insert_into_db(data)
            time.sleep(30)


class Temperature_raw_data(Thread):
    def __init__(self, threadID, name, counter, *args):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.agrs = args

    def run(self):
        start = self.agrs[0]
        end = self.agrs[1]
        data = {}
        data['start_date'] = start
        data['end_date'] = end

        conn = sqlite3.connect("Data.db")
        c = conn.cursor()
        c.execute("SELECT * FROM Temperature_Data")

        data1 = []
        for row in c.fetchall():
            if int(row[0]) >= start and int(row[0]) <= end:
                datax = {}
                datax['timestamp'] = int(row[0])
                datax['value'] = row[1]
                data1.append(datax)

        conn.close()
        data['measurements'] = data1
        global response_temp_data
        response_temp_data = data
        return


def get_fever_data(start, end):
    start_timestamp = start
    end_timestamp = end

    conn = sqlite3.connect("Data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM Temperature_Data")

    data = {}
    data['start_date'] = start_timestamp
    data['end_date'] = end_timestamp

    events_data = []
    one_event_data = {}
    one_measure = []
    one_timestamp = {}

    count_consecutive_vals = 0

    current_end_timestamp = 0

    for row in c.fetchall():

        if int(row[0]) >= start_timestamp and int(row[0]) <= end_timestamp:

            if row[1] > FEVER_VALUE:

                count_consecutive_vals = count_consecutive_vals + 1
                if count_consecutive_vals == 1:
                    # push to firebase Event_start
                    dataa = {'timestamp': row[0], 'fever_event': "FEVER_START_EVENT"}
                    sent = json.dumps(dataa)
                    result = firebase.post('/fever', dataa)

                    with open('temperatureValue.csv', 'a') as f:
                        f.write(str(row[1]) + '\n')

                    one_event_data['event_start'] = int(row[0])

                one_timestamp = {}
                one_timestamp['timestamp'] = int(row[0])
                one_timestamp['value'] = row[1]
                one_measure.append(one_timestamp)

                current_end_timestamp = int(row[0])

            else:
                if count_consecutive_vals != 0:

                    if count_consecutive_vals <= 10:
                        # push event_stop
                        dataa = {'timestamp': row[0],
                                 'fever_event': "FEVER_END_EVENT"}
                        sent = json.dumps(dataa)
                        result = firebase.post('/fever', dataa)

                    one_event_data['event_stop'] = current_end_timestamp
                    one_event_data['measurements'] = one_measure
                    events_data.append(one_event_data)

                    count_consecutive_vals = 0
                    one_event_data = {}
                    one_measure = []
                    one_timestamp = {}

    if path.exists('temperatureValue.csv'):
        fever_data = pd.read_csv("temperatureValue.csv")
        plt.xlabel("Time")
        plt.ylabel("Temperature")
        plt.title("Fever Temperature Event Status")
        plt.plot(fever_data)
        plt.show()
        os.remove('temperatureValue.csv')

    if not ('event_stop' in one_event_data) and current_end_timestamp != 0 and 'event_start' in one_event_data:
        one_event_data['event_stop'] = current_end_timestamp
        one_event_data['measurements'] = one_measure
        events_data.append(one_event_data)

    data['events'] = events_data
    conn.close()
    return data


def maximum_operation(data):
    max_value = -20
    for x in data:
        if max_value < x:
            max_value = x
    return max_value


def median_operation(data):
    data = sorted(data)
    length = len(data)
    if length % 2 == 1:
        length = (length - 1) / 2
    else:
        length = length / 2

    return data[int(length - 1)]


def average_operation(data):
    value = 0
    count = 0
    for x in data:
        value = value + x
        count = count + 1
    return value / count


def temperature_aggregation(start, end, aggregation, operator):
    data = {}
    data['start_date'] = start
    data['end_date'] = end
    data['aggregation_type'] = aggregation
    data['operator_type'] = operator

    measurement = []
    one_timestamp = {}

    conn = sqlite3.connect("Data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM Temperature_Data")

    current_hour = 0
    start_interval = start
    end_interval = 0
    data_values = ()
    end_timestamp = 0
    for row in c.fetchall():

        if start <= int(row[0]) and int(row[0]) <= end:
            if aggregation == 'HOURLY':
                if start_interval == start:
                    end_interval = datetime.timestamp(datetime.fromtimestamp(start) + timedelta(hours=1))

            if aggregation == 'DAILY':
                if start_interval == start:
                    end_interval = datetime.timestamp(datetime.fromtimestamp(start) + timedelta(hours=24))

            if start_interval <= int(row[0]) and end_interval >= int(row[0]):
                data_values = data_values + (row[1],)
            else:

                if operator == 'AVERAGE':
                    one_timestamp['timestamp'] = int(start_interval)

                    one_timestamp['value'] = average_operation(data_values)
                    measurement.append(one_timestamp)

                if operator == 'MAX':
                    one_timestamp['timestamp'] = int(start_interval)
                    one_timestamp['value'] = maximum_operation(data_values)
                    measurement.append(one_timestamp)

                if operator == 'MEDIAN':
                    one_timestamp['timestamp'] = int(start_interval)
                    one_timestamp['value'] = median_operation(data_values)
                    measurement.append(one_timestamp)

                data_values = ()
                data_values = data_values + (row[1],)
                one_timestamp = {}
                start_interval = end_interval

                if aggregation == 'HOURLY':
                    end_interval = datetime.timestamp(datetime.fromtimestamp(start_interval) + timedelta(hours=1))
                if aggregation == 'DAILY':
                    end_interval = datetime.timestamp(datetime.fromtimestamp(start_interval) + timedelta(hours=24))

    if data_values != ():
        if operator == 'AVERAGE':
            one_timestamp['timestamp'] = int(start_interval)
            one_timestamp['value'] = average_operation(data_values)
            measurement.append(one_timestamp)

        if operator == 'MAX':
            one_timestamp['timestamp'] = int(start_interval)
            one_timestamp['value'] = maximum_operation(data_values)
            measurement.append(one_timestamp)

        if operator == 'MEDIAN':
            one_timestamp['timestamp'] = int(start_interval)
            one_timestamp['value'] = median_operation(data_values)
            measurement.append(one_timestamp)
    data['measurements'] = measurement
    conn.close()
    return data

