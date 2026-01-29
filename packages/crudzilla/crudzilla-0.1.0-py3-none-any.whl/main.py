"""
crudzilla - Generate Pydantic models and FastCRUD routers from database schema.

Uses supabase-pydantic (sb-pydantic) to introspect the database and generate
type-safe Pydantic models, then generates FastCRUD routers using the fastcrud library.

Usage:
    crudzilla
    crudzilla --output-dir src/models/generated
    crudzilla --generate-routers
    crudzilla --env-file /path/to/.env
    crudzilla --dry-run --verbose
    crudzilla --async-mode
    crudzilla --config pyproject.toml
    crudzilla --generate-erd
"""

__version__ = "0.1.0"

import argparse
import ast
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse, urlunparse

try:
    import tomllib
except ImportError:
    import tomli as tomllib

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by", "deleted_at", "deleted_by"]
DEFAULT_SOFT_DELETE_COLUMN = "deleted_at"


@dataclass
class GeneratorConfig:
    """Configuration for the model/router generator."""
    output_dir: str = "generated_models"
    routers_dir: str = "src/app/routers/generated"
    schema: str = "public"
    include_sqlalchemy: bool = False
    generate_routers: bool = False
    use_generated_sqlalchemy: bool = False
    async_mode: bool = False
    soft_delete_column: str | None = None
    audit_fields: list[str] = field(default_factory=lambda: DEFAULT_AUDIT_FIELDS.copy())
    exclude_tables: list[str] = field(default_factory=list)
    generate_erd: bool = False
    erd_output: str = "erd.png"
    generate_relationships: bool = False
    session_dependency: str = "get_session"
    dry_run: bool = False
    backup: bool = False
    verbose: bool = False
    quiet: bool = False
    env_file: Path | None = None
    export_metadata: Path | None = None
    watch: bool = False
    watch_interval: int = 5

    @classmethod
    def from_toml(cls, config_path: Path) -> "GeneratorConfig":
        """Load configuration from a TOML file (pyproject.toml or dedicated config)."""
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        if "tool" in data and "db-generator" in data["tool"]:
            config_data = data["tool"]["db-generator"]
        elif "db-generator" in data:
            config_data = data["db-generator"]
        else:
            config_data = data

        field_mapping = {
            "output-dir": "output_dir",
            "routers-dir": "routers_dir",
            "include-sqlalchemy": "include_sqlalchemy",
            "generate-routers": "generate_routers",
            "use-generated-sqlalchemy": "use_generated_sqlalchemy",
            "async-mode": "async_mode",
            "soft-delete-column": "soft_delete_column",
            "audit-fields": "audit_fields",
            "exclude-tables": "exclude_tables",
            "generate-erd": "generate_erd",
            "erd-output": "erd_output",
            "generate-relationships": "generate_relationships",
            "session-dependency": "session_dependency",
            "dry-run": "dry_run",
            "env-file": "env_file",
            "export-metadata": "export_metadata",
            "watch": "watch",
            "watch-interval": "watch_interval",
        }

        kwargs: dict[str, Any] = {}
        for toml_key, attr_name in field_mapping.items():
            if toml_key in config_data:
                value = config_data[toml_key]
                if attr_name in ("env_file", "export_metadata") and value:
                    value = Path(value)
                kwargs[attr_name] = value

        for key, value in config_data.items():
            attr_name = key.replace("-", "_")
            if attr_name not in kwargs and hasattr(cls, "__dataclass_fields__") and attr_name in cls.__dataclass_fields__:
                if attr_name in ("env_file", "export_metadata") and value:
                    value = Path(value)
                kwargs[attr_name] = value

        return cls(**kwargs)

    def merge_cli_args(self, args: argparse.Namespace) -> "GeneratorConfig":
        """Merge CLI arguments into config, CLI takes precedence."""
        updates: dict[str, Any] = {}

        if args.output_dir != "generated_models":
            updates["output_dir"] = args.output_dir
        if args.routers_dir != "src/app/routers/generated":
            updates["routers_dir"] = args.routers_dir
        if args.schema != "public":
            updates["schema"] = args.schema
        if args.include_sqlalchemy:
            updates["include_sqlalchemy"] = True
        if args.generate_routers:
            updates["generate_routers"] = True
        if args.use_generated_sqlalchemy:
            updates["use_generated_sqlalchemy"] = True
        if args.async_mode:
            updates["async_mode"] = True
        if args.soft_delete_column:
            updates["soft_delete_column"] = args.soft_delete_column
        if args.audit_fields:
            updates["audit_fields"] = args.audit_fields
        if args.exclude_tables:
            updates["exclude_tables"] = args.exclude_tables
        if args.generate_erd:
            updates["generate_erd"] = True
        if args.erd_output:
            updates["erd_output"] = args.erd_output
        if args.generate_relationships:
            updates["generate_relationships"] = True
        if hasattr(args, 'session_dependency') and args.session_dependency != "get_session":
            updates["session_dependency"] = args.session_dependency
        if args.dry_run:
            updates["dry_run"] = True
        if args.backup:
            updates["backup"] = True
        if args.verbose:
            updates["verbose"] = True
        if args.quiet:
            updates["quiet"] = True
        if args.env_file:
            updates["env_file"] = args.env_file
        if args.export_metadata:
            updates["export_metadata"] = args.export_metadata
        if hasattr(args, 'watch') and args.watch:
            updates["watch"] = True
        if hasattr(args, 'watch_interval') and args.watch_interval != 5:
            updates["watch_interval"] = args.watch_interval

        from dataclasses import replace
        return replace(self, **updates)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )


