import win32gui
import win32con
import ctypes

def bring_vscode_to_front():
    def enum_handler(hwnd, ctx):
        title = win32gui.GetWindowText(hwnd).lower()
        
        if "visual studio code" in title or "cmd" in title or "powershell" in title:
            try:
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
                
                win32gui.ShowWindow(hwnd, 9)
                
                win32gui.SetForegroundWindow(hwnd)
                
                # print("✨ Teleported you back to work.")
            except Exception as e:
                print(f"Failed to move window: {e}")
            
            return False # Stop searching once found
        return True

    try:
        win32gui.EnumWindows(enum_handler, None)
    except:
        pass