import sqlite3
import json

def create_table():
    conn = sqlite3.connect("Data.db")
    c = conn.cursor()

    # Create table
    c.execute(
        """CREATE TABLE IF NOT EXISTS Temperature_Data (start_date TEXT, end_date TEXT, timestamp TEXT, value REAL)""")
    conn.commit()
    conn.close()


def insert_into_db(resp):
    create_table()

    conn = sqlite3.connect("Data.db")
    c = conn.cursor()

    json.dumps(resp)

    s_date = resp['end_date']
    e_date = resp['start_date']
    for x in resp['measurements']:
        timestamp = x['timestamp']
        val = x['value']
        params = (s_date,e_date,timestamp,val)
        c.execute("INSERT INTO Temperature_Data(start_date,end_date,timestamp,value) VALUES (?,?,?,?)",params)
        conn.commit()

    c.close()
    conn.close()
    print('Done')

def print_database():
    conn = sqlite3.connect("Data.db")
    c = conn.cursor()

    c.execute("SELECT * FROM Temperature_Data")
    for row in c.fetchall():
        print(row)
    conn.close()