import threading
import time
import re
from collections import Counter
from datetime import date
from pynput import keyboard, mouse
import win32gui
import win32process
import psutil


class ProductivityEventCollector:
    """
    Real-time collector for Windows background monitoring.
    Uses win32 APIs and pynput hooks to capture delta counters and sanitized window metadata.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.app_seconds = Counter()
        self.app_switches = Counter()
        self.event_counts = Counter()
        self.last_window_metadata = {}
        self.last_active_app = None
        self._last_click_time = 0
        self.modifiers = {'ctrl': False, 'shift': False, 'alt': False, 'meta': False}
        
        # Start background thread for active application monitoring
        self.running = True
        self.monitor_thread = threading.Thread(target=self._app_monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start mouse and keyboard pynput threads
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self.keyboard_listener.start()
        
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click, on_scroll=self._on_mouse_scroll)
        self.mouse_listener.start()

    def _sanitize_title(self, title):
        if not title:
            return ""
        # Strip folders or path patterns
        title = re.sub(r'[a-zA-Z]:\\[\\\w\s\-\.\(\)]+', '[Path]', title)
        # Strip emails
        title = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[Email]', title)
        # Strip URLs
        title = re.sub(r'https?://[^\s]+', '[URL]', title)
        return title[:120]

    def _get_active_app_info(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return "Idle", "", ""
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            proc_name = proc.name().lower()
            win_class = win32gui.GetClassName(hwnd)
            win_title = win32gui.GetWindowText(hwnd)
            
            # Map processes to application names
            if "chrome" in proc_name:
                return "Chrome", win_class, win_title
            elif "msedge" in proc_name:
                return "Edge", win_class, win_title
            elif "firefox" in proc_name:
                return "Firefox", win_class, win_title
            elif "code" in proc_name:
                return "VS Code", win_class, win_title
            elif "excel" in proc_name:
                return "Excel", win_class, win_title
            elif "winword" in proc_name:
                return "Word", win_class, win_title
            elif "powerpnt" in proc_name:
                return "PowerPoint", win_class, win_title
            elif "figma" in proc_name:
                return "Figma", win_class, win_title
            elif "photoshop" in proc_name:
                return "Photoshop", win_class, win_title
            else:
                name = proc.name().replace(".exe", "").replace(".EXE", "")
                return name.capitalize(), win_class, win_title
        except Exception:
            return "Windows", "CabinetWClass", "Desktop"

    def _app_monitor_loop(self):
        while self.running:
            try:
                app_name, win_class, _ = self._get_active_app_info()
                with self.lock:
                    self.app_seconds[app_name] += 1
                    if app_name != self.last_active_app:
                        if self.last_active_app is not None:
                            self.app_switches[app_name] += 1
                            self.event_counts["app_switch"] += 1
                        self.last_active_app = app_name
            except Exception:
                pass
            time.sleep(1)

    def _record_event(self, event_type, event_key):
        with self.lock:
            self.event_counts[event_type] += 1
            self.event_counts[event_key] += 1
            
            # Capture active window metadata at event time
            app_name, win_class, win_title = self._get_active_app_info()
            self.last_window_metadata[event_key] = {
                "app_name": app_name,
                "window_class": win_class,
                "window_title": self._sanitize_title(win_title)
            }

    def _on_key_press(self, key):
        try:
            # Shift modifiers
            if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
                self.modifiers['shift'] = True
            # Ctrl modifiers
            elif key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
                self.modifiers['ctrl'] = True
            # Alt modifiers
            elif key in {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r}:
                self.modifiers['alt'] = True
            # Win modifiers
            elif key in {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}:
                self.modifiers['meta'] = True

            # combo checks
            if self.modifiers['ctrl']:
                if key == keyboard.Key.tab:
                    if self.modifiers['shift']:
                        self._record_event("keyboard_shortcut", "ctrl_shift_tab")
                    else:
                        self._record_event("keyboard_shortcut", "ctrl_tab")
                    return
                    
                char = None
                if hasattr(key, 'char') and key.char:
                    char = key.char.lower()
                elif hasattr(key, 'vk') and key.vk:
                    try:
                        char = chr(key.vk).lower()
                    except ValueError:
                        pass
                
                if char == 'c':
                    self._record_event("clipboard_action", "copy")
                elif char == 'v':
                    if self.modifiers['shift']:
                        self._record_event("clipboard_action", "paste_no_format")
                    else:
                        self._record_event("clipboard_action", "paste")
                elif char == 'x':
                    self._record_event("clipboard_action", "cut")
                elif char == 'z':
                    self._record_event("clipboard_action", "undo")
                elif char == 'y':
                    self._record_event("clipboard_action", "redo")
                elif char == 's':
                    self._record_event("clipboard_action", "manual_save")
                elif char == 'f':
                    self._record_event("clipboard_action", "find")
                elif char == 'h':
                    self._record_event("clipboard_action", "replace")
                elif char == 'a':
                    self._record_event("clipboard_action", "select_all")
                elif char == 'p':
                    self._record_event("keyboard_shortcut", "ctrl_p")
                elif char == 'l':
                    self._record_event("keyboard_shortcut", "ctrl_l")
                elif char == 't':
                    if self.modifiers['shift']:
                        self._record_event("browser_action", "reopen_closed_tab")
                    else:
                        self._record_event("browser_action", "new_tab")
                elif char == 'w':
                    self._record_event("browser_action", "close_tab")
                
                self._record_event("keyboard_shortcut", "keyboard_shortcut")
                
            elif self.modifiers['alt']:
                if key == keyboard.Key.tab:
                    self._record_event("keyboard_shortcut", "alt_tab")
        except Exception:
            pass

    def _on_key_release(self, key):
        try:
            if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
                self.modifiers['shift'] = False
            elif key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
                self.modifiers['ctrl'] = False
            elif key in {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r}:
                self.modifiers['alt'] = False
            elif key in {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}:
                self.modifiers['meta'] = False
        except Exception:
            pass

    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            now = time.time()
            if (now - self._last_click_time) < 0.3:
                self._record_event("mouse_click", "double_click")
            else:
                self._record_event("mouse_click", "mouse_click")
            self._last_click_time = now

    def _on_mouse_scroll(self, x, y, dx, dy):
        self._record_event("mouse_click", "mouse_scroll")

    def collect_snapshot(self):
        with self.lock:
            apps = []
            today_str = date.today().isoformat()
            for app_name, sec in self.app_seconds.items():
                if sec > 0 or self.app_switches[app_name] > 0:
                    apps.append({
                        "app_name": app_name,
                        "window_class": "",
                        "active_seconds": sec,
                        "switch_count": self.app_switches[app_name],
                        "observed_on": today_str,
                    })
            
            events = []
            
            # Map event subkeys to category event types
            event_keys = {
                "copy": "clipboard_action",
                "paste": "clipboard_action",
                "paste_no_format": "clipboard_action",
                "cut": "clipboard_action",
                "undo": "clipboard_action",
                "redo": "clipboard_action",
                "manual_save": "clipboard_action",
                "find": "clipboard_action",
                "replace": "clipboard_action",
                "select_all": "clipboard_action",
                "new_tab": "browser_action",
                "reopen_closed_tab": "browser_action",
                "close_tab": "browser_action",
                "alt_tab": "keyboard_shortcut",
                "ctrl_tab": "keyboard_shortcut",
                "ctrl_shift_tab": "keyboard_shortcut",
                "ctrl_p": "keyboard_shortcut",
                "ctrl_l": "keyboard_shortcut",
                "double_click": "mouse_click",
                "mouse_scroll": "mouse_click",
                "mouse_click": "mouse_click",
                "app_switch": "app_switch",
                "keyboard_shortcut": "keyboard_shortcut",
            }

            for key, count in self.event_counts.items():
                if count <= 0:
                    continue
                evt_type = event_keys.get(key, "keyboard_shortcut")
                
                # Retrieve corresponding window metadata
                metadata = {}
                if key in self.last_window_metadata:
                    metadata = self.last_window_metadata[key]
                
                events.append({
                    "event_type": evt_type,
                    "event_key": key,
                    "count": count,
                    "metadata": metadata,
                })
            
            # Reset delta values for next period
            self.app_seconds.clear()
            self.app_switches.clear()
            self.event_counts.clear()
            self.last_window_metadata.clear()
            
            return {
                "applications": apps,
                "events": events,
            }


def anonymize_event(event):
    allowed_keys = {"event_type", "app_name", "event_key", "count", "metadata"}
    cleaned = {key: value for key, value in event.items() if key in allowed_keys}
    cleaned.pop("text", None)
    cleaned.pop("url", None)
    cleaned.pop("clipboard", None)
    cleaned.pop("window_title", None)
    return cleaned
