import json
import os
import secrets
from misc import logging

def generate_default_config():
    """Generate a default configuration with secure values"""
    return {
        "app": {
            "debug": True,
            "baseURL": "http://localhost:8000",
            "nameDB": "traveltime",
            "jwtSecretKey": secrets.token_hex(32)  # Generate secure JWT key
        },
        "email": {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "username": "",
                "password": "",
                "senderEmail": ""
            },
            "enabled": False
        }
    }

def load_config():
    """Load configuration with fallback to defaults and environment variables"""
    try:
        # Try to load from file
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            
        # Override with environment variables if present
        if os.getenv("APP_DEBUG"):
            config["app"]["debug"] = os.getenv("APP_DEBUG").lower() == "true"
        if os.getenv("APP_BASE_URL"):
            config["app"]["baseURL"] = os.getenv("APP_BASE_URL")
        if os.getenv("JWT_SECRET_KEY"):
            config["app"]["jwtSecretKey"] = os.getenv("JWT_SECRET_KEY")
            
        # Email config from environment
        if os.getenv("EMAIL_ENABLED"):
            config["email"]["enabled"] = os.getenv("EMAIL_ENABLED").lower() == "true"
        if os.getenv("EMAIL_HOST"):
            config["email"]["smtp"]["host"] = os.getenv("EMAIL_HOST")
        
        return config
        
    except FileNotFoundError:
        # Create default config
        default_config = generate_default_config()
        with open('config.json', 'w') as config_file:
            json.dump(default_config, config_file, indent=2)
        logging.log("Created default config.json file", "warning")
        return default_config
    except Exception as e:
        logging.log(f"Error loading config: {str(e)}", "critical")
        exit(1)
        
config = load_config()

