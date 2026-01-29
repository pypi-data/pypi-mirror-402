import threading
import random
import os
import ctypes
from gtts import gTTS
from playsound import playsound
# from data.roasts import ROASTS # OLD
# from data.praises import PRAISES # OLD
from ..config import config

def show_error_popup(text, error_type):
    
    try:
        if error_type == "roast":
            # Critical Error Icon 
            style = 0x10 | 0x1000
            title = "ROAST INCOMING !!!"
        else:
            # Info Icon  for Success
            style = 0x40 | 0x1000 
            title = "GREAT WORK GETTING BACK"

        ctypes.windll.user32.MessageBoxW(0, text, title, style)
    except:
        pass

def play_audio_and_popup(text, speak_type):
    """
    Generates MP3, plays it, and launches the popup simultaneously.
    """
    def _run():
        try:
            
            filename = f"temp_speech_{random.randint(1000, 9999)}.mp3"
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filename)

            popup_thread = threading.Thread(target=show_error_popup, args=(text,speak_type), daemon=True)
            popup_thread.start()

            # 3. Play the audio
            playsound(filename)

            os.remove(filename)
            
        except Exception as e:
            print(f"Audio Error: {e}")

    threading.Thread(target=_run).start()

def speak(text, speak_type="info"): # Added default arg "info" because it was called with 1 arg in some places
    play_audio_and_popup(text, speak_type)

def speak_alert(speak_type):
    phrase = ""
    if speak_type == "roast":
        phrase = random.choice(config.roasts)
        play_audio_and_popup(phrase, speak_type)
    else:
        phrase = random.choice(config.praises)
        play_audio_and_popup(phrase, speak_type)