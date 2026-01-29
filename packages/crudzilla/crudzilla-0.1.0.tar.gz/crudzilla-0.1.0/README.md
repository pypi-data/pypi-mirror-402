# crudzilla

Generate Pydantic models and FastCRUD routers from your PostgreSQL database schema.

## Installation

```bash
pip install crudzilla
# or
uv add crudzilla
```

## Quick Start

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mydb"

crudzilla                                    # Pydantic models only
crudzilla --generate-routers                 # Include FastCRUD routers
crudzilla --generate-routers --include-sqlalchemy  # Full generation
```

## Options

| Option | Description |
|--------|-------------|
| `-o, --output-dir` | Output directory for models (default: `generated_models`) |
| `--routers-dir` | Output directory for routers (default: `src/app/routers/generated`) |
| `--env-file` | Path to `.env` file containing `DATABASE_URL` |
| `--schema` | Database schema (default: `public`) |
| `--exclude-tables` | Tables to exclude (supports wildcards: `audit_*`, `*_log`) |
| `--include-sqlalchemy` | Generate SQLAlchemy models |
| `--generate-routers` | Generate FastCRUD routers |
| `--async-mode` | Generate async CRUD operations |
| `--dry-run` | Preview without writing files |
| `--backup` | Backup existing files before overwriting |
| `-v, --verbose` | Verbose output |

## Output Structure

```
generated_models/
├── fastapi/
│   └── schema_public_latest.py    # Pydantic schemas
└── sqlalchemy_models.py           # SQLAlchemy models

src/app/routers/generated/
└── generated.py                   # FastCRUD routers
```

## Usage in FastAPI

```python
from fastapi import FastAPI
from src.app.routers.generated.generated import register_generated_routers

app = FastAPI()
register_generated_routers(app, prefix="/api/v1/db")
```

## License

MIT
