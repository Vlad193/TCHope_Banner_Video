import cv2
import os
import time
import threading
import keyboard  # pip install keyboard
import pysubs2   # pip install pysubs2
import pyperclip # pip install pyperclip
import pyautogui

# Paths
video_path = r"path\to\video"
subtitle_path = r"path\to\.srt\subtitles"
output_path = r"D:\Program Files (x86)\Steam\steamapps\common\King Arthur's Gold\Base\Sprites\vid.png" #Check Game Location in steam

# Settings
output_size = (64, 64)
interval_sec = 0.05  # 20 FPS

# Validating
if not os.path.exists(video_path):
    raise FileNotFoundError(f"Video not found: {video_path}")
if subtitle_path and not os.path.exists(subtitle_path):
    raise FileNotFoundError(f"Subtitles not found: {subtitle_path}")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Load Subtitles
subs = []
if subtitle_path:
    subs = pysubs2.load(subtitle_path, encoding="cp1251")

# Video Info
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
duration_sec = frame_count / fps if fps > 0 else 0
if fps <= 0 or duration_sec <= 0:
    raise RuntimeError("Can't get video info")

# Vars
active = False
reset_requested = False
time_position = 0.0
last_subtitle_text = None
lock = threading.Lock()

# Hotkey func
def toggle_active():
    global active
    with lock:
        active = not active
        print(f"[{time.strftime('%H:%M:%S')}] {'ENABLED' if active else 'DISABLED'}")

def request_reset():
    global reset_requested
    with lock:
        reset_requested = True
        print(f"[{time.strftime('%H:%M:%S')}] Resetting to 0 second.")

def try_replace_file(temp_path, final_path):
    while True:
        try:
            os.replace(temp_path, final_path)
            break
        except PermissionError:
            time.sleep(0.1)

# Send to chat | Used for @banner vid
def send_to_chat(text: str):
    pyperclip.copy(text)
    time.sleep(0.02)
    keyboard.press_and_release('y')
    time.sleep(0.02)
    keyboard.press('ctrl')
    keyboard.press_and_release('v')
    keyboard.release('ctrl')
    time.sleep(0.02)
    keyboard.press_and_release('enter')

# Send to chat subtitles
def send_to_chat_sub(text: str):
    time.sleep(0.05)
    keyboard.press_and_release('t')
    time.sleep(0.05)
    keyboard.write(text, delay=0.01)
    time.sleep(0.05)
    keyboard.press_and_release('enter')

# Main Loop
def video_loop():
    global time_position, reset_requested, last_subtitle_text

    while True:
        start_time = time.time()

        with lock:
            if not active:
                time.sleep(0.1)
                continue
            if reset_requested:
                time_position = 0.0
                reset_requested = False

        cap.set(cv2.CAP_PROP_POS_MSEC, time_position * 1000)
        success, frame = cap.read()

        if not success:
            time_position = 0.0
            continue

        resized = cv2.resize(frame, output_size, interpolation=cv2.INTER_AREA)
        base, ext = os.path.splitext(output_path)
        temp_path = base + ".tmp" + ext
        cv2.imwrite(temp_path, resized)
        try_replace_file(temp_path, output_path)

        print(f"[{time.strftime('%H:%M:%S')}] Frame {time_position:.2f} Second → {output_path}")

        send_to_chat("@banner vid")

        if subs:
            current_subs = [line for line in subs if line.start / 1000 <= time_position < line.end / 1000]
            if current_subs:
                current_text = current_subs[0].text.strip()
                if current_text != last_subtitle_text:
                    last_subtitle_text = current_text
                    send_to_chat_sub(current_text)
            else:
                last_subtitle_text = None

        time_position += interval_sec
        if time_position >= duration_sec:
            time_position = 0.0

        elapsed = time.time() - start_time
        sleep_time = interval_sec - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

# Start
threading.Thread(target=video_loop, daemon=True).start()

print("Script started.")
print("  ▸ Press '-' — On/Off")
print("  ▸ Press '+' — Reset video to 0 second")
print("Press CTRL+C for Exit.")

keyboard.add_hotkey('-', toggle_active)
keyboard.add_hotkey('+', request_reset)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exit.")
