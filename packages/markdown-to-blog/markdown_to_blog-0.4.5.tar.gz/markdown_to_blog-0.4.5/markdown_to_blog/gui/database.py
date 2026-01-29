import os
from pathlib import Path
from tortoise import Tortoise, connections
from tortoise.exceptions import DBConnectionError
from loguru import logger


def get_db_path():
    """Get the database file path"""
    home = Path.home()
    db_dir = home / ".markdown_to_blog"
    db_dir.mkdir(exist_ok=True)
    return str(db_dir / "mdb.db")


TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{get_db_path()}"
    },
    "apps": {
        "models": {
            "models": ["markdown_to_blog.gui.models"],
            "default_connection": "default",
        }
    }
}


async def init_db():
    """Initialize the database"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    # Add is_converted column if it doesn't exist
    await migrate_add_is_converted()
    
    logger.info(f"Database initialized at: {get_db_path()}")


async def migrate_add_is_converted():
    """Add is_converted column to publish_records table if it doesn't exist"""
    try:
        db = connections.get("default")
        
        # Check if is_converted column exists
        cursor = await db.execute_query_dict(
            "PRAGMA table_info(publish_records)"
        )
        
        columns = [col['name'] for col in cursor]
        
        if 'is_converted' not in columns:
            # Add the column
            await db.execute_query(
                "ALTER TABLE publish_records ADD COLUMN is_converted INTEGER DEFAULT 0"
            )
            logger.info("Added is_converted column to publish_records table")
    except Exception as e:
        logger.error(f"Error adding is_converted column: {e}")
        # Continue even if migration fails


async def close_db():
    """Close database connections"""
    await Tortoise.close_connections()