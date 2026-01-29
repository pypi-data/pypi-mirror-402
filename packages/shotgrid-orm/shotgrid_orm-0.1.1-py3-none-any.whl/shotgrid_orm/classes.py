import copy
import functools
import json
import os
import traceback
from enum import Enum
from typing import List, Optional

from sqlacodegen_v2 import generators
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

sgapi = None
try:
    import shotgun_api3

    sgapi = shotgun_api3
except ImportError:
    pass

from . import sgtypes


class Base(DeclarativeBase):
    pass


class SchemaType(Enum):
    JSON_FILE = 1
    JSON_TEXT = 2
    SG_USER = 3
    SG_SCRIPT = 4
    SG_CONNECTION = 5


TABLE_IGNORE_LIST: List[str] = []  # ["AppWelcome", "Banner"]
FIELD_IGNORE_LIST: List[str] = []  # ["image_source_entity"]

SQLITE_MEMORY_SQA_URL = "sqlite+pysqlite:///:memory:"

DEFAULT_SCHEMA_TYPE = SchemaType.JSON_FILE
DEFAULT_SCHEMA_FILE = "schema.json"
DEFAULT_SQA_URL = "sqlite+pysqlite:///:memory:"
DEFAULT_OUT_SCRIPT = "sgmodel.py"

DEFAULT_GENERATOR_CLASS = generators.DeclarativeGenerator


def has_sg():
    def decorator_has_sg(func):
        @functools.wraps(func)
        def wrapper_decorator_has_sg(*args, **kwargs):
            if sgapi:
                return func(*args, **kwargs)
            else:
                pass

        return wrapper_decorator_has_sg

    return decorator_has_sg


