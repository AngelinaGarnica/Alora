import logging
import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path

# Configure basic logging if this script is run directly or no handlers are configured
if __name__ == "__main__" or not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')

logger = logging.getLogger(__name__)

# Secret keys .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# LLM
llm = None
if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"[config] Failed to initialize LLM: {e}")
else:
    logger.warning("[config] GOOGLE_API_KEY not set. LLM will not be initialized.")

# DB
chinook_db_path = Path("data/chinook.db")
chinook_sql_file = Path("data/chinook.sql")

# Ensure parent directory for the database exists
chinook_db_path.parent.mkdir(parents=True, exist_ok=True)

# Check if the database file existed *before* attempting to connect.
# sqlite3.connect() will create the file if it doesn't exist.
db_existed_prior_to_connect = chinook_db_path.exists()
logger.info(f"[config] Pre-connect check: DB file '{chinook_db_path}' exists: {db_existed_prior_to_connect}")
logger.info(f"[config] Pre-connect check: SQL file '{chinook_sql_file}' exists: {chinook_sql_file.exists()}")

# Connect to the DB (this will create it if it doesn't exist yet)
conn = None
cursor = None
try:
    conn = sqlite3.connect(chinook_db_path)
    cursor = conn.cursor()
    logger.info(f"[config] Successfully connected to database: {chinook_db_path}")

    # If the DB file did not exist before connecting AND the SQL script file exists,
    # then populate the newly created database.
    if not db_existed_prior_to_connect and chinook_sql_file.exists():
        logger.info(f"[config] Database '{chinook_db_path}' did not exist. Attempting to create from '{chinook_sql_file}'...")
        try:
            with open(chinook_sql_file, "r", encoding="utf-8") as f:
                sql_script = f.read()
            if not sql_script.strip():
                logger.warning(f"[config] SQL script file '{chinook_sql_file}' is empty. Database will not be populated.")
            else:
                cursor.executescript(sql_script)
                conn.commit()
                logger.info(f"[config] Database created and populated successfully from '{chinook_sql_file}'.")
        except Exception as e:
            logger.error(f"[config] Error executing SQL script from '{chinook_sql_file}': {e}")
    elif db_existed_prior_to_connect:
        logger.info(f"[config] Connected to existing database: {chinook_db_path}")
    elif not chinook_sql_file.exists(): 
        logger.warning(f"[config] SQL file '{chinook_sql_file}' not found. Connected to a new, empty database at '{chinook_db_path}'.")

except Exception as e:
    logger.critical(f"[config] Failed to connect to or initialize database '{chinook_db_path}': {e}")


class DBWrapper:
    def __init__(self, db_connection):
        if db_connection is None:
            logger.warning("[DBWrapper] DBWrapper initialized with no database connection.")
        self.conn = db_connection

    def run(self, query: str):
        if not self.conn:
            logger.error("[DBWrapper] No database connection available for run().")
            return [[f"⚠️ Error: No database connection."]] # Return as list of lists
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Exception as e:
            logger.error(f"[DBWrapper] Error executing query '{query}': {e}")
            return [[f"⚠️ Error: {e}"]] # Return as list of lists

    def get_usable_table_names(self):
        if not self.conn:
            logger.error("[DBWrapper] No database connection available for get_usable_table_names().")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            logger.error(f"[DBWrapper] Error getting table names: {e}")
            return []

db = DBWrapper(conn)

if __name__ == "__main__":
    print(f"--- Running {Path(__file__).name} directly ---")
    # connexion check
    if conn:
        try:
            # db instance is already created globally using the global 'conn'
            tables = db.get_usable_table_names()
            print("Tables:", tables)
            if not tables:
                if chinook_sql_file.exists():
                    print(f"WARNING: No tables found. SQL file '{chinook_sql_file.resolve()}' exists.")
                    print("  Possible causes:")
                    print("  1. The sql file is empty or does not create tables.")
                    print("  2. There was an error during the execution of the SQL script (see the logs above).")
                    print(f"  3. The database '{chinook_db_path.resolve()}' exists but is empty.")
                else:
                    print(f"WARNING: No tables found and the SQL file '{chinook_sql_file.resolve()}' does not exist.")
                    print(f"  You have connected to an empty database '{chinook_db_path.resolve()}'.")
        except Exception as e:
            print(f"Error interacting with the databade: {e}")
    else:
        print(f"CRITICAL: The database connection could not be established. Review previous logs. '{chinook_db_path}'.")