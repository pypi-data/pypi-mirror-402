from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SGType:
    id: Mapped[int]
    type: Mapped[str]


class SGUrl:
    content_type: Mapped[str]
    link_type: Mapped[str]
    name: Mapped[str]
    url: Mapped[str]
    local_path: Mapped[str]
    local_path_linux: Mapped[str]
    local_path_mac: Mapped[str]
    local_path_windows: Mapped[str]
    local_storage: Mapped[dict]

    def __repr__(self) -> str:
        return f"SGUrl(content_type={self.content_type!r}, link_type={self.link_type!r}, name={self.name!r}, url={self.url!r}"


sg_types = {
    "addressing": {"hint": Mapped[str], "type": mapped_column(String)},
    "checkbox": {"hint": Mapped[bool], "type": mapped_column(Boolean)},
    "color": {"hint": Mapped[str], "type": mapped_column(String)},
    "currency": {"hint": Mapped[float], "type": mapped_column(Float)},
    "date": {"hint": Mapped[str], "type": mapped_column(String)},
    "date_time": {"hint": Mapped[datetime], "type": mapped_column(DateTime)},
    # NOTE: Entity types are stored as integer IDs. Relationship mappings are handled
    # in classes.py by creating _id and _type fields for polymorphic associations.
    # Full SQLAlchemy relationship() support could be added in future versions.
    "entity": {"hint": Mapped[int], "type": mapped_column(Integer)},
    "float": {"hint": Mapped[float], "type": mapped_column(Float)},
    "footage": {"hint": Mapped[str], "type": mapped_column(String)},
    "image": {"hint": Mapped[str], "type": mapped_column(String)},  # readonly
    "list": {"hint": Mapped[str], "type": mapped_column(String)},
    # NOTE: Multi-entity fields stored as strings. Consider JSON serialization
    # for complex use cases. Full list relationship support could be added in future.
    "multi_entity": {"hint": Mapped[str], "type": mapped_column(String)},
    "number": {"hint": Mapped[int], "type": mapped_column(Integer)},
    "password": {"hint": Mapped[str], "type": mapped_column(String)},
    "percent": {"hint": Mapped[int], "type": mapped_column(Integer)},
    # NOTE: Serializable types (dicts/JSON) stored as strings. Consider using
    # SQLAlchemy JSON type for databases that support it (PostgreSQL, MySQL, SQLite 3.9+)
    "serializable": {"hint": Mapped[str], "type": mapped_column(String)},
    "status_list": {"hint": Mapped[str], "type": mapped_column(String)},
    "system_task_type": {"hint": Mapped[str], "type": mapped_column(String)},
    "tag_list": {"hint": Mapped[str], "type": mapped_column(String)},
    "text": {"hint": Mapped[str], "type": mapped_column(String)},
    "timecode": {"hint": Mapped[int], "type": mapped_column(Integer)},
    # NOTE: URL fields stored as strings. Complex URL objects with metadata
    # could be serialized as JSON if needed.
    "url": {"hint": Mapped[str], "type": mapped_column(String)},
}


sg_types_optional = {
    "addressing": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "checkbox": {"hint": Mapped[Optional[bool]], "type": mapped_column(Boolean)},
    "color": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "currency": {"hint": Mapped[Optional[float]], "type": mapped_column(Float)},
    "date": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "date_time": {"hint": Mapped[Optional[datetime]], "type": mapped_column(DateTime)},
    # NOTE: Entity types are stored as integer IDs. Relationship mappings are handled
    # in classes.py by creating _id and _type fields for polymorphic associations.
    "entity": {"hint": Mapped[Optional[int]], "type": mapped_column(Integer)},
    "float": {"hint": Mapped[Optional[float]], "type": mapped_column(Float)},
    "footage": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "image": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},  # readonly
    "list": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    # NOTE: Multi-entity fields stored as strings. Consider JSON serialization for complex use cases.
    "multi_entity": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "number": {"hint": Mapped[Optional[int]], "type": mapped_column(Integer)},
    "password": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "percent": {"hint": Mapped[Optional[int]], "type": mapped_column(Integer)},
    # NOTE: Serializable types (dicts/JSON) stored as strings.
    "serializable": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "status_list": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "system_task_type": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "tag_list": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "text": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
    "timecode": {"hint": Mapped[Optional[int]], "type": mapped_column(Integer)},
    # NOTE: URL fields stored as strings.
    "url": {"hint": Mapped[Optional[str]], "type": mapped_column(String)},
}
