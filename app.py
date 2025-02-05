import os
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, send_file
from enum import Enum

#from .const import SETTINGS_FILE, TimelapseState

SETTINGS_FILE = "config.json"

class TimelapseState(Enum):
    OFF = "Aus"
    WAITING = "Warte auf Aufnahmezeitpunkt"
    RECORDING = "Aufnahme läuft"

app = Flask(__name__)
state = TimelapseState.OFF

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as file:
            return json.load(file)
        
    return {
        "interval": 10,
        "capture_duration": 60,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "start_time": "12:30",
        "video_duration": 60
    }

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)

def start_timelapse():
    global state
    settings = load_settings()

    start_time = datetime.strptime(settings['start_date'] + " " + settings['start_time'], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(seconds=settings['capture_duration'])

    state = TimelapseState.WAITING

    # Warte bis Aufnahme starten soll
    now = datetime.now()
    while now < start_time:
        if state == TimelapseState.OFF:
            return
        
        print("Warte auf Aufnahmezeitpunkt ...")
        now = datetime.now()
        time.sleep(1)

    state = TimelapseState.RECORDING

    # Aufnahme durchführen
    print(f"Aufnahmezeitpunkt erreicht!")
    current_time = start_time
    i = 1
    while current_time < end_time:
        if state == TimelapseState.OFF:
            break
        
        interval = settings['interval']
        date = current_time.strftime("%Y-%m-%d-%H-%M-%S")

        subprocess.run(["fswebcam", "-r", "1280x720", "--jpeg", "85", f"images/{date}.jpg"])
        print(f"#{i}: Aufnahme gemacht! Warte {interval} Sekunden ...")
        time.sleep(interval)

        i = i + 1
        current_time += timedelta(seconds=interval)

    # Video erstellen
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    subprocess.run([
        "ffmpeg", "-framerate", str(int(settings['capture_duration'] / settings['video_duration'])),
        "-pattern_type", "glob", "-i", "images/*.jpg",
        "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p", f"videos/{date}.mp4"
    ])

    # Alle Fotos löschen
    for file in os.scandir("images/"):
        if file.name.endswith(".jpg"):
            os.unlink(file.path)

    state = TimelapseState.OFF

    print(f"Ende. Video erstellt und Bilder gelöscht!")

@app.route('/')
def index():
    settings = load_settings()
    start_time = datetime.strptime(settings['start_date'] + " " + settings['start_time'], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(seconds=settings['capture_duration'])

    videos = []

    for file in os.scandir("videos/"):
        if file.name.endswith(".mp4"):
            videos.append(file.name)

    return render_template('index.html', settings=settings, end_time=end_time, state=state, running=state!=TimelapseState.OFF, videos=videos)

@app.route('/start_timelapse', methods=['POST'])
def start():
    global state
    if not state == TimelapseState.OFF:
        return redirect('/')

    threading.Thread(target=start_timelapse, daemon=True).start()
    return redirect('/')

@app.route('/stop_timelapse', methods=['POST'])
def stop():
    global state
    state = TimelapseState.OFF
    return redirect('/')

@app.route('/download', methods=['GET'])
def download():
    return send_file('videos/' + request.args.get('file'), as_attachment=True)

@app.route('/delete', methods=['POST'])
def delete():
    os.unlink('videos/' + request.args.get('file'))
    return redirect('/')

@app.route('/set_settings', methods=['POST'])
def set_settings():
    settings = load_settings()

    settings['interval'] = int(request.form['interval'])
    settings['capture_duration'] = int(request.form['capture_duration'])
    settings['start_date'] = request.form['start_date']
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