import os
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect

SETTINGS_FILE = "config.json"

app = Flask(__name__)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
        
    return {
    "interval": 10,
    "capture_duration": 60,
    "start_time": "12:30",
    "video_duration": 60
}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)

def start_timelapse():
    settings = load_settings()

    start_time = datetime.strptime(settings['start_time'], "%H:%M")
    end_time = start_time + timedelta(seconds=settings['capture_duration'])

    while datetime.now() < start_time:
        time.sleep(1)

    print(f"Aufnahme startet")
    current_time = start_time
    i = 1
    while current_time < end_time:
        print(f"#{i}: Aufnahme gemacht")
        date_str = current_time.strftime("%Y%m%d%H%M%S")
        subprocess.run(["fswebcam", "-r", "1280x720", "--jpeg", "85", "-D", "1", f"/path/to/images/{date_str}.jpg"])
        time.sleep(settings['interval'])
        i = i + 1
        current_time += timedelta(seconds=settings['interval'])

    print(f"Ende. Video erstellen")

@app.route('/')
def index():
    settings = load_settings()
    return render_template('index.html', settings=settings)

@app.route('/start_timelapse', methods=['POST'])
def start():
    threading.Thread(target=start_timelapse, daemon=True).start()
    return redirect('/')

@app.route('/set_settings', methods=['POST'])
def set_settings():
    settings = load_settings()

    settings['interval'] = int(request.form['interval'])
    settings['capture_duration'] = int(request.form['capture_duration'])
    settings['start_time'] = request.form['start_time']
    settings['video_duration'] = int(request.form['video_duration'])
    
    save_settings(settings)
    return redirect('/')

@app.route('/reset_settings', methods=['POST'])
def reset_settings():
    if os.path.exists(SETTINGS_FILE): 
        os.remove('config.json')

    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)