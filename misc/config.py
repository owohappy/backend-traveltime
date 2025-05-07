import json 

global config

with open('config.json', 'r') as config_file:
    config = json.load(config_file)