from random import random
import sys
import threading
import time
import argparse
import shutil
import os
from pathlib import Path
from flask import Flask, request
from flask_cors import CORS
from werkzeug.serving import make_server
import logging

# Rich imports for pretty CLI
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import print as rprint

# Config
from .config import config

# Relative imports
from .get_active_windows import ActiveWindows
from .roast_modules.roaster_speaker import speak_alert, speak
from .roast_modules.log_shame import log_shame
from .roast_modules.send_nag import send_nag, send_alert
from .roast_modules.bring_vscode import bring_vscode_to_front
from .utils.break_input import handle_user_input
from .state import current_state

console = Console()

SELF_TITLES = ["ROAST INCOMING !!!", "GREAT WORK GETTING BACK", "New notification", "python"]

# Setup logging to file for debugging
logging.basicConfig(
    filename='guilt_3p_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Suppress Flask CLI output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

CORS(app) 

ActiveWindowsFetcher = ActiveWindows(sys.platform)

CONSECUTIVE_SECONDS = 0

@app.route('/update', methods=['POST'])
def receive_url():
    try:
        data = request.json
        url = data.get('url', '')
        
        # Log received URL for debugging
        logger.debug(f"Received URL update: {url}")
        
        # Update the global variable
        current_state.CURRENT_BROWSER_URL = url
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in receive_url: {e}")
        return "Error", 500


@app.route('/health', methods=['GET'])
def health_check():
    return "Activity Spy is running.", 200

def run_server():
    """Starts the Flask server in a separate thread"""
    try:
        logger.info("Starting Flask server on port 5000...")
        # Use make_server directly to avoid "Serving Flask app" banner
        server = make_server('127.0.0.1', 5000, app, threaded=True)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")

def print_banner():
    ascii_art = """
  ░██████             ░██░██    ░██        ░██████  ░█████████  
 ░██   ░██               ░██    ░██       ░██   ░██ ░██     ░██ 
░██        ░██    ░██ ░██░██ ░████████          ░██ ░██     ░██ 
░██  █████ ░██    ░██ ░██░██    ░██         ░█████  ░█████████  
░██     ██ ░██    ░██ ░██░██    ░██             ░██ ░██         
 ░██  ░███ ░██   ░███ ░██░██    ░██       ░██   ░██ ░██         
  ░█████░█  ░█████░██ ░██░██     ░████     ░██████  ░██         
                                                                
                                                                
  
     Parama-Poi-Padi da  (or)  Petty Productivity Patrol
    """
    
    panel = Panel(
        Align.center(
            Text(ascii_art, style="bold cyan") 
        ),
        title="[bold green]Active[/]",
        border_style="cyan"
    )
    console.print(panel)

def setup_extension():
    ext_src = Path(__file__).parent / "assets" / "extension"
    console.print(f"[bold blue]Extension source found at:[/bold blue] {ext_src}")
    
    # Check if user wants to copy
    console.print(Panel("""[yellow]You need to load this extension in your browser (Edge/Chrome).[/yellow]
1. Open Extensions page (chrome://extensions or edge://extensions)
2. Enable Developer Mode
3. Click 'Load unpacked'
4. Select the folder shown above""", title="Setup Instructions"))

    console.print("\n[bold red]IMPORTANT:[/bold red] If you renamed the project folder, you MUST reload the extension!")
    
    # Optional: Copy to Documents
    docs_dir = Path(os.path.expanduser("~/Documents")) / "RoastProtoExtension"
    console.print(f"\nWould you like to copy the extension to [cyan]{docs_dir}[/cyan] for safekeeping? (y/n)")
    console.print("This prevents it from being deleted if you update/remove the python package.", style="dim")
    choice = input("Copy? (y/N): ").lower()
    if choice == 'y':
        if docs_dir.exists():
            try:
                shutil.rmtree(docs_dir)
            except Exception as e:
                console.print(f"[red]Error removing old extension folder: {e}[/red]")
                return
        try:
            shutil.copytree(ext_src, docs_dir)
            console.print(f"[green]Copied to {docs_dir}. Point your browser there.[/green]")
        except Exception as e:
            console.print(f"[red]Error copying extension: {e}[/red]")
            console.print(f"Please use the package location: {ext_src}")
    else:
        console.print("Okay, using the package location.")

def main():
    global CONSECUTIVE_SECONDS

    CONSECUTIVE_WORK_SECONDS = 0

    print_banner()
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=handle_user_input, daemon=True).start()
    
    logger.info("Main loop starting...")
    
    try:
        while True:
            current_time = time.time()
            
            if current_time < current_state.BREAK_UNTIL_TIMESTAMP:
                remaining = int(current_state.BREAK_UNTIL_TIMESTAMP - current_time)
                
                if remaining <= 10 and not current_state.BREAK_WARNING_SENT:
                    console.print("\n [bold yellow]BREAK ENDING SOON[/bold yellow]")
                    speak("Ten seconds left. Prepare to work.")
                    send_alert("Break Ending", "10 seconds remaining.")
                    current_state.BREAK_WARNING_SENT = True
                
                time.sleep(1)
                continue
                
            # If break JUST finished
            if current_state.BREAK_UNTIL_TIMESTAMP > 0 and current_time >= current_state.BREAK_UNTIL_TIMESTAMP:
                console.print("\n[bold red]BREAK OVER. BACK TO WORK.[/bold red]")
                speak("Break is over. Get back to code.")
                current_state.BREAK_UNTIL_TIMESTAMP = 0 # Reset so we dont trigger this again
            
            app_name, window_title = ActiveWindowsFetcher.get_active_windows()
            # print(f"Active App: {app_name} | Title: {window_title}")


            is_self_alert = False
            for title in SELF_TITLES:
                if title.lower() in window_title.lower() or title.lower() in app_name.lower():
                    is_self_alert = True
                    break
                    
            if is_self_alert:
                console.print("[dim] -> Alert window detected. Pausing monitoring...[/dim]")
                time.sleep(1) 
                continue
            is_distracted = False
            
            if any(b in app_name for b in config.browsers):
                if any(d in current_state.CURRENT_BROWSER_URL for d in config.forbidden):
                    is_distracted = True
            
            if is_distracted:
                CONSECUTIVE_WORK_SECONDS = 0
                CONSECUTIVE_SECONDS += 1
                console.print(f"[red]Distracted for: {CONSECUTIVE_SECONDS}s[/red]")

                if CONSECUTIVE_SECONDS == 2:
                    console.print("\n[bold red on white]!!! DISTRACTION DETECTED !!![/bold red on white]")

                    send_nag()
                if CONSECUTIVE_SECONDS == 10:
                    speak_alert("roast") # Speak a roast
                
                if CONSECUTIVE_SECONDS == 20:
                    log_shame(current_state.CURRENT_BROWSER_URL)
                    send_alert("CHECK YOUR DESKTOP - HALL OF SHAME", "Your distraction has been logged in hall of shame.")
                    speak_alert("roast") # Speak again

                if CONSECUTIVE_SECONDS > 30 and CONSECUTIVE_SECONDS % 10 == 0:
                    console.print("[bold white on red]!!! FORCING WINDOW SWAP !!![/bold white on red]")
                    bring_vscode_to_front()

            else:
                if CONSECUTIVE_SECONDS > 0:
                    # We enter "Probation Mode" to verify they are actually back.
                    
                    CONSECUTIVE_WORK_SECONDS += 1
                    console.print(f"[cyan]-> Verifying return to work: {CONSECUTIVE_WORK_SECONDS}/5s[/cyan]")
                    
                    if CONSECUTIVE_WORK_SECONDS >= 5:
                        # have stayed in work mode for 5 full seconds.
                        
                        if CONSECUTIVE_SECONDS > 5: 
                            console.print("[bold green]-> Return verified! Praise delivered.[/bold green]")
                            speak_alert("praise")
                        else:
                            console.print("[green]-> Return verified. Distraction was short, silent reset.[/green]")
                        
                        # Reset the counters now that verification is done
                        CONSECUTIVE_SECONDS = 0
                        CONSECUTIVE_WORK_SECONDS = 0
                else:
                    # They are working and have no pending distraction. All good.
                    pass

            time.sleep(1)


    except KeyboardInterrupt:
        console.print("\n[bold]Exiting.[/bold]")

def entry_point():
    parser = argparse.ArgumentParser(description="Guilt-3P - Activity Spy")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("run", help="Run the application")
    subparsers.add_parser("setup-extension", help="Setup the browser extension")
    subparsers.add_parser("init-config", help="Initialize configuration file")
    
    args = parser.parse_args()
    
    if args.command == "setup-extension":
        setup_extension()
    elif args.command == "init-config":
        config.create_default_config()
    else:
        # Default to running the app if no command or 'run' command
        main()

if __name__ == "__main__":
    entry_point()
