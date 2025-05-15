import os
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from misc import config, logging

# Global engine variable, to be initialized by init_database()
engine = None

def init_database():
    """
    Initializes the database engine and creates all tables defined in SQLModel.metadata.
    This function should be called once at application startup, after all models
    have been imported (e.g., by importing misc.models).
    """
    global engine

    if engine is not None:
        logging.log("Database already initialized.", "info")
        return

    try:
        jsonConfig = config.config
        debugBool = jsonConfig['app']['debug']
        nameDB = jsonConfig['app']['nameDB']

        db_folder = "./db"
        # Create the database directory if it doesn't exist
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)
            logging.log(f"Created database directory: {db_folder}", "info")

        db_filename = f"{nameDB}{'_debug' if debugBool else ''}.db"
        db_url = f"sqlite:///{os.path.join(db_folder, db_filename)}" # Use os.path.join for robustness

        engine = create_engine(db_url)

        # IMPORTANT: This is where tables are created.
        # All SQLModel classes (e.g., User, UserPoints from misc/models.py)
        # must have been imported before this line is executed so they are registered
        # in SQLModel.metadata.
        SQLModel.metadata.create_all(engine)

        mode = "Debug" if debugBool else "Production"
        logging.log(f"{mode} database initialized successfully using {db_url}", "info")

    except Exception as e:
        logging.log(f"Critical error initializing database: {str(e)}", "critical")
        # Re-raise the exception to halt application startup if DB initialization fails
        raise

def get_session():
    """
    Provides a database session.
    Ensures init_database() has been called.
    """
    if engine is None:
        error_msg = "Database engine not initialized. Call init_database() first."
        logging.log(error_msg, "error")
        # This will likely cause a 500 error if a request tries to get a session before init.
        raise RuntimeError(error_msg)
    
    with Session(engine) as session:
        return session
