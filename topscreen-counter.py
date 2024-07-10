import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import ctypes
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import time
import json
import os

settings_file = "settings.json"
default_start_time = datetime(2024, 7, 5, 21, 0)
default_title_text = "Accountibility Counter"
widget_height = 20

if os.path.exists(settings_file):
    with open(settings_file, "r") as f:
        settings = json.load(f)
        start_time = datetime.fromisoformat(settings.get("start_time", default_start_time.isoformat()))
        title_text = settings.get("title_text", default_title_text)
else:
    start_time = default_start_time
    title_text = default_title_text

class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("hWnd", ctypes.c_void_p), ("uCallbackMessage", ctypes.c_uint),
                ("uEdge", ctypes.c_uint), ("rc", ctypes.c_int * 4), ("lParam", ctypes.c_int)]

ABM_NEW = 0x00000000
ABM_SETPOS = 0x00000003
ABE_TOP = 1

def set_appbar(hwnd):
    screen_width = root.winfo_screenwidth()
    abd = APPBARDATA(ctypes.sizeof(APPBARDATA), hwnd, 0, ABE_TOP, (0, 0, screen_width, widget_height), 0)
    ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
    ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))

def update_counter():
    while True:
        now = datetime.now()
        elapsed = now - start_time
        days, remainder = divmod(elapsed.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        counter_label.config(text=f"{int(days):02}:{int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        root.update_idletasks()
        time.sleep(1)

def create_image():
    image = Image.new('RGB', (64, 64), "black")
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, 64, 64), fill="white")
    dc.rectangle((16, 16, 48, 48), fill="black")
    return image

def on_quit(icon, item):
    icon.stop()
    root.quit()

def setup_tray_icon():
    icon_image = create_image()
    menu = (item('Settings', lambda: root.after(0, open_settings)), item('Quit', on_quit))
    icon = pystray.Icon("accountability_counter", icon_image, title_text, menu)
    icon.run()

def save_settings():
    with open(settings_file, "w") as f:
        json.dump({
            "start_time": start_time.isoformat(),
            "title_text": title_text
        }, f)

def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("350x160")
    
    tk.Label(settings_window, text="Enter the title text:").pack(pady=5)
    title_entry = tk.Entry(settings_window, width=50)
    title_entry.pack(pady=5)
    title_entry.insert(0, title_text)

    tk.Label(settings_window, text="Enter the start time (YYYY-MM-DD HH:MM:SS):").pack(pady=5)
    time_entry = tk.Entry(settings_window, width=50)
    time_entry.pack(pady=5)
    time_entry.insert(0, start_time.strftime("%Y-%m-%d %H:%M:%S"))

    def save_and_close():
        global start_time, title_text
        new_title_text = title_entry.get()
        new_start_time = time_entry.get()
        
        if new_title_text:
            title_text = new_title_text
            text_label.config(text=title_text)
        
        try:
            start_time = datetime.strptime(new_start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("Invalid format", "The start time format is invalid. Please use YYYY-MM-DD HH:MM:SS")
            return
        
        save_settings()
        settings_window.destroy()

    tk.Button(settings_window, text="OK", command=save_and_close).pack(pady=10)

lock_file_path = os.path.expanduser("~/.top_screen_counter.lock")
lock_file = open(lock_file_path, "w")
try:
    import portalocker
    portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)
except (ImportError, portalocker.LockException):
    print("Another instance is already running. Exiting.")
    exit()

root = tk.Tk()
root.title(title_text)
screen_width = root.winfo_screenwidth()
root.geometry(f"{screen_width}x{widget_height}+0+0")
root.overrideredirect(True)
root.attributes("-topmost", True)

hwnd = root.winfo_id()
set_appbar(hwnd)

counter_frame = tk.Frame(root, bg='black')
counter_frame.pack(fill='both', expand=True)

counter_label = tk.Label(counter_frame, font=("Helvetica", 8), bg="black", fg="red")
counter_label.pack(side='left', padx=5)

text_label = tk.Label(counter_frame, text=title_text, font=("Helvetica", 8), bg="black", fg="white")
text_label.pack(side='left', padx=5)

threading.Thread(target=update_counter, daemon=True).start()
threading.Thread(target=setup_tray_icon, daemon=True).start()

root.mainloop()