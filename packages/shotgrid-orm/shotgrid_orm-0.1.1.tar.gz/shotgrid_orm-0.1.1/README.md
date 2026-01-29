# Shotgrid ORM Generator

![PyPI](https://img.shields.io/pypi/v/shotgrid_orm)
![Python Version](https://img.shields.io/pypi/pyversions/shotgrid_orm)
![License](https://img.shields.io/github/license/johnetran/shotgrid_orm)
[![Tests](https://github.com/johnetran/shotgrid_orm/actions/workflows/test.yml/badge.svg)](https://github.com/johnetran/shotgrid_orm/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/johnetran/shotgrid_orm/branch/main/graph/badge.svg)](https://codecov.io/gh/johnetran/shotgrid_orm)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

### For Autodesk Flow Production Tracking system (formerly Shotgun/Shotgrid - SG)

This tool generates a SQLAlchemy ORM for a Shotgrid schema for the purposes of reporting, BI, data warehousing, and analytics. It does not generate foreign key constraints and primary keys are not auto-increment. This allows maximum freedom to transfer data from Shotgrid into a target database, retaining its native primary keys (IDs).

## Overview
![Shotgrid ORM](doc/ShotgridORM.png)

## Installation

Install from PyPI:

```bash
pip install shotgrid_orm
```

Or install from source:

```bash
git clone https://github.com/johnetran/shotgrid_orm.git
cd shotgrid_orm
pip install -e .
```

## Requirements

- Python 3.8 or higher
- SQLAlchemy 2.0.45+
- shotgun-api3 3.9.2+
- sqlacodegen-v2 0.1.4+
- alembic 1.16.5+

## Features

- **Multiple Schema Sources**: Load schemas from JSON files, JSON text, or live Shotgrid connections
- **Dynamic ORM Generation**: Creates SQLAlchemy 2.0 declarative models with proper type hints
- **Standalone Script Export**: Generate self-contained Python files with your ORM models
- **Preserve Shotgrid IDs**: Non-auto-increment primary keys maintain original Shotgrid identifiers
- **Polymorphic Relationships**: Handles entity and multi-entity fields with automatic _id and _type columns
- **Alembic Integration**: Built-in support for database migrations
- **Flexible Design**: No forced foreign key constraints for maximum data transfer flexibility

## Quick Start

### Basic Usage

```python
from shotgrid_orm import SGORM, SchemaType

# Load schema from JSON file
sg_orm = SGORM(
    sg_schema_type=SchemaType.JSON_FILE,
    sg_schema_source="schema.json",
    echo=False
)

# Access entity classes
Shot = sg_orm["Shot"]
Asset = sg_orm["Asset"]

# Generate standalone Python script
sg_orm.create_script("sgmodel.py")
```

### Complete Example: Data Warehousing

```python
import os
from shotgrid_orm import SGORM, SchemaType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Connect to live Shotgrid and generate ORM
sg_orm = SGORM(
    sg_schema_type=SchemaType.SG_SCRIPT,
    sg_schema_source={
        "url": os.getenv("SG_URL"),
        "script": os.getenv("SG_SCRIPT"),
        "api_key": os.getenv("SG_API_KEY")
    }
)

# Create PostgreSQL database for analytics
engine = create_engine("postgresql://user:pass@localhost/shotgrid_analytics")
sg_orm.Base.metadata.create_all(engine)

# Now use standard Shotgrid API to fetch data and insert into database
# This preserves all Shotgrid IDs for future syncing
```

## Detailed Usage

### Schema Loading Options

```python
from shotgrid_orm import SGORM, SchemaType

# Option 1: Load from JSON file
sg_orm = SGORM(
    sg_schema_type=SchemaType.JSON_FILE,
    sg_schema_source="schema.json"
)

# Option 2: Load from JSON string
json_text = '{"Project": {...}, "Shot": {...}}'
sg_orm = SGORM(
    sg_schema_type=SchemaType.JSON_TEXT,
    sg_schema_source=json_text
)

# Option 3: Connect with script credentials
sg_orm = SGORM(
    sg_schema_type=SchemaType.SG_SCRIPT,
    sg_schema_source={
        "url": "https://mystudio.shotgunstudio.com",
        "script": "my_script",
        "api_key": "abc123..."
    }
)

# Option 4: Use existing Shotgun connection
import shotgun_api3
sg = shotgun_api3.Shotgun(url, script, key)
sg_orm = SGORM(
    sg_schema_type=SchemaType.SG_CONNECTION,
    sg_schema_source=sg
)

```

### Creating and Managing Databases

```python
from sqlalchemy import create_engine

# SQLite (for local development/testing)
engine = create_engine("sqlite:///shotgrid.db")

# PostgreSQL (recommended for production)
engine = create_engine("postgresql://user:pass@localhost:5432/shotgrid")

# MySQL
engine = create_engine("mysql+pymysql://user:pass@localhost/shotgrid")

# Create all tables
sg_orm.Base.metadata.create_all(engine)

# Drop all tables (use with caution!)
sg_orm.Base.metadata.drop_all(engine)
```

### Working with Data

```python
from sqlalchemy.orm import Session
from sqlalchemy import select

# Using dynamically generated classes
Shot = sg_orm["Shot"]
Asset = sg_orm["Asset"]

session = Session(engine)

# Create a record (preserving Shotgrid ID)
shot = Shot()
shot.id = 1234  # Use actual Shotgrid ID
shot.code = "010"
shot.description = "Opening shot"
session.add(shot)
session.commit()

# Query records
shot = session.execute(
    select(Shot).where(Shot.code == "010")
).scalar_one()

# Update records
shot.description = "Updated description"
session.commit()

# Delete records
session.delete(shot)
session.commit()

session.close()
```

### Using Generated Scripts

After calling `create_script("sgmodel.py")`, you can use the generated module independently:

```python
import sgmodel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///mydb.db")
sgmodel.Base.metadata.create_all(engine)

session = Session(engine)

# Access classes directly
asset = sgmodel.Asset(id=1, code="HERO_CHAR")
session.add(asset)
session.commit()

# Or access dynamically via CLASSES dict
shot_class = sgmodel.CLASSES["Shot"]
shot = shot_class(id=100, code="010")
session.add(shot)
session.commit()
```

### Handling Entity Relationships

Entity fields in Shotgrid become `{field}_id` and `{field}_type` columns:

```python
Shot = sg_orm["Shot"]

shot = Shot()
shot.id = 100
shot.code = "010"

# Single entity field (e.g., project)
shot.project_id = 1
shot.project_type = "Project"

# Another entity field (e.g., sequence)
shot.sg_sequence_id = 10
shot.sg_sequence_type = "Sequence"

session.add(shot)
session.commit()
```

## Advanced Usage

### Ignoring Entities or Fields

```python
sg_orm = SGORM(
    sg_schema_type=SchemaType.JSON_FILE,
    sg_schema_source="schema.json",
    ignored_tables=["AppWelcome", "Banner"],  # Skip these entities
    ignored_fields=["image_source_entity"]     # Skip these fields globally
)
```

### Using with Alembic Migrations

```bash
# Initialize Alembic
alembic init alembic

# Generate migration after schema changes
alembic revision --autogenerate -m "Add new custom fields"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Bulk Data Transfer from Shotgrid

```python
import shotgun_api3
from shotgrid_orm import SGORM, SchemaType
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Connect to Shotgrid
sg = shotgun_api3.Shotgun(url, script, key)

# Generate ORM from live connection
sg_orm = SGORM(sg_schema_type=SchemaType.SG_CONNECTION, sg_schema_source=sg)

# Setup target database
engine = create_engine("postgresql://user:pass@localhost/warehouse")
sg_orm.Base.metadata.create_all(engine)
session = Session(engine)

# Fetch all shots from Shotgrid
Shot = sg_orm["Shot"]
shots_data = sg.find("Shot", [], ["id", "code", "description", "project"])

# Insert into warehouse database
for shot_data in shots_data:
    shot = Shot()
    shot.id = shot_data["id"]
    shot.code = shot_data["code"]
    shot.description = shot_data["description"]

    # Handle entity relationships
    if shot_data.get("project"):
        shot.project_id = shot_data["project"]["id"]
        shot.project_type = shot_data["project"]["type"]

    session.add(shot)

session.commit()
session.close()
```

## Common Pitfalls & Solutions

### 1. Primary Key Conflicts

**Problem**: Attempting to use auto-increment IDs when Shotgrid uses specific IDs.

```python
# ❌ Wrong - SQLAlchemy tries to auto-increment
shot = Shot()
# id is not set, but SQLAlchemy expects it

# ✅ Correct - Always set the ID explicitly
shot = Shot()
shot.id = 1234  # Use the actual Shotgrid ID
```

**Solution**: Always explicitly set the `id` field to match Shotgrid's ID. This tool intentionally disables auto-increment to preserve Shotgrid IDs.

### 2. Entity Field Confusion

**Problem**: Trying to set entity relationships as objects instead of ID/type pairs.

```python
# ❌ Wrong - Shotgrid entity fields aren't relationships
shot.project = project_object

# ✅ Correct - Set _id and _type separately
shot.project_id = 1
shot.project_type = "Project"
```

**Solution**: Entity fields become two columns: `{field}_id` (integer) and `{field}_type` (string).

### 3. Metadata Field Name Clash

**Problem**: Shotgrid's `metadata` field conflicts with SQLAlchemy's metadata.

**Solution**: This is automatically handled - the field is renamed to `_metadata` in the ORM.

```python
# Access Shotgrid's metadata field
shot._metadata = {"custom": "data"}
```

### 4. Schema Not Found

**Problem**: `FileNotFoundError` when loading schema from JSON.

```python
# ❌ Wrong - Relative path might not work
sg_orm = SGORM(SchemaType.JSON_FILE, "schema.json")

# ✅ Correct - Use absolute path or ensure working directory
import os
schema_path = os.path.join(os.getcwd(), "schema.json")
sg_orm = SGORM(SchemaType.JSON_FILE, schema_path)
```

### 5. Missing Shotgun API Package

**Problem**: `ImportError` when trying to connect to live Shotgrid.

**Solution**: Install the Shotgrid API:
```bash
pip install shotgun-api3
```

### 6. NULL vs Empty String

**Problem**: Shotgrid treats empty strings differently than NULL.

```python
# Be explicit about NULL vs empty string
shot.description = None  # NULL in database
shot.description = ""     # Empty string
```

## FAQ

### How do I get my Shotgrid schema as JSON?

Use the Shotgrid API to export your schema:

```python
import shotgun_api3
import json

sg = shotgun_api3.Shotgun(url, script, key)
schema = {}

entities = sg.schema_entity_read()
for entity_name in entities:
    entity = entities[entity_name]
    fields = sg.schema_field_read(entity_name)
    entity["fields"] = fields
    schema[entity_name] = entity

with open("schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

### Can I add foreign key constraints manually?

Yes! While they're not generated automatically, you can add them:

```python
from sqlalchemy import ForeignKey

# After generating the ORM, modify the class
Shot = sg_orm["Shot"]
# Add ForeignKey to project_id if you want referential integrity
# Note: This requires manual modification of generated code
```

### Does this work with custom Shotgrid fields?

Yes! Custom fields are automatically included in the generated ORM. The tool reads the complete schema including all custom fields.

### Can I use this for real-time syncing?

This tool is designed for one-way data transfer (Shotgrid → Database) for analytics/reporting. For real-time bidirectional sync, consider using Shotgrid's event framework or webhooks.

### What database engines are supported?

Any database supported by SQLAlchemy 2.0:
- PostgreSQL (recommended for production)
- MySQL/MariaDB
- SQLite (great for development)
- Oracle
- Microsoft SQL Server

### How do I handle schema changes?

Use Alembic for migrations:

```bash
# Generate migration after Shotgrid schema changes
alembic revision --autogenerate -m "Shotgrid schema update"
alembic upgrade head
```

Or regenerate the ORM and recreate tables (loses data):

```python
sg_orm.Base.metadata.drop_all(engine)
sg_orm.Base.metadata.create_all(engine)
```

### Can I filter which entities are included?

Yes, use the `ignored_tables` parameter:

```python
sg_orm = SGORM(
    sg_schema_type=SchemaType.JSON_FILE,
    sg_schema_source="schema.json",
    ignored_tables=["Banner", "AppWelcome", "PageSetting"]
)
```

### How do I access classes dynamically?

Use dictionary notation or the `CLASSES` dict:

```python
# From SGORM instance
Shot = sg_orm["Shot"]
Shot = sg_orm.classes["Shot"]

# From generated script
import sgmodel
Shot = sgmodel.CLASSES["Shot"]
```

### Is this an official Autodesk tool?

No, this is a community-developed tool. It uses the official Shotgrid Python API but is not affiliated with or supported by Autodesk.

### What about multi-entity fields?

Multi-entity fields (one-to-many) create reverse foreign key columns on related tables in the format `{SourceTable}_{field}_id`.

## Environment Variables

For live Shotgrid connections, set these environment variables:

```bash
export SG_URL="https://your-studio.shotgunstudio.com"
export SG_SCRIPT="your_script_name"
export SG_API_KEY="your_api_key_here"
```

## Known Limitations

- **Foreign Keys**: ForeignKey constraints are intentionally not generated to allow flexibility in data transfer. You can add them manually if needed.
- **Entity Relationships**: Entity and multi-entity types are stored as integer IDs and strings rather than full SQLAlchemy relationship() objects.
- **Complex Types**: Serializable fields (dicts/JSON) and URL fields are stored as strings. Consider JSON serialization for complex use cases.
- **Read-Only Fields**: Some Shotgrid field types (like image) are read-only and stored as strings.

## Use Cases

- **Data Warehousing**: Extract Shotgrid data into analytical databases (PostgreSQL, MySQL, etc.)
- **Reporting & BI**: Build custom reports using standard SQL tools
- **Data Migration**: Transfer Shotgrid data between environments while preserving IDs
- **Backup & Archival**: Create local copies of Shotgrid data with full schema preservation
- **Custom Integrations**: Build applications that work with Shotgrid data offline

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [SQLAlchemy](https://www.sqlalchemy.org/)
- Schema code generation powered by [sqlacodegen-v2](https://github.com/ksindi/sqlacodegen)
- Shotgrid API integration via [shotgun-api3](https://github.com/shotgunsoftware/python-api)

## Links

- **PyPI**: https://pypi.org/project/shotgrid_orm/
- **GitHub**: https://github.com/johnetran/shotgrid_orm
- **Issues**: https://github.com/johnetran/shotgrid_orm/issues
- **Autodesk Flow Production Tracking**: https://www.autodesk.com/products/flow-production-tracking/
