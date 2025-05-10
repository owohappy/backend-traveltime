import json 
from misc import logging
global config

try:
    # Load data from config.json
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
# throw error and end program if config.json is not found


except FileNotFoundError:
    #Create config.json with default values
    default_config = {
    "app": {
      "debug": True,
      "baseURL": "http://localhost:8000",
      "nameDB": "test",
      "jwtSecretKey": ""
    },
    "email":
    {
        "smtp": {
            "host": "smtp.example.com",
            "port": 587,
            "username": "",
            "password": "",
            "senderEmail":""
        },
        "enabled": False

    }
}
    logging.log("Config file not found", "critical")

