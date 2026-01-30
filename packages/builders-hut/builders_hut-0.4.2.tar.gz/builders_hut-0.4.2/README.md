<p align="center">
  <pre>
 ____        _ _     _                 _   _       _   
| __ ) _   _(_) | __| | ___ _ __ ___  | | | |_   _| |_ 
|  _ \| | | | | |/ _` |/ _ \ '__/ __| | |_| | | | | __|
| |_) | |_| | | | (_| |  __/ |  \__ \ |  _  | |_| | |_ 
|____/ \__,_|_|_|\__,_|\___|_|  |___/ |_| |_|\__,_|\__|
  </pre>
</p>

<p align="center">
  <strong>🏠 FastAPI Scaffolding Tool</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/builders-hut/"><img src="https://img.shields.io/pypi/v/builders-hut?color=purple&style=flat-square" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/builders-hut/"><img src="https://img.shields.io/pypi/pyversions/builders-hut?style=flat-square" alt="Python Versions"></a>
  <a href="https://opensource.org/licenses/BSD-3-Clause"><img src="https://img.shields.io/badge/license-BSD--3--Clause-blue?style=flat-square" alt="License"></a>
</p>

---

## Overview

**Builders Hut** is a powerful command-line tool that scaffolds production-ready FastAPI projects in seconds. Stop wasting time on boilerplate—start building features immediately with a clean, scalable project structure.

### Why Builders Hut?

- ⚡ **Instant Setup** — Generate a complete FastAPI project with one command
- 🏗️ **Production-Ready Architecture** — Clean separation of concerns with repositories, services, and schemas
- 🎨 **Beautiful Defaults** — Stunning landing page and Scalar API documentation out of the box
- 🔧 **Zero Configuration** — Auto-creates virtual environment and installs dependencies
- 🌐 **Cross-Platform** — Works seamlessly on Windows and Linux

---

## Installation

```bash
pip install builders-hut
```

> **Requires Python 3.13+**

---

## Quick Start

Create a new FastAPI project in seconds:

```bash
# Interactive mode (prompts for details)
hut build

# Or provide all options directly
hut build --name "my-api" --description "My awesome API" --version "1.0.0" --path ./my-project
```

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--name` | `-n` | Project name | *(prompted)* |
| `--description` | `-d` | Project description | `A new project` |
| `--version` | `-v` | Project version | `0.1.0` |
| `--path` | `-p` | Output directory | `./demo` |

---

## Generated Project Structure

Builders Hut creates a clean, scalable architecture following best practices:

```
my-project/
├── .venv/                    # Virtual environment (auto-created)
├── .env                      # Environment configuration
├── pyproject.toml            # Project metadata & dependencies
│
├── app/
│   ├── main.py               # FastAPI application entry point
│   │
│   ├── api/                  # API route definitions
│   │   ├── __init__.py
│   │   ├── common.py         # Common routes (health, docs, home)
│   │   └── v1/               # Version 1 endpoints
│   │       └── __init__.py
│   │
│   ├── core/                 # Core configuration
│   │   ├── config.py         # Pydantic settings management
│   │   └── logger.py         # Logging configuration
│   │
│   ├── database/             # Database connections & sessions
│   │   └── __init__.py
│   │
│   ├── models/               # ORM / data models
│   │   └── __init__.py
│   │
│   ├── schemas/              # Pydantic request/response schemas
│   │   └── __init__.py
│   │
│   ├── services/             # Business logic layer
│   │   └── __init__.py
│   │
│   ├── repositories/         # Data access layer
│   │   └── __init__.py
│   │
│   ├── workers/              # Background jobs & async workers
│   │   └── __init__.py
│   │
│   ├── utils/                # Utility functions
│   │   └── __init__.py
│   │
│   ├── scripts/              # Server run scripts
│   │   ├── dev.py            # Development server (with hot reload)
│   │   └── prod.py           # Production server
│   │
│   └── templates/            # Jinja2 templates
│       └── index.html        # Beautiful landing page
│
└── tests/                    # Unit & integration tests
    └── __init__.py
```

---

## Features

### 🎨 Beautiful Landing Page

