import os
import time

# from roast_modules.roaster_speaker import speak # OLD
from ..roast_modules.roaster_speaker import speak

# from app.state import current_state # OLD
from ..state import current_state

def handle_user_input():

    
    print("\ncommands: 'break <mins>' (1-10) | 'quit'\n")
    
    while True:
        try:
            user_cmd = input().strip().lower()
            
            if user_cmd == "quit":
                print("Exiting...")
                os._exit(0) # Force kill all threads
            
            if user_cmd.startswith("break"):
                try:
                    parts = user_cmd.split()
                    if len(parts) < 2:
                        print(">>")
                        continue
                        
                    mins = int(parts[1])
                    
                    if 1 <= mins <= 10:
                        # Set the Break Timer
                        current_state.BREAK_UNTIL_TIMESTAMP = time.time() + (mins * 60)
                        current_state.BREAK_WARNING_SENT = False
                        
                        print(f"\nBREAK STARTED: See you in {mins} minutes.")
                        speak(f"Enjoy your break. You have {mins} minutes.")
                    else:
                        print(">>")
                except ValueError:
                    print(">>")
                    
        except:
            pass