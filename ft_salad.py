import threading
import eventlet
import serial
import subprocess
import os
import csv
import datetime
import sys

eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, send, emit
from time import time, gmtime, strftime

app = Flask(__name__)
socketio = SocketIO(app)
fieldnames = ['temperature', 'humidity', 'time']
data = []
data_file = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "sensor_data.csv"
)

output_logs = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "output.logs"
)

sys.stdout = open(output_logs, 'w+')

def listen():
    global ser, data_file
    tmp = 0
    hum = 0
    time_taken = 0

    if ser:
        while True:
            read_serial = ser.readline()
            print(read_serial)
            read_serial = read_serial.strip()
            split = read_serial.split(',');

            if len(split) != 2:
                continue

            if 'Humidity' in split[0]:
                hum_data = split[0].split(' ');
                if (len(hum_data) != 2):
                    continue
                hum = hum_data[1]
            else:
                continue

            if 'Temperature' in split[1]:
                tmp_data = split[1].split(' ');
                if (len(tmp_data) != 2):
                    continue
                tmp = tmp_data[1]
            else:
                continue

            time_taken = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            appendDataCSV(data_file, makeData(hum, tmp, time_taken));
    print("listening over")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/data")
def dataPi():
    if ser:
        while True:
            read_serial = ser.readline()
            print(read_serial)
            read_serial = read_serial.strip()
            split = read_serial.split(',');

            if len(split) != 2:
                continue

            if 'Humidity' in split[0]:
                hum_data = split[0].split(' ');
                if (len(hum_data) != 2):
                    continue
                hum = hum_data[1]
            else:
                continue

            if 'Temperature' in split[1]:
                tmp_data = split[1].split(' ');
                if (len(tmp_data) != 2):
                    continue
                tmp = tmp_data[1]
            else:
                continue

            time_taken = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            break
    return return_template('data.html', makeData(hum, tmp, time_taken));

@app.route("/sensor_data")
def getSensorData():
    global data
    return jsonify(data[-43200:])

def createDataCSV(filename):
    with open(filename, 'w+') as csvfile:
        fieldnames = ['temperature', 'humidity', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

def appendDataCSV(filename, data):
    with open(filename, 'a+') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(data)

def makeData(humidity, temperature, time):
    return {
        'temperature': temperature,
        'humidity': humidity,
        'time': time
    }

dev = False
ser = False

try:
    dev = subprocess.check_output('ls /dev/ttyACM*', shell=True)
    ser = serial.Serial(dev.strip(), 9600)
except:
    print("Couldn't find any devices.")

eventlet.spawn(listen)

if __name__ == "__main__":
    try:
        with open(data_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
                print(row)
    except:
        createDataCSV(data_file)

    row_count = sum(1 for row in data)

    if (row_count == 0):
        createDataCSV(data_file)

    socketio.run(app, debug=False)