Every project comes with a stunning, responsive landing page that displays API status in real-time with automatic health checks.

<p align="center">
  <em>Dark theme with purple accents • Real-time status monitoring • Link to API docs</em>
</p>

### 📚 Scalar API Documentation

Forget Swagger UI—your API ships with [Scalar](https://scalar.com/), a modern, beautiful API documentation interface.

- Dark mode by default
- Interactive API testing
- Clean, developer-friendly design

Access at: `http://localhost:8000/docs`

### ⚙️ Pydantic Settings

Type-safe configuration management with automatic environment variable loading:

```python
from app.core.config import settings

print(settings.TITLE)        # Your project name
print(settings.DEBUG)        # True/False
print(settings.PORT)         # 8000
```

### 🔄 Health Check Endpoint

Built-in health monitoring at `/health`:

```json
{ "status": "ok" }
```

---

## Running Your Project

After scaffolding, navigate to your project and run:

```bash
cd my-project

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Start development server (with hot reload)
run_dev_server

# Or run directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:
- **Landing Page:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Included Dependencies

Your scaffolded project comes with these essential packages pre-installed:

| Package | Purpose |
|---------|---------|
| `fastapi` | High-performance web framework |
| `uvicorn` | Lightning-fast ASGI server |
| `pydantic-settings` | Type-safe configuration management |
| `python-dotenv` | Environment variable loading |
| `scalar-fastapi` | Modern API documentation |
| `jinja2` | Template rendering |
| `email-validator` | Email validation support |
| `tzdata` | Timezone data |
| `pytest` | Testing framework (dev) |

---

## Environment Configuration

The generated `.env` file contains essential configuration:

```env
TITLE="my-api"
DESCRIPTION="My awesome API"
VERSION="1.0.0"
DEBUG=True
PORT=8000
HOST="0.0.0.0"
```

All values are automatically loaded via Pydantic Settings and accessible through `settings`.

---

## Architecture Philosophy

Builders Hut follows a **layered architecture** pattern for clean, maintainable code:

```
┌─────────────────────────────────────┐
│            API Routes               │  ← HTTP request/response handling
├─────────────────────────────────────┤
│            Services                 │  ← Business logic
├─────────────────────────────────────┤
│           Repositories              │  ← Data access abstraction
├─────────────────────────────────────┤
│         Database / Models           │  ← Data persistence
└─────────────────────────────────────┘
```

- **API Layer** — Handles HTTP requests, validation, and responses
- **Service Layer** — Contains business logic, orchestrates operations
- **Repository Layer** — Abstracts database access, enables testing
- **Model Layer** — Defines data structures and ORM models

---

## Examples

### Create a Simple CRUD API

After scaffolding, add a new endpoint in `app/api/v1/`:

```python
# app/api/v1/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def get_users():
    return [{"id": 1, "name": "John"}]

@router.post("/")
async def create_user(name: str):
    return {"id": 2, "name": name}
```

Register in `app/api/__init__.py`:

```python
from app.api.common import router as common_router
from app.api.v1.users import router as users_router

__all__ = ["common_router", "users_router"]
```

Include in `app/main.py`:

```python
from app.api import common_router, users_router

app.include_router(common_router)
app.include_router(users_router, prefix="/api/v1")
```

---

## Roadmap

- [ ] Logger configuration
- [ ] Database setup wizards (PostgreSQL, SQLite, MongoDB)
- [ ] `hut add` command for adding components to existing projects
- [ ] Authentication templates (JWT, OAuth)
- [ ] Docker & docker-compose generation
- [ ] CI/CD pipeline templates

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone the repository
git clone https://github.com/Agsdovah95/builders-hut.git
cd builders-hut

# Install in development mode
pip install -e .
```

---

## License

This project is licensed under the **BSD-3-Clause License** — see the [LICENSE.txt](LICENSE.txt) file for details.

---

## Author

**Arnab Gupta**  
📧 arnabgupta84@gmail.com  
🔗 [GitHub](https://github.com/Agsdovah95)

---

<p align="center">
  <sub>Built with ❤️ for the FastAPI community</sub>
</p>