class SGORM:

    def __init__(
        self,
        sg_schema_type=DEFAULT_SCHEMA_TYPE,
        sg_schema_source=DEFAULT_SCHEMA_FILE,
        ignored_tables=TABLE_IGNORE_LIST,
        ignored_fields=FIELD_IGNORE_LIST,
        echo=True,
    ):

        if not sg_schema_type:
            sg_schema_type = DEFAULT_SCHEMA_TYPE
        if not sg_schema_source:
            sg_schema_source = DEFAULT_SCHEMA_FILE
        self.sg_schema_type = sg_schema_type
        self.sg_schema_source = sg_schema_source

        self.echo = echo

        if not ignored_tables:
            ignored_tables = TABLE_IGNORE_LIST
        if not ignored_fields:
            ignored_fields = FIELD_IGNORE_LIST

        self.ignored_tables = ignored_tables
        self.ignored_fields = ignored_fields

        # read the SG schema0
        self.sg_schema, self.sg = self.read_sg_schema()

        # create classes
        self.classes, self.tables = self.create_sg_classes()

        # create in-memory engine so that classes can be reflected
        self.engine = create_engine(SQLITE_MEMORY_SQA_URL, echo=self.echo)

        # if (drop_all):
        #     self.info("dropping all tables")
        #     Base.metadata.drop_all(bind=self.engine)

        # create the ORM
        self.session = self.create_sg_orm()

        self.Base = Base

        # self.create_script(out_script)

    def __getitem__(self, class_name):
        return self.classes.get(str(class_name))

    def get(self, class_name, default=None):
        return self.classes.get(str(class_name), default)

    def info(self, message, color=None, echo=None):
        if not echo:
            echo = self.echo

        if echo:
            print(message)

    def create_sg_orm(self):
        Base.metadata.create_all(self.engine)
        session = Session(self.engine)
        return session

    def read_sg_schema(self):
        sg = None
        sg_schema = {}
        if self.sg_schema_type in [SchemaType.JSON_FILE, SchemaType.JSON_TEXT]:
            sg_schema = self.read_schema_from_json()

        elif self.sg_schema_type in [SchemaType.SG_USER, SchemaType.SG_SCRIPT, SchemaType.SG_CONNECTION]:
            sg = self.sg_connect()
            sg_schema = self.read_schema_from_sg(sg)

        return sg_schema, sg

    def read_schema_from_json(self):
        sg_schema = {}
        if isinstance(self.sg_schema_source, str):
            if self.sg_schema_type == SchemaType.JSON_FILE:
                if os.path.isfile(self.sg_schema_source):
                    with open(self.sg_schema_source) as f:
                        sg_schema = json.load(f)
            elif self.sg_schema_type == SchemaType.JSON_TEXT:
                sg_schema = json.loads(self.sg_schema_source)

        return sg_schema

    @has_sg()
    def sg_connect(self):
        sg = None
        if isinstance(self.sg_schema_source, dict):
            url = self.sg_schema_source.get("url") or self.sg_schema_source.get("base_url")
            if url:
                if self.sg_schema_type == SchemaType.SG_USER:
                    login = self.sg_schema_source.get("login")
                    password = self.sg_schema_source.get("password")
                    auth_token = self.sg_schema_source.get("auth_token")
                    if login and password:
                        sg = sgapi.Shotgun(url, login=login, password=password, auth_token=auth_token)

                elif self.sg_schema_type == SchemaType.SG_SCRIPT:
                    script_name = self.sg_schema_source.get("script_name") or self.sg_schema_source.get("script")
                    api_key = self.sg_schema_source.get("api_key")
                    sudo_as_login = self.sg_schema_source.get("sudo_as_login")
                    if script_name and api_key:
                        sg = sgapi.Shotgun(url, script_name=script_name, api_key=api_key, sudo_as_login=sudo_as_login)

                elif self.sg_schema_type == SchemaType.SG_CONNECTION:
                    self.sg = self.sg_schema_source
        else:
            print("invalid schema source")

        return sg

    def read_schema_from_sg(self, sg):
        sg_schema = {}
        if sg:
            entities = sg.schema_entity_read()
            for entity_name in sorted(entities):
                entity = entities.get(entity_name, {})
                fields = sg.schema_field_read(entity_name)
                entity["fields"] = fields
                sg_schema[entity_name] = entity
        else:
            print("no sg")

        return sg_schema

    def create_sg_classes(self):

        classes = {}
        tables = {}
        for table in self.sg_schema:
            self.info(f"TABLE {table}")

            if table in self.ignored_tables:
                self.info(f"ignoring table: {table}")
                continue

            t_def = self.sg_schema.get(table)
            if not t_def:
                self.info(f"NO definition for table: {table}")
                continue

            if table not in tables:
                tables[table] = {}

            t_namespace = tables[table].get("namespace")
            if not isinstance(t_namespace, dict):
                t_namespace = {"__tablename__": table}
            t_annotations = tables[table].get("annotations")
            if not isinstance(t_annotations, dict):
                t_annotations = {}

            tables[table]["definition"] = t_def

            fields = t_def.get("fields")
            for field in fields:

                if field in self.ignored_fields:
                    self.info(f"ignoring field: {field}")
                    continue

                field_code = field
                if field == "metadata":
                    field_code = f"_{field}"

                field_def = fields.get(field)
                field_type = field_def.get("data_type")
                field_type_value = field_type.get("value")
                field_properties = field_def.get("properties")
                field_valid_types = field_properties.get("valid_types")

                self.info(f"==> {field_code} ({field_type_value})")

                if field_code == "id":
                    self.info("* id field")
                    t_annotations[field_code] = Mapped[int]
                    t_namespace[field_code] = mapped_column(primary_key=True, autoincrement=False)

                else:
                    if field_type_value in ["entity", "multi_entity"]:
                        self.info(f"* {field_type_value} field")
                        if field_valid_types and field_valid_types.get("value"):
                            v_tables = field_valid_types.get("value")

                            if field_type_value == "entity":
                                # singe entity
                                if len(v_tables) == 1:

                                    v_table = v_tables[0]
                                    if v_table in self.ignored_tables:
                                        self.info(f"ignoring v_table: {v_table}")
                                        continue

                                    # table points to ONE type of v_table - need foreign key TO v_table
                                    foreign_field_code = f"{v_table}_{field_code}_id"
                                    t_annotations[foreign_field_code] = Mapped[Optional[int]]
                                    # NOTE: ForeignKey constraints are intentionally not generated to allow maximum
                                    # flexibility when transferring data from Shotgrid to target databases.
                                    # Users can add them manually if desired:
                                    # t_namespace[foreign_field_code] = mapped_column(ForeignKey(f"{v_tables}.id"))

                                else:
                                    # table points to MANY types of v_table - need an id and type TO v_table
                                    # "number": {"hint": Mapped[int], "type": mapped_column(Integer)},
                                    self.info(f"assigning annotation for {field_code}_id")
                                    t_annotations[f"{field_code}_id"] = Mapped[Optional[int]]
                                    # self.info(f"assigning namespace for {field_code}_id")
                                    # t_namespace[f"{field_code}_id"] = mapped_column(Integer)
                                    self.info(f"assigning annotation for {field_code}_type")
                                    t_annotations[f"{field_code}_type"] = Mapped[Optional[str]]
                                    self.info(f"assigning namespace for {field_code}_type")
                                    # t_namespace[f"{field_code}_type"] = mapped_column(String)
                                    # self.info(f"done assigning field {field_code} to id and type")

                            else:
                                # multi entity
                                if len(v_tables) == 1:

                                    v_table = v_tables[0]
                                    if v_table in self.ignored_tables:
                                        self.info(f"ignoring v_table: {v_table}")
                                        continue

                                    if v_table not in tables:
                                        tables[v_table] = {}

                                    v_namespace = tables[v_table].get("namespace")
                                    if not isinstance(v_namespace, dict):
                                        v_namespace = {"__tablename__": v_table}

                                    v_annotations = tables[v_table].get("annotations")
                                    if not isinstance(v_annotations, dict):
                                        v_annotations = {}

                                    # table points to ONE type of v_table - need foreign key FROM v_table
                                    foreign_field_code = f"{table}_{field_code}_id"
                                    if not v_annotations.get(foreign_field_code) and not t_namespace.get(
                                        foreign_field_code
                                    ):
                                        # add to
                                        v_annotations[foreign_field_code] = Mapped[Optional[int]]
                                        # NOTE: ForeignKey constraints are intentionally not generated to allow maximum
                                        # flexibility when transferring data from Shotgrid to target databases.
                                        # Users can add them manually if desired:
                                        # v_namespace[foreign_field_code] = mapped_column(ForeignKey(f"{table}.id"))

                                    tables[v_table]["namespace"] = v_namespace
                                    tables[v_table]["annotations"] = v_annotations

                                # unsupported case? (because of multipe v_tables that we would need to point back to table)
                                # else:
                                #     # table points to MANY types of v_table - need an id and type FROM v_table
                                #     # "number": {"hint": Mapped[int], "type": mapped_column(Integer)},
                                #     self.info(f"assigning annotation for {field_code}_id")
                                #     v_annotations[f"{field_code}_id"] = Mapped[int]
                                #     self.info(f"assigning namespace for {field_code}_id")
                                #     v_namespace[f"{field_code}_id"] = mapped_column(Integer)
                                #     self.info(f"assigning annotation for {field_code}_type")
                                #     v_annotations[f"{field_code}_type"] = Mapped[str]
                                #     self.info(f"assigning namespace for {field_code}_type")
                                #     v_namespace[f"{field_code}_type"] = mapped_column(String)
                                #     self.info(f"done assigning field {field_code} to id and type")

                    else:
                        self.info(f"* {field_type_value} field")
                        if field_type_value in list(sgtypes.sg_types.keys()):
                            self.info(f"assigning annotation for {field_code}")
                            t_annotations[field_code] = copy.deepcopy(
                                sgtypes.sg_types_optional.get(field_type_value).get("hint")
                            )
                            # self.info(f"assigning namespace for {field_code}")
                            # t_namespace[field_code] = copy.deepcopy(sgtypes.sg_types.get(field_type_value).get("type"))
                            self.info("done assigning normal type")
                        else:
                            self.info(f"{field_type_value} unsupported")

            tables[table]["annotations"] = t_annotations
            tables[table]["namespace"] = t_namespace

        for node in tables:
            self.info(f"setting annotations in namespace for {node}")

            t_namespace = tables[node]["namespace"]
            t_annotations = tables[node]["annotations"]
            t_namespace["__annotations__"] = t_annotations

            try:
                self.info(f"creating class {node}")
                TClass = type(node, (Base,), t_namespace)

                self.info(f"adding class {node}")
                tables[node]["class"] = TClass
                classes[node] = TClass

            except Exception as error:
                self.info(f"Error creating type {node}: {error}")
                self.info(traceback.format_exc())

        return classes, tables

    def create_script(self, out_script=DEFAULT_OUT_SCRIPT, generator_class=DEFAULT_GENERATOR_CLASS):

        if not out_script:
            out_script = DEFAULT_OUT_SCRIPT
        if not generator_class:
            generator_class = DEFAULT_GENERATOR_CLASS

        gen = generator_class(Base.metadata, self.engine, [])
        code = gen.generate()
        with open(out_script, "w") as f:
            # ensures no auto-increment since we are using SG's id's
            code = code.replace(
                "id = mapped_column(Integer, primary_key=True)",
                "id = mapped_column(Integer, primary_key=True, autoincrement=False)",
            )

            code += """

########################################
# generated classes dict for easy access
########################################
import inspect
CLASSES = {n: c for n, c in globals().copy().items() if inspect.isclass(c) }

"""
            f.write(code)
