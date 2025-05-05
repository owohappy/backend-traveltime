import datetime
from colorama import Fore, Back, Style

def log(message: str, type:str = "error"):
    '''
    message: str
    type:str
    Possible types: 
        error = logging for error
        warning = logging for warning
        info = logging for info 
        debug = logging for debug
    '''
    current_time = datetime.datetime.now().strftime("%H:%M:%S")

    if (type == "error"):
        print(f"[{current_time}] {Fore.RED} {type}: {Fore.WHITE} {message}")
        return None
    if (type == "warning"):
        print(f"[{current_time}] {Fore.YELLOW} {type}:{Fore.WHITE} {message}")
        return None
    if (type == "info"):
        print(f"[{current_time}] {Fore.CYAN} {type}:{Fore.WHITE} {message}")
        return None
    if (type == "debug"):
        print(f"[{current_time}] {Fore.BLUE} {type}:{Fore.WHITE} {message}")
        return None
    
        
