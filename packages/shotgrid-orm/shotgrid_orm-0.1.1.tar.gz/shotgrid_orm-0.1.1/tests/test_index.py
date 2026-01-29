"""Tests for SGORM indexing and class access."""


def test_get_class_by_index(sg_orm):
    """Test accessing entity classes using index notation."""
    shot_class = sg_orm["Shot"]
    assert shot_class is not None
    assert hasattr(shot_class, "__tablename__")
    assert shot_class.__tablename__ == "Shot"


def test_get_class_by_get_method(sg_orm):
    """Test accessing entity classes using get method."""
    shot_class = sg_orm.get("Shot")
    assert shot_class is not None
    assert hasattr(shot_class, "__tablename__")
    assert shot_class.__tablename__ == "Shot"


def test_get_nonexistent_class(sg_orm):
    """Test accessing a class that doesn't exist."""
    # Using get() should return None for missing classes
    nonexistent_class = sg_orm.get("NonExistentEntity")
    assert nonexistent_class is None


def test_get_multiple_classes(sg_orm):
    """Test accessing multiple entity classes."""
    Project = sg_orm["Project"]
    Shot = sg_orm["Shot"]
    Asset = sg_orm["Asset"]

    assert Project is not None
    assert Shot is not None
    assert Asset is not None

    assert Project.__tablename__ == "Project"
    assert Shot.__tablename__ == "Shot"
    assert Asset.__tablename__ == "Asset"