def normalize_database_url(db_url: str) -> str:
    """Ensure database URL has an explicit port and properly encode password."""
    parsed = urlparse(db_url)
    if parsed.port is None and parsed.hostname:
        default_port = 5432
        if parsed.password:
            encoded_password = quote(parsed.password, safe='')
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}:{default_port}"
        else:
            netloc = f"{parsed.hostname}:{default_port}"
        parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)
    return db_url


def load_env_file(env_file: Path) -> str | None:
    """Load DATABASE_URL from an env file."""
    if not env_file.exists():
        return None

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def get_database_url(env_file: Path | None = None) -> str:
    """Get database URL from environment or .env file.

    Search order:
    1. Explicit env_file argument
    2. DATABASE_URL environment variable
    3. .env in current working directory
    4. .env in script's parent directory
    5. .env in script's directory
    """
    if env_file:
        db_url = load_env_file(env_file)
        if db_url:
            logger.debug(f"Loaded DATABASE_URL from {env_file}")
            return normalize_database_url(db_url)
        raise ValueError(f"DATABASE_URL not found in {env_file}")

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.debug("Using DATABASE_URL from environment")
        return normalize_database_url(db_url)

    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env",
    ]

    for path in env_paths:
        db_url = load_env_file(path)
        if db_url:
            logger.debug(f"Loaded DATABASE_URL from {path}")
            return normalize_database_url(db_url)

    raise ValueError(
        "DATABASE_URL not found. Searched:\n"
        f"  - Environment variable DATABASE_URL\n"
        f"  - {env_paths[0]}\n"
        f"  - {env_paths[1]}\n"
        f"  - {env_paths[2]}\n"
        "Use --env-file to specify a custom path."
    )


