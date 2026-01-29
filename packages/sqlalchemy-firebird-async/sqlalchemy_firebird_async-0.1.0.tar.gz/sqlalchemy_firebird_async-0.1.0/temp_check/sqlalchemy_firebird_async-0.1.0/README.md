## Installation
pip install sqlalchemy-firebird-async[all]

## Usage

### 1. Using Native Async Driver (Recommended)
Use `firebirdsql` library (pure python, asyncio).

```python
from sqlalchemy.ext.asyncio import create_async_engine

# URL scheme: firebird+firebirdsql_async://...
engine = create_async_engine(
    "firebird+firebirdsql_async://sysdba:masterkey@localhost/db"
)

2. Using Legacy FDB Driver
Uses fdb library in a threadpool.

Python

# URL scheme: firebird+fdb_async://...
engine = create_async_engine(
    "firebird+fdb_async://sysdba:masterkey@localhost/db"
)

