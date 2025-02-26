import pyautogui
import keyboard
import time
import json
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import ImageGrab, Image
import threading
import os
from datetime import datetime
import platform

# For Windows
if platform.system() == "Windows":
    import win32gui
    import win32process
    import psutil
# For macOS
elif platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace
    except ImportError:
        print("AppKit not available. Install with: pip install pyobjc-framework-Cocoa")
# For Linux
elif platform.system() == "Linux":
    try:
        from Xlib import display, X
        from Xlib.protocol.rq import Event
    except ImportError:
        print("Xlib not available. Install with: pip install python-xlib")

class InputRecorder:
    def __init__(self):
        self.recording = False
        self.actions = []
        self.start_time = 0
        self.screenshot_size = (100, 100)  # Default size (width, height)
        self.screenshot_dir = "screenshots"
        
        # Create screenshot directory if it doesn't exist
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
        # Set up the GUI
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Input Recorder")
        self.root.geometry("300x400")
        
        # Create frames
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        config_frame = tk.Frame(self.root, padx=10, pady=10)
        config_frame.pack(fill=tk.X)
        
        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill=tk.X)
        
        # Control buttons
        self.start_button = tk.Button(control_frame, text="Start Recording", command=self.start_recording, bg="green", fg="white")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(control_frame, text="Stop Recording", command=self.stop_recording, bg="red", fg="white", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Configuration options
        tk.Label(config_frame, text="Screenshot Size:").grid(row=0, column=0, sticky=tk.W)
        
        size_frame = tk.Frame(config_frame)
        size_frame.grid(row=0, column=1, sticky=tk.W)
        
        tk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
        self.width_entry = tk.Entry(size_frame, width=5)
        self.width_entry.insert(0, str(self.screenshot_size[0]))
        self.width_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Label(size_frame, text="Height:").pack(side=tk.LEFT, padx=(5, 0))
        self.height_entry = tk.Entry(size_frame, width=5)
        self.height_entry.insert(0, str(self.screenshot_size[1]))
        self.height_entry.pack(side=tk.LEFT, padx=2)
        
        update_button = tk.Button(config_frame, text="Update Size", command=self.update_screenshot_size)
        update_button.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        save_button = tk.Button(config_frame, text="Save Script", command=self.save_script)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        play_button = tk.Button(config_frame, text="Play Script", command=self.play_script)
        play_button.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Status display
        self.status_label = tk.Label(status_frame, text="Not recording", fg="red")
        self.status_label.pack()
        
        self.action_count_label = tk.Label(status_frame, text="Actions: 0")
        self.action_count_label.pack()
        
        self.screenshot_count_label = tk.Label(status_frame, text="Screenshots: 0")
        self.screenshot_count_label.pack()
        
        self.window_label = tk.Label(status_frame, text="Current window: None")
        self.window_label.pack()
        
        # Start the tkinter event loop
        self.root.mainloop()
    
    def get_active_window_info(self):
        """Get information about the currently active window"""
        window_info = {"title": "Unknown", "process": "Unknown"}
        
        # Windows implementation
        if platform.system() == "Windows":
            try:
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                window_info["title"] = win32gui.GetWindowText(hwnd)
                window_info["process"] = psutil.Process(pid).name()
            except Exception as e:
                print(f"Error getting window info: {e}")
        
        # macOS implementation
        elif platform.system() == "Darwin":
            try:
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                window_info["process"] = active_app['NSApplicationName']
                window_info["title"] = active_app['NSApplicationName']  # macOS doesn't easily provide window titles
            except Exception as e:
                print(f"Error getting window info: {e}")
        
        # Linux implementation
        elif platform.system() == "Linux":
            try:
                d = display.Display()
                root = d.screen().root
                window_id = root.get_full_property(
                    d.intern_atom('_NET_ACTIVE_WINDOW'), X.AnyPropertyType
                ).value[0]
                
                window = d.create_resource_object('window', window_id)
                window_info["title"] = window.get_full_property(
                    d.intern_atom('_NET_WM_NAME'), 0
                ).value.decode()
                
                window_pid = window.get_full_property(
                    d.intern_atom('_NET_WM_PID'), X.AnyPropertyType
                )
                if window_pid:
                    window_info["process"] = psutil.Process(window_pid.value[0]).name()
            except Exception as e:
                print(f"Error getting window info: {e}")
        
        return window_info
    
    def update_screenshot_size(self):
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            self.screenshot_size = (width, height)
            messagebox.showinfo("Success", f"Screenshot size updated to {width}x{height}")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for width and height")
    
    def start_recording(self):
        self.recording = True
        self.actions = []
        self.start_time = time.time()
        self.status_label.config(text="Recording...", fg="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start recording in a separate thread
        self.record_thread = threading.Thread(target=self.record_inputs)
        self.record_thread.daemon = True
        self.record_thread.start()
    
    def stop_recording(self):
        self.recording = False
        self.status_label.config(text="Not recording", fg="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.action_count_label.config(text=f"Actions: {len(self.actions)}")
    
    def record_inputs(self):
        screenshot_count = 0
        
        # Listen for keypress events
        keyboard.hook(lambda e: self.on_key_event(e) if self.recording and e.event_type == 'down' else None)
        
        while self.recording:
            # Record mouse movement
            x, y = pyautogui.position()
            timestamp = time.time() - self.start_time
            
            # Get active window info
            active_window = self.get_active_window_info()
            
            # Update window label
            self.root.after(0, lambda title=active_window["title"]: 
                            self.window_label.config(text=f"Current window: {title[:20]}..."))
            
            # Only record mouse movements when they change
            if not self.actions or self.actions[-1]['type'] != 'mousemove' or \
               (self.actions[-1]['x'] != x or self.actions[-1]['y'] != y):
                self.actions.append({
                    'type': 'mousemove',
                    'x': x,
                    'y': y,
                    'time': timestamp,
                    'window_title': active_window["title"],
                    'window_process': active_window["process"]
                })
            
            # Check for mouse clicks
            if pyautogui.mouseDown(button='left'):
                screenshot_path = self.take_screenshot(x, y, screenshot_count)
                screenshot_count += 1
                
                self.actions.append({
                    'type': 'click',
                    'button': 'left',
                    'x': x,
                    'y': y,
                    'time': timestamp,
                    'screenshot': screenshot_path,
                    'window_title': active_window["title"],
                    'window_process': active_window["process"]
                })
                
                # Update screenshot count on GUI
                self.root.after(0, lambda: self.screenshot_count_label.config(text=f"Screenshots: {screenshot_count}"))
                
                # Wait for release to avoid multiple clicks
                while pyautogui.mouseDown(button='left') and self.recording:
                    time.sleep(0.01)
            
            # Update action count periodically
            if len(self.actions) % 10 == 0:
                self.root.after(0, lambda count=len(self.actions): self.action_count_label.config(text=f"Actions: {count}"))
            
            time.sleep(0.01)
    
    def on_key_event(self, event):
        timestamp = time.time() - self.start_time
        active_window = self.get_active_window_info()
        
        # Record key press
        self.actions.append({
            'type': 'keypress',
            'key': event.name,
            'time': timestamp,
            'window_title': active_window["title"],
            'window_process': active_window["process"]
        })
    
    def take_screenshot(self, x, y, count):
        # Calculate the bounds for the screenshot
        half_width = self.screenshot_size[0] // 2
        half_height = self.screenshot_size[1] // 2
        
        left = max(0, x - half_width)
        top = max(0, y - half_height)
        right = left + self.screenshot_size[0]
        bottom = top + self.screenshot_size[1]
        
        # Take the screenshot
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        # Save the screenshot
        filename = f"{self.screenshot_dir}/screenshot_{count}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        screenshot.save(filename)
        
        return filename
    
    def save_script(self):
        if not self.actions:
            messagebox.showinfo("Info", "No actions recorded yet")
            return
        
        filename = simpledialog.askstring("Save Script", "Enter filename:", initialvalue="input_script.json")
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            
            with open(filename, 'w') as f:
                json.dump({
                    'actions': self.actions,
                    'screenshot_size': self.screenshot_size
                }, f, indent=2)
            
            messagebox.showinfo("Success", f"Script saved as {filename}")
    
    def play_script(self):
        filename = simpledialog.askstring("Load Script", "Enter filename:", initialvalue="input_script.json")
        if not filename:
            return
            
        if not os.path.exists(filename):
            messagebox.showerror("Error", f"File {filename} not found")
            return
        
        try:
            with open(filename, 'r') as f:
                script = json.load(f)
            
            actions = script['actions']
            
            # Ask for confirmation
            if not messagebox.askyesno("Confirm", f"Play script with {len(actions)} actions? The script will start in 3 seconds."):
                return
            
            # Start playback in a separate thread
            playback_thread = threading.Thread(target=self.execute_script, args=(actions,))
            playback_thread.daemon = True
            playback_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load script: {str(e)}")
    
    def execute_script(self, actions):
        # Wait a moment before starting
        self.status_label.config(text="Starting playback in 3 seconds...", fg="blue")
        time.sleep(3)
        self.status_label.config(text="Playing script...", fg="blue")
        
        last_time = 0
        
        for action in actions:
            # Wait for the appropriate time
            time_diff = action['time'] - last_time
            if time_diff > 0:
                time.sleep(time_diff)
            
            # Check if target window is active
            current_window = self.get_active_window_info()
            if 'window_title' in action and current_window['title'] != action['window_title']:
                print(f"Warning: Expected window '{action['window_title']}' but found '{current_window['title']}'")
            
            # Execute the action
            if action['type'] == 'mousemove':
                pyautogui.moveTo(action['x'], action['y'], duration=0.1)
            elif action['type'] == 'click':
                pyautogui.click(action['x'], action['y'], button=action['button'])
            elif action['type'] == 'keypress':
                pyautogui.press(action['key'])
            
            last_time = action['time']
        
        self.status_label.config(text="Script playback complete", fg="green")
        time.sleep(2)
        self.status_label.config(text="Not recording", fg="red")

if __name__ == "__main__":
    app = InputRecorder()
