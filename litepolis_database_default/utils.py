import os
import time # Make sure time is imported
from contextlib import contextmanager
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool # Keep this import
from pymysql.err import ProgrammingError as PyMySQLProgrammingError # Keep this

from litepolis import get_config # Assuming this import exists

DEFAULT_CONFIG = {
    "database_url": "starrocks://litepolis:password@localhost:9030/litepolis_default"
}

database_url = DEFAULT_CONFIG.get("database_url")
if ("PYTEST_CURRENT_TEST" not in os.environ and
    "PYTEST_VERSION" not in os.environ):
    try:
        database_url = get_config("litepolis_database_default", "database_url")
    except Exception as e: # Catch potential errors during config loading
        print(f"Warning: Could not load config, using default DB URL. Error: {e}")
        pass

metadata = MetaData()

# Define engine and SessionLocal globally, but initialize engine as None first
engine = None
SessionLocal = None

def connect_db():
    global engine, SessionLocal
    # Dispose the old engine if it exists
    if engine is not None:
        print("Disposing existing global engine...")
        engine.dispose()

    print(f"Creating new global engine with URL: {database_url}")
    engine = create_engine(database_url,
                            pool_size=5,
                            max_overflow=10,
                            pool_timeout=30,
                            pool_pre_ping=True) # Keep pre-ping

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Global engine and SessionLocal configured.")

# Initialize the engine and session factory when the module loads
# connect_db() # Let's move this call to be explicitly after table creation


# --- MODIFIED wait_for_schema_changes ---
# (Increased retries and delay slightly, added more logging)
def wait_for_schema_changes(engine_to_check, table_name: str, retries=15, delay=1):
    print(f"Starting schema change check for table '{table_name}'...")
    operation_successful = False
    last_exception = None # Keep track of the last error
    for attempt in range(retries):
        time.sleep(delay) # Wait *before* trying
        try:
            with engine_to_check.connect() as connection:
                # Use text() for the raw SQL check
                connection.execute(text(f"SELECT 1 FROM {table_name} LIMIT 0"))
                # Need to commit transaction even for SELECT in some DB/driver combos
                # although likely not needed for StarRocks SELECT, doesn't hurt.
                connection.commit()
            print(f"--- Table '{table_name}' is ready (Attempt {attempt + 1}/{retries}).")
            operation_successful = True
            return True # Exit function on success
        except ProgrammingError as e:
            last_exception = e # Store the last exception
            is_schema_change_error = False
            # Check if original error exists and has the expected structure
            if hasattr(e, 'orig') and isinstance(e.orig, PyMySQLProgrammingError) and len(e.orig.args) >= 2:
                 err_code = e.orig.args[0]
                 err_msg = str(e.orig.args[1]).lower()
                 # Error code 1064 and specific message text
                 if err_code == 1064 and f"table \"{table_name}\"" in err_msg and "schema change operation is in progress" in err_msg:
                      is_schema_change_error = True

            if is_schema_change_error and attempt < retries - 1:
                print(f"--- Schema change ongoing for '{table_name}' (Attempt {attempt + 1}/{retries}). Retrying...")
                # Optional: Increase delay slightly for later retries
                # if attempt > 5: delay = 1.5
                # if attempt > 10: delay = 2
            else:
                # It's a different error, or max retries reached, or unexpected error format
                print(f"--- Failed readiness check for '{table_name}' (Attempt {attempt + 1}/{retries}). Error: {e}")
                # Break the loop on non-schema-change errors or max retries
                break
        except Exception as e: # Catch other potential exceptions during connect/execute
            last_exception = e
            print(f"--- Unexpected error during check for '{table_name}' (Attempt {attempt + 1}/{retries}): {e}")
            # Decide if you want to retry on generic errors or break
            break # Probably safer to break on unknown errors


    if not operation_successful:
         print(f"--- Table '{table_name}' did not become ready after {retries} attempts.")
         if last_exception:
              print(f"--- Last error for '{table_name}': {last_exception}")
         return False # Indicate failure

    # This part is unreachable if loop completed, but added for clarity
    return False


# --- MODIFIED create_db_and_tables ---
def create_db_and_tables():
    global engine # Need to modify the global engine

    # Create a temporary engine specifically for DDL using NullPool
    print("Creating temporary engine for DDL...")
    engine_ddl = create_engine(database_url, poolclass=NullPool, echo=False) # echo=False for less noise usually
    try:
        print(f"Running metadata.create_all on {len(metadata.tables)} tables...")
        # This single call attempts to create all tables defined in metadata
        metadata.create_all(engine_ddl)
        print("metadata.create_all command sent.")
    except Exception as e:
        print(f"ERROR during metadata.create_all: {e}")
        raise # Re-raise critical DDL errors
    finally:
        print("Disposing of temporary DDL engine.")
        engine_ddl.dispose()

    # Now, create a *checking* engine (can use pooling) to verify ALL tables
    print("Creating engine for schema change checks...")
    engine_check = create_engine(database_url, pool_pre_ping=True, echo=False)
    all_tables_ready = True
    try:
        print("Checking readiness for all tables...")
        # Check each table defined in the metadata
        for table_name in metadata.tables.keys():
            if not wait_for_schema_changes(engine_check, table_name=table_name):
                print(f"FATAL: Table '{table_name}' failed readiness check.")
                all_tables_ready = False
                # Decide whether to break or check all tables regardless
                # break # Option 1: Stop checking if one fails
        if not all_tables_ready:
             # Option 2: Raise an error if not all tables became ready
             raise RuntimeError("Not all tables became ready after creation.")

    finally:
        print("Disposing of schema check engine.")
        engine_check.dispose()

    # --- IMPORTANT: Reset the main global engine ---
    print("Resetting the main global engine for application use...")
    connect_db() # This disposes the old global 'engine' and creates a new one

    print("Database initialization complete. All checked tables are ready.")


@contextmanager
def get_session() -> Session:
    # Ensure the global engine/SessionLocal is initialized
    if SessionLocal is None:
        print("WARNING: get_session called before SessionLocal was initialized. Running connect_db().")
        # This might indicate an issue with initialization order if it happens frequently
        connect_db()
        if SessionLocal is None: # Still None after connect_db? Something is wrong.
             raise RuntimeError("Failed to initialize SessionLocal in connect_db.")

    db = SessionLocal()
    try:
        yield db
    except Exception: # Rollback on exception
         db.rollback()
         raise # Re-raise the exception
    finally:
        db.close()

# --- Ensure create_db_and_tables is called appropriately ---
# This is currently called at the bottom of Actor.py when it's imported.
# Consider moving this to a dedicated setup script or a pytest fixture
# for better control, especially in test environments.