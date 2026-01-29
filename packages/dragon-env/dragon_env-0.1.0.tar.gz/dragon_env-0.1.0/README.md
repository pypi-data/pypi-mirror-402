# dragon-env

Small, clean utility to load, validate, and type-cast environment variables (with automatic `.env` loading).

## Installation

```bash
pip install dragon-env
```

## Basic usage

```python
from dragon_env import env, EnvError

PORT = env("PORT", cast=int)
DEBUG = env("DEBUG", default=False, cast=bool, required=False)

try:
    DATABASE_URL = env("DATABASE_URL")
except EnvError as e:
    raise SystemExit(str(e))
```

## Example `.env`

```dotenv
PORT=8000
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost:5432/app
```

