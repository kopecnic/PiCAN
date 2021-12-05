from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import can
import cantools
import random


from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
#socketio = SocketIO(app, logger=True, engineio_logger=True, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('display_test')
def display_test():

    lenght = random.randint(1, 10)

    canDataList = []

    for i in range(1, lenght):
        canDataList.append(i)

    emit('test_response', {'text': "THIS IS A TEST!!!", 'time': datetime.now().strftime("%H:%M:%S.%f")[:-3], 'canData': canDataList})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