def to_snake_case(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def validate_python_file(file_path: Path) -> bool:
    """Validate that a generated Python file has correct syntax."""
    try:
        with open(file_path) as f:
            ast.parse(f.read())
        logger.debug(f"Validated syntax: {file_path}")
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False


def get_schema_fingerprint(db_url: str, schema: str = "public") -> str | None:
    """Get a fingerprint of the database schema for change detection.

    Queries PostgreSQL information_schema to get table/column definitions
    and returns a hash that changes when the schema changes.
    """
    import hashlib

    try:
        import psycopg2
    except ImportError:
        logger.warning("psycopg2 not installed, watch mode will use timestamp-based detection")
        return None

    query = """
        SELECT
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name = c.table_name
            AND t.table_schema = c.table_schema
        WHERE t.table_schema = %s
            AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position
    """

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(query, (schema,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        schema_str = json.dumps(rows, sort_keys=True, default=str)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Could not get schema fingerprint: {e}")
        return None


def run_watch_mode(config: "GeneratorConfig", run_func: callable) -> None:
    """Run in watch mode, regenerating when schema changes are detected."""
    import signal

    db_url = get_database_url(config.env_file)
    last_fingerprint = None
    generation_count = 0

    def signal_handler(sig, frame):
        logger.info("\nWatch mode stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Starting watch mode (checking every {config.watch_interval}s)")
    logger.info("Press Ctrl+C to stop\n")

    while True:
        try:
            current_fingerprint = get_schema_fingerprint(db_url, config.schema)

            if current_fingerprint is None:
                current_fingerprint = str(time.time())
                if generation_count == 0:
                    logger.info("Initial generation...")
                    run_func(config)
                    generation_count += 1
                    last_fingerprint = current_fingerprint
            elif current_fingerprint != last_fingerprint:
                if last_fingerprint is None:
                    logger.info("Initial generation...")
                else:
                    logger.info(f"Schema change detected (fingerprint: {current_fingerprint})")
                    logger.info("Regenerating models...")

                run_func(config)
                generation_count += 1
                last_fingerprint = current_fingerprint
                logger.info(f"Generation #{generation_count} complete. Watching for changes...\n")
            else:
                logger.debug(f"No changes (fingerprint: {current_fingerprint})")

            time.sleep(config.watch_interval)

        except KeyboardInterrupt:
            logger.info("\nWatch mode stopped.")
            break
        except Exception as e:
            logger.error(f"Error during watch: {e}")
            time.sleep(config.watch_interval)


def backup_file(file_path: Path) -> Path | None:
    """Create a timestamped backup of a file if it exists."""
    if not file_path.exists():
        return None
    timestamp = int(time.time())
    backup_path = file_path.with_suffix(f".{timestamp}.bak")
    shutil.copy2(file_path, backup_path)
    logger.debug(f"Backed up {file_path} to {backup_path}")
    return backup_path


def should_exclude_table(table_name: str, exclude_patterns: list[str]) -> bool:
    """Check if a table should be excluded based on patterns."""
    for pattern in exclude_patterns:
        if pattern.startswith("*") and table_name.endswith(pattern[1:]):
            return True
        if pattern.endswith("*") and table_name.startswith(pattern[:-1]):
            return True
        if table_name == pattern:
            return True
    return False


def is_audit_field(field_name: str, audit_fields: list[str]) -> bool:
    """Check if a field is an audit field that should be excluded from create/update schemas."""
    return field_name.lower() in [f.lower() for f in audit_fields]


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key relationship."""
    column: str
    references_table: str
    references_column: str
    constraint_name: str | None = None


@dataclass
class TableInfo:
    """Information about a database table including relationships."""
    name: str
    columns: list[str]
    primary_key: str | None
    foreign_keys: list[ForeignKeyInfo]
    has_soft_delete: bool = False
    soft_delete_column: str | None = None


def extract_foreign_keys_from_sqlalchemy(file_path: Path) -> dict[str, list[ForeignKeyInfo]]:
    """Extract foreign key information from SQLAlchemy models file.

    Handles multiple FK definition patterns:
    1. Inline ForeignKey(): `user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))`
    2. ForeignKeyConstraint in __table_args__: `ForeignKeyConstraint(['user_id'], ['user.id'], ...)`
    """
    foreign_keys: dict[str, list[ForeignKeyInfo]] = {}

    with open(file_path) as f:
        content = f.read()

    current_class = None
    in_table_args = False
    table_args_content = ""

    for line in content.split('\n'):
        if line.strip().startswith('class ') and '(Base):' in line:
            if current_class and table_args_content:
                _parse_table_args_fks(current_class, table_args_content, foreign_keys)

            current_class = line.split('class ')[1].split('(')[0].strip()
            table_name = to_snake_case(current_class)
            if table_name not in foreign_keys:
                foreign_keys[table_name] = []
            in_table_args = False
            table_args_content = ""

        if current_class:
            if '__table_args__' in line:
                in_table_args = True
                table_args_content = line
            elif in_table_args:
                table_args_content += line
                if line.strip().startswith(')') and not line.strip().startswith('PrimaryKey'):
                    in_table_args = False

            if 'ForeignKey(' in line and not in_table_args:
                fk_match = re.search(r"ForeignKey\(['\"]([^'\"]+)['\"]", line)
                col_match = re.search(r"^\s+(\w+):", line)

                if fk_match and col_match:
                    ref_table_col = fk_match.group(1)
                    column_name = col_match.group(1)

                    if '.' in ref_table_col:
                        ref_table, ref_col = ref_table_col.split('.', 1)
                    else:
                        ref_table = ref_table_col
                        ref_col = "id"

                    table_name = to_snake_case(current_class)
                    foreign_keys[table_name].append(ForeignKeyInfo(
                        column=column_name,
                        references_table=ref_table,
                        references_column=ref_col,
                    ))

    if current_class and table_args_content:
        _parse_table_args_fks(current_class, table_args_content, foreign_keys)

    return foreign_keys


def _parse_table_args_fks(
    class_name: str,
    table_args_content: str,
    foreign_keys: dict[str, list[ForeignKeyInfo]]
) -> None:
    """Parse ForeignKeyConstraint from __table_args__ content.

    Handles patterns like:
    ForeignKeyConstraint(['user_id'], ['user.id'], name='session_user_id_fkey')
    ForeignKeyConstraint(['col1', 'col2'], ['other.col1', 'other.col2'])
    """
    table_name = to_snake_case(class_name)
    if table_name not in foreign_keys:
        foreign_keys[table_name] = []

    fk_pattern = r"ForeignKeyConstraint\s*\(\s*\[([^\]]+)\]\s*,\s*\[([^\]]+)\]"

    for match in re.finditer(fk_pattern, table_args_content):
        local_cols_str = match.group(1)
        ref_cols_str = match.group(2)

        local_cols = [c.strip().strip("'\"") for c in local_cols_str.split(',')]
        ref_cols = [c.strip().strip("'\"") for c in ref_cols_str.split(',')]

        for local_col, ref_col in zip(local_cols, ref_cols):
            if '.' in ref_col:
                ref_table, ref_column = ref_col.split('.', 1)
            else:
                ref_table = ref_col
                ref_column = "id"

            fk_info = ForeignKeyInfo(
                column=local_col,
                references_table=ref_table,
                references_column=ref_column,
            )
            if fk_info not in foreign_keys[table_name]:
                foreign_keys[table_name].append(fk_info)


def detect_soft_delete_column(columns: list[str], soft_delete_column: str | None) -> str | None:
    """Detect if a table has a soft delete column."""
    if soft_delete_column and soft_delete_column in columns:
        return soft_delete_column

    common_soft_delete_cols = ["deleted_at", "is_deleted", "deleted", "removed_at"]
    for col in common_soft_delete_cols:
        if col in columns:
            return col
    return None


def extract_table_info_from_sqlalchemy(file_path: Path, soft_delete_col: str | None = None) -> dict[str, TableInfo]:
    """Extract comprehensive table information from SQLAlchemy models."""
    tables: dict[str, TableInfo] = {}
    foreign_keys = extract_foreign_keys_from_sqlalchemy(file_path)

    with open(file_path) as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return tables

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
            (isinstance(b, ast.Name) and b.id == "Base") for b in node.bases
        ):
            class_name = node.name
            table_name = to_snake_case(class_name)

            columns = []
            primary_key = None

            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    col_name = item.target.id
                    columns.append(col_name)

                    if item.value and "primary_key" in ast.dump(item.value):
                        primary_key = col_name

            soft_del_col = detect_soft_delete_column(columns, soft_delete_col)

            tables[table_name] = TableInfo(
                name=table_name,
                columns=columns,
                primary_key=primary_key,
                foreign_keys=foreign_keys.get(table_name, []),
                has_soft_delete=soft_del_col is not None,
                soft_delete_column=soft_del_col,
            )

    return tables


def generate_erd(models_dir: Path, output_path: Path, dry_run: bool = False) -> bool:
    """Generate an Entity Relationship Diagram using erdantic."""
    if dry_run:
        logger.info(f"[DRY RUN] Would generate ERD: {output_path}")
        return True

    sqlalchemy_file = models_dir / "sqlalchemy_models.py"
    if not sqlalchemy_file.exists():
        logger.warning("SQLAlchemy models file not found; cannot generate ERD")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import erdantic"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            logger.warning("erdantic not installed. Install with: pip install erdantic")
            return False
    except FileNotFoundError:
        logger.warning("Could not check for erdantic")
        return False

    erd_script = f'''
import sys
sys.path.insert(0, "{models_dir.parent}")
try:
    import erdantic as erd
    from {models_dir.name}.sqlalchemy_models import Base

    models = [cls for cls in Base.__subclasses__()]
    if models:
        diagram = erd.create(*models)
        diagram.draw("{output_path}")
        print(f"ERD generated: {output_path}")
    else:
        print("No models found to diagram")
except Exception as e:
    print(f"ERD generation failed: {{e}}")
    sys.exit(1)
'''

    try:
        result = subprocess.run(
            [sys.executable, "-c", erd_script],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info(f"Generated ERD: {output_path}")
            return True
        else:
            logger.warning(f"ERD generation failed: {result.stderr or result.stdout}")
            return False
    except Exception as e:
        logger.warning(f"ERD generation failed: {e}")
        return False


def extract_model_info(file_path: Path) -> list[dict]:
    """Extract Pydantic model information from a generated file."""
    models = []
    with open(file_path) as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return models

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)

            is_pydantic_model = (
                "BaseModel" in bases or
                "CustomModel" in bases or
                "CustomModelInsert" in bases or
                "CustomModelUpdate" in bases or
                any("Base" in str(b) for b in bases)
            )

            if is_pydantic_model:
                fields = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id
                        fields.append(field_name)

                models.append({
                    "name": node.name,
                    "fields": fields,
                })

    return models


def get_sqla_class_names(sqlalchemy_file: Path) -> dict[str, str]:
    """Extract class names from the SQLAlchemy models file.

    Returns a mapping from snake_case table name to actual class name.
    """
    class_names = {}
    with open(sqlalchemy_file) as f:
        for line in f:
            if line.strip().startswith('class ') and '(Base):' in line:
                class_name = line.split('class ')[1].split('(')[0].strip()
                if class_name != 'Base':
                    table_name = to_snake_case(class_name)
                    class_names[table_name] = class_name
    return class_names


def generate_router_file(
    models: list[dict],
    models_import_path: str,
    routers_dir: Path,
    models_dir: Path,
    use_generated_sqlalchemy: bool = False,
    dry_run: bool = False,
    backup: bool = False,
    exclude_tables: list[str] | None = None,
    async_mode: bool = False,
    soft_delete_column: str | None = None,
    audit_fields: list[str] | None = None,
    generate_relationships: bool = False,
    session_dependency: str = "get_session",
) -> dict:
    """Generate a generated.py file with FastCRUD routers.

    Args:
        models: List of model info dicts
        models_import_path: Import path for Pydantic schemas
        routers_dir: Directory to write the router file
        models_dir: Directory containing generated models
        use_generated_sqlalchemy: If True, use generated SQLAlchemy models instead of pg_schemas
        dry_run: If True, don't write files, just show what would be done
        backup: If True, backup existing files before overwriting
        exclude_tables: List of table names/patterns to exclude
        async_mode: If True, generate async CRUD operations
        soft_delete_column: Column name for soft delete (e.g., 'deleted_at')
        audit_fields: Fields to exclude from create/update schemas
        generate_relationships: If True, generate relationship endpoints
        session_dependency: Name of the session dependency function

    Returns:
        Metadata dict with information about generated routers
    """
    exclude_tables = exclude_tables or []
    audit_fields = audit_fields or DEFAULT_AUDIT_FIELDS

    if not dry_run:
        routers_dir.mkdir(parents=True, exist_ok=True)

    base_models = [m for m in models if m["name"].endswith("BaseSchema")]

    sqla_class_map = {}
    table_info: dict[str, TableInfo] = {}
    if use_generated_sqlalchemy:
        sqla_file = models_dir / "sqlalchemy_models.py"
        if sqla_file.exists():
            sqla_class_map = get_sqla_class_names(sqla_file)
            table_info = extract_table_info_from_sqlalchemy(sqla_file, soft_delete_column)

    pydantic_imports = []
    sqlalchemy_imports = []
    router_definitions = []
    router_includes = []
    created_routers = []
    relationship_routers = []

    session_type = "AsyncSession" if async_mode else "DBSession"
    session_import = "from sqlalchemy.ext.asyncio import AsyncSession" if async_mode else "from sqlalchemy.orm import Session as DBSession"
    crud_decorator = "async " if async_mode else ""
    await_prefix = "await " if async_mode else ""

    for model in base_models:
        base_name = model["name"]
        entity_name = base_name.replace("BaseSchema", "")
        insert_name = f"{entity_name}Insert"
        update_name = f"{entity_name}Update"
        table_name = to_snake_case(entity_name)

        if should_exclude_table(table_name, exclude_tables):
            logger.debug(f"Excluding table: {table_name}")
            continue

        if use_generated_sqlalchemy:
            sqla_model_name = (
                sqla_class_map.get(table_name) or
                sqla_class_map.get(table_name + 's') or
                sqla_class_map.get(table_name + 'es') or
                sqla_class_map.get(table_name.rstrip('y') + 'ies')
            )
            if not sqla_model_name:
                logger.warning(f"No SQLAlchemy model found for {table_name}, skipping")
                continue
        else:
            sqla_model_name = entity_name

        pydantic_imports.extend([insert_name, update_name])
        sqlalchemy_imports.append(sqla_model_name)

        tbl_info = table_info.get(table_name)
        has_soft_delete = tbl_info.has_soft_delete if tbl_info else False
        soft_del_col = tbl_info.soft_delete_column if tbl_info else None

        router_opts = [
            f"session={session_dependency}",
            f"model={sqla_model_name}",
            f"create_schema={insert_name}",
            f"update_schema={update_name}",
            f'path="/{table_name}"',
            f'tags=["{table_name}"]',
        ]

        if has_soft_delete and soft_del_col:
            router_opts.append(f'is_deleted_column="{soft_del_col}"')
            if soft_del_col in ("deleted_at", "removed_at", "archived_at"):
                router_opts.append(f'deleted_at_column="{soft_del_col}"')

        router_definitions.append(f'''
{table_name}_router = crud_router(
    {(',' + chr(10) + '    ').join(router_opts)},
)''')

        router_includes.append(f"    app.include_router({table_name}_router, prefix=prefix)")
        created_routers.append(f"{table_name}_router")

        if generate_relationships and tbl_info and tbl_info.foreign_keys:
            for fk in tbl_info.foreign_keys:
                ref_table = fk.references_table
                ref_pascal = to_pascal_case(ref_table.rstrip('s'))

                rel_router_name = f"{table_name}_by_{fk.column}_router"
                relationship_routers.append({
                    "name": rel_router_name,
                    "parent_table": ref_table,
                    "child_table": table_name,
                    "fk_column": fk.column,
                })

    sqlalchemy_import_path = models_import_path.replace(".fastapi.schema_public_latest", ".sqlalchemy_models")

    if use_generated_sqlalchemy:
        sqlalchemy_import_block = f'''from {sqlalchemy_import_path} import (
    {(',' + chr(10) + '    ').join(sorted(set(sqlalchemy_imports)))},
)'''
    else:
        sqlalchemy_import_block = f'''# Import SQLAlchemy models - update path as needed
try:
    from src.core.db.pg_schemas import (
        {(',' + chr(10) + '        ').join(sorted(set(sqlalchemy_imports)))},
    )
except ImportError:
    # Fallback to generated models
    from {sqlalchemy_import_path} import (
        {(',' + chr(10) + '        ').join(sorted(set(sqlalchemy_imports)))},
    )'''

    relationship_code = ""
    if generate_relationships and relationship_routers:
        rel_definitions = []
        rel_includes = []

        for rel in relationship_routers:
            parent_pascal = to_pascal_case(rel["parent_table"].rstrip('s'))
            child_pascal = to_pascal_case(rel["child_table"].rstrip('s'))

            rel_definitions.append(f'''
# Relationship: {rel["child_table"]} belongs to {rel["parent_table"]} via {rel["fk_column"]}
{rel["name"]} = APIRouter(tags=["{rel["parent_table"]}-{rel["child_table"]}"])

@{rel["name"]}.get("/{rel["parent_table"]}/{{parent_id}}/{rel["child_table"]}")
{crud_decorator}def get_{rel["child_table"]}_by_{rel["fk_column"]}(
    parent_id: int,
    db: {session_type} = Depends({session_dependency}),
    skip: int = 0,
    limit: int = 100,
):
    """Get {rel["child_table"]} records by {rel["fk_column"]}."""
    query = select({child_pascal}).where({child_pascal}.{rel["fk_column"]} == parent_id).offset(skip).limit(limit)
    result = {await_prefix}db.execute(query)
    return result.scalars().all()
''')

            rel_includes.append(f'    app.include_router({rel["name"]}, prefix=f"{{prefix}}")')

        relationship_code = f'''

# Relationship routers
{"".join(rel_definitions)}

def register_relationship_routers(app: FastAPI, prefix: str = "/api/v1/db") -> None:
    """Register relationship routers with the FastAPI app."""
{chr(10).join(rel_includes)}
'''

    extra_imports = ""
    if generate_relationships:
        extra_imports = f'''
{session_import}
from sqlalchemy import select
from fastapi import Depends, APIRouter
'''

    mode_comment = "# Mode: ASYNC" if async_mode else "# Mode: SYNC"
    soft_delete_comment = f"# Soft Delete: enabled (column: {soft_delete_column})" if soft_delete_column else "# Soft Delete: disabled"

    content = f'''"""
Auto-generated by crudzilla v{__version__}
https://github.com/anthropics/crudzilla-py

DO NOT EDIT THIS FILE DIRECTLY - it will be overwritten on regeneration.

FastCRUD routers from database schema.
Pydantic schemas from: {models_import_path}
SQLAlchemy models from: {sqlalchemy_import_path if use_generated_sqlalchemy else "src.core.db.pg_schemas (with fallback)"}
{mode_comment}
{soft_delete_comment}
# Audit fields excluded from create/update: {audit_fields}

Usage in main.py:
    from src.app.routers.generated.generated import register_generated_routers
    register_generated_routers(app, prefix="/api/v1/db")

Requirements:
    pip install fastcrud
"""

from fastapi import FastAPI
from fastcrud import crud_router

from {models_import_path} import (
    {(',' + chr(10) + '    ').join(sorted(set(pydantic_imports)))},
)
{sqlalchemy_import_block}
{extra_imports}
# Database session dependency - update this import path as needed
# from src.core.db.session import {session_dependency}
def {session_dependency}():
    raise NotImplementedError("Configure your database session dependency")


# Generated FastCRUD routers
{"".join(router_definitions)}


def register_generated_routers(app: FastAPI, prefix: str = "/api/v1/db") -> None:
    """Register all generated CRUD routers with the FastAPI app."""
{chr(10).join(router_includes)}

{relationship_code}

all_routers = [
    {(',' + chr(10) + '    ').join(created_routers)},
]

__all__ = ["register_generated_routers", "all_routers"{', "register_relationship_routers"' if relationship_routers else ''}]
'''

    output_file = routers_dir / "generated.py"
    metadata = {
        "output_file": str(output_file),
        "routers_count": len(created_routers),
        "routers": [r.replace("_router", "") for r in created_routers],
        "pydantic_imports": sorted(set(pydantic_imports)),
        "sqlalchemy_imports": sorted(set(sqlalchemy_imports)),
        "async_mode": async_mode,
        "soft_delete_enabled": soft_delete_column is not None,
        "audit_fields": audit_fields,
        "relationship_routers": len(relationship_routers),
    }

    if dry_run:
        logger.info(f"[DRY RUN] Would generate: {output_file}")
        logger.info(f"[DRY RUN] Mode: {'async' if async_mode else 'sync'}")
        logger.info(f"[DRY RUN] Would contain {len(created_routers)} FastCRUD routers: {', '.join(metadata['routers'])}")
        if relationship_routers:
            logger.info(f"[DRY RUN] Would contain {len(relationship_routers)} relationship routers")
        return metadata

    if backup:
        backup_file(output_file)

    with open(output_file, "w") as f:
        f.write(content)

    if not validate_python_file(output_file):
        logger.error(f"Generated file has syntax errors: {output_file}")

    logger.info(f"Generated: {output_file}")
    logger.info(f"Mode: {'async' if async_mode else 'sync'}")
    logger.info(f"Contains {len(created_routers)} FastCRUD routers")
    if relationship_routers:
        logger.info(f"Contains {len(relationship_routers)} relationship routers")

    return metadata


def generate_routers(
    models_dir: Path,
    routers_dir: Path,
    use_generated_sqlalchemy: bool = False,
    dry_run: bool = False,
    backup: bool = False,
    exclude_tables: list[str] | None = None,
    schema: str = "public",
    async_mode: bool = False,
    soft_delete_column: str | None = None,
    audit_fields: list[str] | None = None,
    generate_relationships: bool = False,
    session_dependency: str = "get_session",
) -> dict | None:
    """Generate FastCRUD routers from Pydantic models."""
    fastapi_dir = models_dir / "fastapi"
    search_dir = fastapi_dir if fastapi_dir.exists() else models_dir

    latest_file = search_dir / f"schema_{schema}_latest.py"
    if latest_file.exists():
        model_files = [latest_file]
    else:
        model_files = [f for f in search_dir.glob("*.py") if not f.name.startswith("_")]

    if not model_files:
        logger.error(f"No model files found in {search_dir}")
        return None

    models_import_path = str(models_dir).replace("/", ".") + f".fastapi.schema_{schema}_latest"

    all_models = []
    for model_file in model_files:
        models = extract_model_info(model_file)
        all_models.extend(models)

    if not all_models:
        logger.error("No models found in generated files")
        return None

    return generate_router_file(
        all_models,
        models_import_path,
        routers_dir,
        models_dir,
        use_generated_sqlalchemy,
        dry_run=dry_run,
        backup=backup,
        exclude_tables=exclude_tables,
        async_mode=async_mode,
        soft_delete_column=soft_delete_column,
        audit_fields=audit_fields,
        generate_relationships=generate_relationships,
        session_dependency=session_dependency,
    )


CRUDZILLA_HEADER = f'''"""
Auto-generated by crudzilla v{__version__}
https://github.com/anthropics/crudzilla-py

DO NOT EDIT THIS FILE DIRECTLY - it will be overwritten on regeneration.
"""

'''


def add_crudzilla_header(file_path: Path) -> None:
    """Add crudzilla header to a generated file if not already present."""
    with open(file_path) as f:
        content = f.read()

    if "Auto-generated by crudzilla" in content:
        return

    if content.startswith('"""'):
        end_docstring = content.find('"""', 3)
        if end_docstring != -1:
            content = CRUDZILLA_HEADER + content[end_docstring + 3:].lstrip('\n')
    else:
        content = CRUDZILLA_HEADER + content

    with open(file_path, 'w') as f:
        f.write(content)


def fix_sqlalchemy_models(file_path: Path) -> None:
    """Post-process SQLAlchemy models to fix common issues.

    Fixes:
    1. Add missing __tablename__ attributes
    2. Rename reserved column names (metadata -> metadata_)
    3. Fix ARRAY types without item_type
    4. Add crudzilla header
    """
    with open(file_path) as f:
        content = f.read()

    reserved_columns = ['metadata']
    for col in reserved_columns:
        content = content.replace(f'    {col}: Mapped[', f'    {col}_: Mapped[')
        content = content.replace(f'"{col}"', f'"{col}_"')

    content = content.replace('mapped_column(ARRAY,', 'mapped_column(ARRAY(String),')

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        if line.strip().startswith('class ') and '(Base):' in line:
            class_name = line.split('class ')[1].split('(')[0].strip()
            table_name = to_snake_case(class_name) + 's'

            if i + 1 < len(lines) and 'Class for table:' in lines[i + 1]:
                comment_line = lines[i + 1]
                if 'Class for table:' in comment_line:
                    table_name = comment_line.split('Class for table:')[1].strip()
                new_lines.append(lines[i + 1])
                i += 1

            new_lines.append(f'    __tablename__ = "{table_name}"')
            new_lines.append('')

        i += 1

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))

    add_crudzilla_header(file_path)


def cleanup_old_versions(output_path: Path) -> None:
    """Remove old timestamped versions, keeping only the latest files."""
    for subdir in ["fastapi", "sqlalchemy"]:
        subdir_path = output_path / subdir
        if not subdir_path.exists():
            continue

        for prefix in ["schema_public_", "database_public_"]:
            files = list(subdir_path.glob(f"{prefix}*.py"))
            latest_file = subdir_path / f"{prefix}latest.py"

            for f in files:
                if f != latest_file and f.name != "__init__.py":
                    f.unlink()


def generate_sqlalchemy_models(output_path: Path, db_url: str, dry_run: bool = False, backup: bool = False) -> bool:
    """Generate SQLAlchemy models using sqlacodegen."""
    output_file = output_path / "sqlalchemy_models.py"

    if ':5432' not in db_url and '@' in db_url:
        parts = db_url.split('@')
        host_part = parts[1].split('/')[0]
        if ':' not in host_part:
            db_url = db_url.replace(host_part, host_part + ':5432')

    if dry_run:
        logger.info(f"[DRY RUN] Would generate SQLAlchemy models: {output_file}")
        return True

    if backup:
        backup_file(output_file)

    cmd = [
        sys.executable, "-m", "sqlacodegen",
        db_url,
        "--generator", "declarative",
        "--outfile", str(output_file),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        fix_sqlalchemy_models(output_file)
        logger.info(f"Generated SQLAlchemy models: {output_file.name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"sqlacodegen failed: {e.stderr.decode() if e.stderr else e}")
        return False
    except FileNotFoundError:
        logger.warning("sqlacodegen not found. Install with: pip install sqlacodegen")
        return False


def generate_models(
    output_dir: str = "generated_models",
    include_sqlalchemy: bool = True,
    verbose: bool = True,
    env_file: Path | None = None,
    dry_run: bool = False,
    backup: bool = False,
    schema: str = "public",
) -> dict:
    """Generate Pydantic and optionally SQLAlchemy models from database schema."""
    db_url = get_database_url(env_file)

    output_path = Path(output_dir)

    metadata = {
        "output_dir": str(output_path.absolute()),
        "schema": schema,
        "include_sqlalchemy": include_sqlalchemy,
        "dry_run": dry_run,
        "pydantic_files": [],
        "sqlalchemy_file": None,
    }

    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        cleanup_old_versions(output_path)

    logger.info(f"Generating models to: {output_path.absolute()}")
    logger.info(f"Schema: {schema}")
    logger.info(f"Include SQLAlchemy: {include_sqlalchemy}")

    if dry_run:
        logger.info("[DRY RUN] Would generate Pydantic models with sb-pydantic")
        metadata["pydantic_files"] = [f"schema_{schema}_latest.py"]
    else:
        cmd = [
            sys.executable, "-m", "supabase_pydantic", "gen",
            "--type", "pydantic",
            "--framework", "fastapi",
            "--db-url", db_url,
            "-d", str(output_path),
            "--singular-names",
        ]

        if verbose:
            cmd.append("-v")

        try:
            subprocess.run(cmd, check=True, capture_output=False)
            logger.info("Pydantic models generated successfully")

            fastapi_dir = output_path / "fastapi"
            if fastapi_dir.exists():
                generated_files = list(fastapi_dir.glob("schema_*.py"))
                metadata["pydantic_files"] = [f.name for f in generated_files]
                if generated_files:
                    logger.info(f"Generated {len(generated_files)} Pydantic schema file(s)")
                    for f in generated_files:
                        add_crudzilla_header(f)
                        if not validate_python_file(f):
                            logger.warning(f"Generated file has syntax issues: {f}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Error generating Pydantic models: {e}")
            sys.exit(1)
        except FileNotFoundError:
            logger.error("supabase-pydantic not found. Install with: pip install supabase-pydantic")
            sys.exit(1)

    if include_sqlalchemy:
        logger.info("Generating SQLAlchemy models with sqlacodegen...")
        if generate_sqlalchemy_models(output_path, db_url, dry_run=dry_run, backup=backup):
            metadata["sqlalchemy_file"] = "sqlalchemy_models.py"

    return metadata


def run_with_config(config: GeneratorConfig) -> dict:
    """Execute generation with the provided configuration."""
    if config.verbose:
        setup_logging(verbose=True)
    elif config.quiet:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
    else:
        setup_logging(verbose=False)

    all_metadata: dict[str, Any] = {}

    include_sqla = config.include_sqlalchemy or config.use_generated_sqlalchemy or config.generate_erd
    models_metadata = generate_models(
        output_dir=config.output_dir,
        include_sqlalchemy=include_sqla,
        verbose=not config.quiet and not config.dry_run,
        env_file=config.env_file,
        dry_run=config.dry_run,
        backup=config.backup,
        schema=config.schema,
    )
    all_metadata["models"] = models_metadata

    if config.generate_routers:
        logger.info("Generating FastCRUD routers...")
        routers_metadata = generate_routers(
            models_dir=Path(config.output_dir),
            routers_dir=Path(config.routers_dir),
            use_generated_sqlalchemy=config.use_generated_sqlalchemy,
            dry_run=config.dry_run,
            backup=config.backup,
            exclude_tables=config.exclude_tables,
            schema=config.schema,
            async_mode=config.async_mode,
            soft_delete_column=config.soft_delete_column,
            audit_fields=config.audit_fields,
            generate_relationships=config.generate_relationships,
            session_dependency=config.session_dependency,
        )
        if routers_metadata:
            all_metadata["routers"] = routers_metadata

    if config.generate_erd:
        logger.info("Generating ERD...")
        erd_path = Path(config.output_dir) / config.erd_output
        if generate_erd(Path(config.output_dir), erd_path, config.dry_run):
            all_metadata["erd"] = str(erd_path)

    if config.export_metadata:
        if config.dry_run:
            logger.info(f"[DRY RUN] Would export metadata to: {config.export_metadata}")
        else:
            with open(config.export_metadata, "w") as f:
                json.dump(all_metadata, f, indent=2)
            logger.info(f"Exported metadata to: {config.export_metadata}")

    return all_metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Pydantic models and FastCRUD routers from database schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Generate Pydantic models only
  %(prog)s --include-sqlalchemy               # Include SQLAlchemy models
  %(prog)s --generate-routers                 # Also generate FastCRUD routers
  %(prog)s --generate-routers --async-mode    # Generate async CRUD routers
  %(prog)s --session-dependency get_async_db  # Custom session dependency name
  %(prog)s --env-file /path/to/.env           # Use specific env file
  %(prog)s --dry-run --verbose                # Preview what would be generated
  %(prog)s --exclude-tables users sessions    # Exclude specific tables
  %(prog)s --schema public --backup           # Backup existing files
  %(prog)s --config pyproject.toml            # Load config from TOML file
  %(prog)s --generate-erd                     # Generate ERD diagram
  %(prog)s --soft-delete-column deleted_at    # Enable soft delete
  %(prog)s --generate-relationships           # Generate relationship endpoints
  %(prog)s --watch                            # Watch for schema changes (dev mode)
  %(prog)s --watch --watch-interval 10        # Watch with custom interval

Config file (pyproject.toml):
  [tool.db-generator]
  output-dir = "src/models/generated"
  async-mode = true
  soft-delete-column = "deleted_at"
  audit-fields = ["created_at", "updated_at"]
  exclude-tables = ["audit_*", "*_log"]
  session-dependency = "get_async_db"
  watch-interval = 10
        """
    )

    parser.add_argument(
        "-c", "--config",
        type=Path,
        metavar="FILE",
        help="Load configuration from TOML file (pyproject.toml or dedicated config)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="generated_models",
        help="Output directory for generated models (default: generated_models)"
    )
    parser.add_argument(
        "--routers-dir",
        default="src/app/routers/generated",
        help="Output directory for generated routers (default: src/app/routers/generated)"
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to .env file containing DATABASE_URL"
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="Database schema to introspect (default: public)"
    )
    parser.add_argument(
        "--exclude-tables",
        nargs="+",
        default=[],
        metavar="TABLE",
        help="Tables to exclude from router generation (supports wildcards: 'audit_*', '*_log')"
    )
    parser.add_argument(
        "--include-sqlalchemy",
        action="store_true",
        help="Also generate SQLAlchemy models"
    )
    parser.add_argument(
        "--generate-routers",
        action="store_true",
        help="Generate FastCRUD routers from the Pydantic models"
    )
    parser.add_argument(
        "--use-generated-sqlalchemy",
        action="store_true",
        help="Use generated SQLAlchemy models instead of pg_schemas.py"
    )
    parser.add_argument(
        "--async-mode",
        action="store_true",
        help="Generate async CRUD operations (requires AsyncSession)"
    )
    parser.add_argument(
        "--soft-delete-column",
        metavar="COLUMN",
        help="Enable soft delete with specified column (e.g., 'deleted_at')"
    )
    parser.add_argument(
        "--audit-fields",
        nargs="+",
        default=None,
        metavar="FIELD",
        help=f"Fields to exclude from create/update schemas (default: {DEFAULT_AUDIT_FIELDS})"
    )
    parser.add_argument(
        "--generate-relationships",
        action="store_true",
        help="Generate relationship endpoints based on foreign keys"
    )
    parser.add_argument(
        "--session-dependency",
        default="get_session",
        metavar="NAME",
        help="Name of the database session dependency function (default: get_session)"
    )
    parser.add_argument(
        "--generate-erd",
        action="store_true",
        help="Generate Entity Relationship Diagram (requires erdantic)"
    )
    parser.add_argument(
        "--erd-output",
        default=None,
        metavar="FILE",
        help="Output path for ERD diagram (default: <output-dir>/erd.png)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup existing files before overwriting"
    )
    parser.add_argument(
        "--export-metadata",
        type=Path,
        metavar="FILE",
        help="Export generation metadata to JSON file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Watch for schema changes and auto-regenerate (useful in development)"
    )
    parser.add_argument(
        "--watch-interval",
        type=int,
        default=5,
        metavar="SECONDS",
        help="Interval between schema checks in watch mode (default: 5)"
    )

    args = parser.parse_args()

    if args.verbose and args.quiet:
        parser.error("--verbose and --quiet are mutually exclusive")

    if args.config and args.config.exists():
        logger.info(f"Loading configuration from: {args.config}")
        config = GeneratorConfig.from_toml(args.config)
        config = config.merge_cli_args(args)
    else:
        config = GeneratorConfig(
            output_dir=args.output_dir,
            routers_dir=args.routers_dir,
            schema=args.schema,
            include_sqlalchemy=args.include_sqlalchemy,
            generate_routers=args.generate_routers,
            use_generated_sqlalchemy=args.use_generated_sqlalchemy,
            async_mode=args.async_mode,
            soft_delete_column=args.soft_delete_column,
            audit_fields=args.audit_fields or DEFAULT_AUDIT_FIELDS,
            exclude_tables=args.exclude_tables,
            generate_erd=args.generate_erd,
            erd_output=args.erd_output or "erd.png",
            generate_relationships=args.generate_relationships,
            session_dependency=args.session_dependency,
            dry_run=args.dry_run,
            backup=args.backup,
            verbose=args.verbose,
            quiet=args.quiet,
            env_file=args.env_file,
            export_metadata=args.export_metadata,
            watch=args.watch,
            watch_interval=args.watch_interval,
        )

    if config.watch:
        if config.dry_run:
            parser.error("--watch and --dry-run are mutually exclusive")
        run_watch_mode(config, run_with_config)
    else:
        run_with_config(config)


if __name__ == "__main__":
    main()
