# app/database.py
import logging
import databases
import sqlalchemy # databases uses SQLAlchemy core components
from pathlib import Path

from app.config import settings
from app.auth import get_password_hash # For hashing default admin password

logger = logging.getLogger(__name__)

# Create the database URL (already done in config, just using it here)
DATABASE_URL = settings.DATABASE_URL

# Create a 'databases' database object
# force_rollback=True can be useful for testing
database = databases.Database(DATABASE_URL) # , force_rollback=False

# SQLAlchemy metadata (optional but good practice if you plan to use ORM later)
metadata = sqlalchemy.MetaData()

async def connect_db():
    """
    Connects to the database defined in the settings.
    """
    try:
        await database.connect()
        logger.info("Database connection established.")
    except Exception as e:
        logger.exception(f"Failed to connect to the database: {e}")
        raise # Re-raise exception to potentially stop app startup

async def disconnect_db():
    """
    Disconnects from the database.
    """
    try:
        await database.disconnect()
        logger.info("Database connection closed.")
    except Exception as e:
        logger.exception(f"Failed to disconnect from the database: {e}")


async def initialize_database():
    """
    Initializes the database by executing the init.sql script
    and ensures the default admin user exists.
    """
    if not database.is_connected:
        logger.warning("Database not connected during initialization attempt. Connecting now.")
        await connect_db() # Ensure connection before proceeding

    try:
        # --- Step 1: Execute init.sql script ---
        sql_script_path = Path(__file__).parent.parent / "sql" / "init.sql"
        if sql_script_path.exists():
            logger.info(f"Executing database initialization script: {sql_script_path}")
            with open(sql_script_path, "r", encoding="utf-8") as f:
                # Simple split by semicolon; might need refinement for complex SQL
                sql_statements = f.read().split(';')
                async with database.transaction(): # Use transaction for script execution
                    for statement in sql_statements:
                        clean_statement = statement.strip()
                        if clean_statement: # Avoid executing empty strings
                            try:
                                await database.execute(query=clean_statement)
                            except Exception as e:
                                # Log errors (e.g., table already exists) but continue
                                logger.warning(f"Error executing SQL statement: {e}. Statement: '{clean_statement[:100]}...'")
            logger.info("Database schema initialization script executed.")
        else:
            logger.warning(f"Database initialization script not found at: {sql_script_path}")

        # --- Step 2: Check and create default admin user ---
        logger.info(f"Checking for default admin user: {settings.DEFAULT_ADMIN_USER}")
        query = "SELECT id FROM users WHERE username = :username"
        existing_user = await database.fetch_one(query=query, values={"username": settings.DEFAULT_ADMIN_USER})

        if existing_user:
            logger.info(f"Default admin user '{settings.DEFAULT_ADMIN_USER}' already exists.")
        else:
            logger.info(f"Default admin user '{settings.DEFAULT_ADMIN_USER}' not found. Creating...")
            hashed_password = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            insert_query = """
                INSERT INTO users (username, hashed_password, is_active)
                VALUES (:username, :hashed_password, TRUE)
            """
            values = {
                "username": settings.DEFAULT_ADMIN_USER,
                "hashed_password": hashed_password
            }
            try:
                await database.execute(query=insert_query, values=values)
                logger.info(f"Default admin user '{settings.DEFAULT_ADMIN_USER}' created successfully.")
            except Exception as e:
                # Catch potential unique constraint errors if run concurrently (less likely on startup)
                logger.exception(f"Failed to create default admin user '{settings.DEFAULT_ADMIN_USER}': {e}")
                # Check again if it exists now, maybe another process created it
                existing_user = await database.fetch_one(query=query, values={"username": settings.DEFAULT_ADMIN_USER})
                if not existing_user:
                     raise # Re-raise if creation truly failed

    except Exception as e:
        logger.exception(f"An error occurred during database initialization: {e}")
        # Depending on severity, you might want to stop the application
        # For now, we log and continue, but critical failures might need `raise`
