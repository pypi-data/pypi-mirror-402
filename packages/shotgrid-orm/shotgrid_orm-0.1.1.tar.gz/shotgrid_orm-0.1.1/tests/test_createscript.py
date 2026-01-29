"""Tests for script creation from various schema sources."""

# ruff: noqa: I001
import os
import pytest

from shotgrid_orm import SGORM, SchemaType


def test_create_script_from_json_file(sg_orm, temp_dir):
    """Test creating a Python script from JSON schema file."""
    script_path = temp_dir / "sgmodel_from_file.py"
    sg_orm.create_script(str(script_path))

    # Verify script was created
    assert script_path.exists()
    content = script_path.read_text()

    # Verify script contains expected content
    assert "class Shot" in content
    assert "class Asset" in content
    assert "class Project" in content
    assert "CLASSES = {" in content
    assert "Base = declarative_base()" in content


@pytest.mark.skipif(
    not all([os.getenv("SG_URL"), os.getenv("SG_SCRIPT"), os.getenv("SG_API_KEY")]),
    reason="Shotgrid credentials not available",
)
def test_create_script_from_live_connection():
    """Test creating a Python script from live Shotgrid connection.

    This test requires SG_URL, SG_SCRIPT, and SG_API_KEY environment variables.
    """
    sg_orm = SGORM(
        sg_schema_type=SchemaType.SG_SCRIPT,
        sg_schema_source={
            "url": os.getenv("SG_URL"),
            "script": os.getenv("SG_SCRIPT"),
            "api_key": os.getenv("SG_API_KEY"),
        },
        echo=False,
    )

    # Create script in temp location
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        script_path = f.name

    try:
        sg_orm.create_script(script_path)

        # Verify script was created
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()

        # Verify basic structure
        assert "Base = declarative_base()" in content
        assert "CLASSES = {" in content
    finally:
        # Cleanup
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_script_autoincrement_disabled(sg_orm, temp_dir):
    """Test that generated script has autoincrement disabled for all PKs."""
    script_path = temp_dir / "sgmodel_test.py"
    sg_orm.create_script(str(script_path))

    content = script_path.read_text()

    # Verify that id columns have autoincrement=False
    # The generated script should contain this for primary keys
    assert "autoincrement=False" in content
