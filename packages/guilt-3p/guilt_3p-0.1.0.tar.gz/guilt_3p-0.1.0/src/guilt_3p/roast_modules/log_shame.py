import os
import datetime
def log_shame(url):
    try:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
        file_path = os.path.join(desktop, "HALL_OF_SHAME.txt")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(file_path, "a") as f:
            f.write(f"[{timestamp}] WASTED TIME ON: {url}\n")
    except:
        pass