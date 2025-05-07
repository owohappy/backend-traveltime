import json 
from misc import logging
global config

try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    logging.log("Config file not found", "critical")
