import json
import os
import secrets
from misc import logging

def generate_default_config():
    return {
        "app": {
            "debug": True,
            "baseURL": "http://localhost:8000",
            "nameDB": "traveltime",
            "jwtSecretKey": secrets.token_hex(32)
        },
        "email": {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "username": "",
                "password": "",
                "senderEmail": ""
            },
            "subjects": {
                "verifyEmail": "Verify your TravelTime account",
                "resetPassword": "Reset your TravelTime password",
                "enableMFA": "Enable Two-Factor Authentication"
            },
            "enabled": False
        }
    }

def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # env overrides
        if os.getenv("APP_DEBUG"):
            config["app"]["debug"] = os.getenv("APP_DEBUG").lower() == "true"
        if os.getenv("APP_BASE_URL"):
            config["app"]["baseURL"] = os.getenv("APP_BASE_URL")
        if os.getenv("JWT_SECRET_KEY"):
            config["app"]["jwtSecretKey"] = os.getenv("JWT_SECRET_KEY")
            
        if os.getenv("EMAIL_ENABLED"):
            config["email"]["enabled"] = os.getenv("EMAIL_ENABLED").lower() == "true"
        if os.getenv("EMAIL_HOST"):
            config["email"]["smtp"]["host"] = os.getenv("EMAIL_HOST")
        if os.getenv("EMAIL_PORT"):
            config["email"]["smtp"]["port"] = int(os.getenv("EMAIL_PORT"))
        if os.getenv("EMAIL_USERNAME"):
            config["email"]["smtp"]["username"] = os.getenv("EMAIL_USERNAME")
        if os.getenv("EMAIL_PASSWORD"):
            config["email"]["smtp"]["password"] = os.getenv("EMAIL_PASSWORD")
        if os.getenv("EMAIL_SENDER"):
            config["email"]["smtp"]["senderEmail"] = os.getenv("EMAIL_SENDER")
        
        return config
        
    except FileNotFoundError:
        default_config = generate_default_config()
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        logging.log("Created default config.json", "warning")
        return default_config
    except Exception as e:
        logging.log(f"Config error: {e}", "critical")
        exit(1)
        
config = load_config()

