import os
import json
import time
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect

SETTINGS_FILE = "config.json"

app = Flask(__name__)
running = False

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
    settings = load_settings()

    start_time = datetime.strptime(settings['start_date'] + " " + settings['start_time'], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(seconds=settings['capture_duration'])

    now = datetime.now()

    print(now.strftime("%d%m/%Y, %H:%M:%S") + " < " + start_time.strftime("%d/%m/%Y, %H:%M:%S"))

    while now < start_time:
        print(now.strftime("%Y-%m-%d %H:%M") + " < " + start_time.strftime("%Y-%m-%d %H:%M"))
        print("Warte auf Aufnahmezeitpunkt ...")
        now = datetime.now()
        time.sleep(1)

    running = True

    print(f"Aufnahmezeitpunkt erreicht!")
    current_time = start_time
    i = 1
    while current_time < end_time:
        date_str = current_time.strftime("%Y%m%d%H%M%S")
        subprocess.run(["fswebcam", "-r", "1280x720", "--jpeg", "85", f"images/{date_str}.jpg"])
        print(f"#{i}: Aufnahme gemacht! Warte {settings['interval']} Sekunden ...")
        time.sleep(settings['interval'])

        i = i + 1
        current_time += timedelta(seconds=settings['interval'])

    subprocess.run([
        "ffmpeg", "-framerate", str(int(settings['capture_duration'] / settings['video_duration'])),
        "-pattern_type", "glob", "-i", "images/*.jpg",
        "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p", "video.mp4"
    ])

    running = False

    for file in os.scandir("images/"):
        if file.name.endswith(".jpg"):
            os.unlink(file.path)

    print(f"Ende. Video erstellt und Bilder gelöscht!")

@app.route('/')
def index():
    settings = load_settings()
    start_time = datetime.strptime(settings['start_date'] + " " + settings['start_time'], "%Y-%m-%d %H:%M")
    end_time = start_time + timedelta(seconds=settings['capture_duration'])

    return render_template('index.html', settings=settings, end_time=end_time, running=running)

@app.route('/start_timelapse', methods=['POST'])
def start():
    threading.Thread(target=start_timelapse, daemon=True).start()
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