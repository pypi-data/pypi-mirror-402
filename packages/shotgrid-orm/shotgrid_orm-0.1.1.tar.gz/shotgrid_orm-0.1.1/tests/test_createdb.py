"""Tests for database creation from schema."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


def test_create_database_from_schema(sg_orm, test_db_path):
    """Test creating a database with all tables from schema."""
    engine = create_engine(f"sqlite+pysqlite:///{test_db_path}", echo=False)
    session = Session(engine)

    # Drop all tables if they exist
    sg_orm.Base.metadata.drop_all(bind=engine)

    # Create all tables
    sg_orm.Base.metadata.create_all(engine)

    # Verify tables were created using inspector
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    # Check that expected tables exist
    assert "Project" in table_names
    assert "Shot" in table_names
    assert "Asset" in table_names
    assert "Sequence" in table_names

    session.close()


def test_drop_and_recreate_tables(sg_orm, test_db_path):
    """Test dropping and recreating tables."""
    engine = create_engine(f"sqlite+pysqlite:///{test_db_path}", echo=False)

    # Create tables
    sg_orm.Base.metadata.create_all(engine)

    # Verify tables exist
    inspector = inspect(engine)
    assert "Project" in inspector.get_table_names()

    # Drop all tables
    sg_orm.Base.metadata.drop_all(bind=engine)

    # Verify tables are gone
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert len(table_names) == 0

    # Recreate tables
    sg_orm.Base.metadata.create_all(engine)

    # Verify tables are back (need new inspector to refresh cache)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert len(table_names) > 0
    assert "Project" in table_names
