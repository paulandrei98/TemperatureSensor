import sensor as sens
import database as db
import json
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/')
def hello():
    db.print_database()
    return "Hello"

@app.route('/temperature')
def temperature():
    start = request.args.get('start')
    end = request.args.get('end')
    resp = sens.get_response()
    db.insert_into_db(resp)
    return json.dumps(resp, sort_keys=True, indent=4)

if __name__ == '__main__':
    app.run(debug=True,host='localhost', port=5051)

