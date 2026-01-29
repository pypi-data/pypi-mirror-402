import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    # Просто создание движка и проверка диалекта
    engine = create_async_engine("firebird+firebirdsql_async://user:pass@localhost/db")
    print(f"✅ Engine created: {engine}")
    print(f"✅ Dialect: {engine.dialect.name}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
