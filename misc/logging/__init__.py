import datetime
from colorama import Fore, Back, Style
import os

def write_to_file(filename, line_of_text):
    # Check if the file exists
    if not os.path.exists(filename):
        # Create the file and write the line
        with open(filename, 'w') as file:
            file.write(line_of_text + '\n')
        print(f"File '{filename}' created and text added.")
    else:
        # Append to the existing file
        with open(filename, 'a') as file:
            file.write(line_of_text + '\n')
        print(f"Text appended to existing file '{filename}'.")

logfilename =  "log/" + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')) + ".txt"

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
        data = f"[{current_time}] {Fore.RED} {type}: {Fore.WHITE} {message}"
        print(data)
        write_to_file(logfilename, data)
        return None
    if (type == "warning"):
        data = f"[{current_time}] {Fore.YELLOW} {type}:{Fore.WHITE} {message}"
        print(data)
        write_to_file(logfilename, data)
        return None
    if (type == "info"):
        data = f"[{current_time}] {Fore.CYAN} {type}:{Fore.WHITE} {message}"
        print(data)
        write_to_file(logfilename, data)
        return None
    if (type == "debug"):
        data = f"[{current_time}] {Fore.BLUE} {type}:{Fore.WHITE} {message}"
        print(data)
        write_to_file(logfilename, data)
        return None
    if (type == "critical"):
        data = f"[{current_time}] {Fore.RED} {type}:{Fore.RED} {message}"
        print(data)
        write_to_file(logfilename, data)
        exit(1)
        return None
    
        
