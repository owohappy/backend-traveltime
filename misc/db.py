import os
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from misc import config, logging

engine = None

def init_database():
    global engine
    
    if engine:
        logging.log("DB already up", "info")
        return

    try:
        cfg = config.config
        debug = cfg['app']['debug']
        db_name = cfg['app']['nameDB']

        if not os.path.exists("./db"):
            os.makedirs("./db")

        filename = f"{db_name}{'_debug' if debug else ''}.db"
        db_url = f"sqlite:///./db/{filename}"

        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        mode = "Debug" if debug else "Prod"
        logging.log(f"{mode} DB ready: {db_url}", "info")

    except Exception as e:
        logging.log(f"DB init failed: {e}", "critical")
        raise

def get_session():
    if not engine:
        logging.log("DB engine not ready", "error")
        raise RuntimeError("DB not initialized")
    
    return Session(engine)

