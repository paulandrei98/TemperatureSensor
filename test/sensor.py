import random
import json
import time
from time import sleep
from collections import defaultdict

def get_response():
    timestamp1 = int(round(time.time() * 1000))
    timestamp2 = timestamp1+10000

    data = defaultdict(dict)
    data['start_date'] = timestamp1
    data['end_date'] = timestamp2

    data1 = []
    while timestamp1 < timestamp2:
        temp = round(random.uniform(-20.0, 50.0),1)
        datax = defaultdict(dict)
        datax['timestamp'] = timestamp1
        datax['value'] = temp
        data1.append(datax)
        sleep(2)
        timestamp1 = int(round(time.time() * 1000))


    data['measurements'] = data1

    return json.loads(json.dumps(data))

