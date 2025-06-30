import datetime
from colorama import Fore, Back, Style
import os

def write_to_file(filename, text):
    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode) as f:
        f.write(text + '\n')

logfilename = f"log/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.txt"

def log(message: str, level: str = "error"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    colors = {
        "error": Fore.RED,
        "warning": Fore.YELLOW,
        "info": Fore.CYAN,
        "debug": Fore.BLUE,
        "critical": Fore.RED,
        "success": Fore.GREEN
    }
    
    color = colors.get(level, Fore.WHITE)
    data = f"[{timestamp}] {color} {level}:{Fore.WHITE} {message}"
    
    print(data)
    write_to_file(logfilename, data)
    
    if level == "critical":
        exit(1)
    
        
