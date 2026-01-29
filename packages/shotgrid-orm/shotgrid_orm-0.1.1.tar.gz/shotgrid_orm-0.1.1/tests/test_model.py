"""Tests for generated model file functionality."""

import importlib.util
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_generated_model_import(sg_orm, temp_dir, test_db_path):
    """Test that generated model file can be imported and used."""
    # Generate the model script
    model_path = temp_dir / "sgmodel.py"
    sg_orm.create_script(str(model_path))

    # Import the generated module
    spec = importlib.util.spec_from_file_location("sgmodel", model_path)
    sgmodel = importlib.util.module_from_spec(spec)
    sys.modules["sgmodel"] = sgmodel
    spec.loader.exec_module(sgmodel)

    # Create database and tables using generated model
    engine = create_engine(f"sqlite+pysqlite:///{test_db_path}", echo=False)
    sgmodel.Base.metadata.create_all(engine)
    session = Session(engine)

    # Test creating an Asset using generated model
    asset = sgmodel.Asset()
    asset.id = 1
    asset.code = "TestAsset"

    session.add(asset)
    session.commit()

    # Test reading the asset
    retrieved_asset = session.execute(select(sgmodel.Asset).where(sgmodel.Asset.id == 1)).scalar_one()

    assert retrieved_asset.id == 1
    assert retrieved_asset.code == "TestAsset"

    # Test updating the asset
    retrieved_asset.code = "UpdatedAssetName"
    session.commit()

    # Verify update
    changed_asset = session.execute(select(sgmodel.Asset).where(sgmodel.Asset.id == 1)).scalar_one()
    assert changed_asset.code == "UpdatedAssetName"

    session.close()

    # Cleanup
    del sys.modules["sgmodel"]


def test_generated_model_classes_dict(sg_orm, temp_dir):
    """Test that generated model has CLASSES dict for dynamic access."""
    # Generate the model script
    model_path = temp_dir / "sgmodel.py"
    sg_orm.create_script(str(model_path))

    # Import the generated module
    spec = importlib.util.spec_from_file_location("sgmodel", model_path)
    sgmodel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sgmodel)

    # Verify CLASSES dict exists
    assert hasattr(sgmodel, "CLASSES")
    assert isinstance(sgmodel.CLASSES, dict)

    # Verify we can get classes from the dict
    shot_class = sgmodel.CLASSES.get("Shot")
    assert shot_class is not None
    assert hasattr(shot_class, "__tablename__")
    assert shot_class.__tablename__ == "Shot"


def test_dynamic_class_instantiation(sg_orm, temp_dir, test_db_path):
    """Test creating instances using dynamically accessed classes."""
    # Generate the model script
    model_path = temp_dir / "sgmodel.py"
    sg_orm.create_script(str(model_path))

    # Import the generated module
    spec = importlib.util.spec_from_file_location("sgmodel", model_path)
    sgmodel = importlib.util.module_from_spec(spec)
    sys.modules["sgmodel"] = sgmodel
    spec.loader.exec_module(sgmodel)

    # Create database
    engine = create_engine(f"sqlite+pysqlite:///{test_db_path}", echo=False)
    sgmodel.Base.metadata.create_all(engine)
    session = Session(engine)

    # Get Shot class dynamically
    shot_class = sgmodel.CLASSES.get("Shot")

    # Create shot with kwargs (important for dynamic Shotgrid data)
    args = {"id": 1, "code": "TestShot"}
    new_shot = shot_class(**args)

    session.add(new_shot)
    session.commit()

    # Verify shot was created
    retrieved_shot = session.execute(select(shot_class).where(shot_class.id == 1)).scalar_one()
    assert retrieved_shot.id == 1
    assert retrieved_shot.code == "TestShot"

    session.close()

    # Cleanup
    del sys.modules["sgmodel"]
