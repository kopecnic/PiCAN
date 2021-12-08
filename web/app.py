from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import can
import cantools
import random

import sys

sys.path.append('../tools/PiCANAnalyzer')

import CANAnalyzer


from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
#socketio = SocketIO(app, logger=True, engineio_logger=True, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

bus0 = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000) #setup bus 1
bus1 = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=1000000) #setup bus 2

#initialize Analyzer object
analyzer = CANAnalyzer.CANAnalyzer(busses=[bus0, bus1], id_display_mode=0, data_display_mode=0, timestamp_display_mode=1) 

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('display_test')
def display_test():

    canDataList = []

    tableHeaders = analyzer.get_web_print_table_headers()
    tableData = analyzer.get_web_print_data_table()

    emit('test_response', {'text': "THIS IS A TEST!!!", 'time': datetime.now().strftime("%H:%M:%S.%f")[:-3], 'canData': canDataList, 'tableHeaders': tableHeaders, 'tableData': tableData})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
