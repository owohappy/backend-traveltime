from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from misc import config, logging

jsonConfig = config.config
debugBool = jsonConfig['app']['debug']
nameDB = jsonConfig['app']['nameDB']

# Check if tool is running in debug mode
if debugBool:
    try:
        engine = create_engine("sqlite:///./db/" + nameDB + "_debug.db")
        SQLModel.metadata.create_all(engine)
        logging.log("Debug mode enabled, using debug database.", "info")
    except Exception as e:
            logging.log("Error creating engine: " + str(e), "critical")
else:
    try:
        engine = create_engine("sqlite:///./db/" + nameDB + ".db")
        SQLModel.metadata.create_all(engine)
        logging.log("Debug mode disabled, using production database.", "info")
    except Exception as e:
            logging.log("Error creating engine: " + str(e), "critical")


def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
