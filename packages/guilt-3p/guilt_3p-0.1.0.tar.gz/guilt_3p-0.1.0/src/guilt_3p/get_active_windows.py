import subprocess
import psutil


class ActiveWindows:
    def __init__(self,os):
        self.os = os
    
    def get_active_window_info_windows(self):
        """Windows: Returns (app_name, window_title)"""
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            h_wnd = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h_wnd, ctypes.byref(pid))
            process = psutil.Process(pid.value)
            app_name = process.name().lower().replace(".exe", "")
            
            length = user32.GetWindowTextLengthW(h_wnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(h_wnd, buf, length + 1)
            window_title = buf.value
            return app_name, window_title
        except:
            return None, None



    def get_active_window_info_macos(self):
        """macOS: Returns (app_name, window_title, url)"""
        script = '''
        global frontApp, frontAppName, windowTitle
        set windowTitle to ""
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName
                try
                    set windowTitle to value of attribute "AXTitle" of window 1
                end try
            end tell
        end tell
        return {frontAppName, windowTitle}
        '''
        
        try:
            result = subprocess.check_output(["osascript", "-e", script]).decode("utf-8").strip()
            app_name, window_title = result.split(", ")
        except:
            app_name, window_title = "Unknown", "Unknown"

            
        return app_name, window_title


    
    def get_active_window_info_linux(self):
        """Linux: Returns (app_name, window_title). Requires xdotool."""
        try:
            window_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode("utf-8").strip()
            window_title = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode("utf-8").strip()
            pid = subprocess.check_output(["xdotool", "getwindowpid", window_id]).decode("utf-8").strip()
            process = psutil.Process(int(pid))
            app_name = process.name()
            return app_name, window_title
        except:
            return "Unknown", "Unknown"
    
    def get_active_windows(self):
        if self.os == "win32":
            return self.get_active_window_info_windows()
        elif self.os == "darwin":
            return self.get_active_window_info_macos()
        elif self.os.startswith("linux"):
            return self.get_active_window_info_linux()
        else:
            return None
