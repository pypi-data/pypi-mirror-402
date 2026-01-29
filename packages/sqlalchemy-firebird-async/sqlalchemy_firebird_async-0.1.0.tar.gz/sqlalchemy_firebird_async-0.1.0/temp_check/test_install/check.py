import sys
from sqlalchemy.dialects import registry
from sqlalchemy.ext.asyncio import create_async_engine

print("--- Checking installation ---")

# 1. Проверяем, видит ли Алхимия наши Entry Points
# (Это самый надежный способ узнать, сработала ли магия pyproject.toml)
available = registry.load("firebird.fdb_async")
print(f"✅ Found 'firebird.fdb_async': {available}")

available_aio = registry.load("firebird.firebirdsql_async")
print(f"✅ Found 'firebird.firebirdsql_async': {available_aio}")

# 2. Пробуем создать движок (без подключения)
try:
    # Пробуем схему для fdb
    engine = create_async_engine("firebird+fdb_async://u:p@localhost/db")
    print(f"✅ Engine created for fdb_async. Dialect: {engine.dialect.name}")
    
    # Пробуем схему для firebirdsql
    engine2 = create_async_engine("firebird+firebirdsql_async://u:p@localhost/db")
    print(f"✅ Engine created for firebirdsql_async. Dialect: {engine2.dialect.name}")

except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

print("--- SUCCESS: Package is ready for PyPI ---")
