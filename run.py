import json
import coremodules as coremodule
from flask import Flask
from flask import request
import sqlite3


app = Flask(__name__)



@app.route('/fever')
def fever():
    start = int(request.args.get('start',0))
    end = int(request.args.get('end',0))
    data = {}
    if start !=0 and end != 0:
        data = coremodule.get_fever_data(start,end)
        #print(json.dumps(data, indent=4))
    else:
        data = 'Invalid command'
    return data if data.get('events') else "-1"


@app.route('/temperature')
def temperature():
    start = int(request.args.get('start',0))
    end = int(request.args.get('end',0))
    aggregation = request.args.get('aggregation', 0)
    operator = request.args.get('operator', 0)
    data = {}

    if aggregation == 0 and operator == 0 and start != 0 and end != 0:
        c = coremodule.Temperature_raw_data(3, 'Thread_3', 3,start,end)
        c.start()
        c.join()
        data = coremodule.response_temp_data
    else:
        if aggregation != 0 and operator != 0 and start != 0 and end != 0:
            if operator != 'AVERAGE' and operator != 'MEDIAN' and operator != 'MAX':
                data = 'Invalid operator'
            else:
                if aggregation != 'HOURLY' and aggregation != 'DAILY':
                    data = 'Invalid aggregation'
                else:
                    data = coremodule.temperature_aggregation(start, end, aggregation, operator)

        else:
            data = 'Invalid command'

    return data if data.get('measurements') else "-1"


@app.route('/')
def hello():
    return "<center><h1>Main page</h1></center>"


def run_flask():
    app.run(debug=False, host='localhost', port=5051)

if __name__ == '__main__':
  b = coremodule.Sensor(2,'Thread_2',2)
  b.start()
  run_flask()


'''def print_database(): #stergem dupa
    conn = sqlite3.connect("Data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM Temperature_Data")
    for row in c.fetchall():
        print(row[0],row[1])
    conn.close()
'''
