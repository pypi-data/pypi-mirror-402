import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    # URL из нашего conftest
    url = "firebird+firebirdsql_async://testuser:testpass@localhost:32785//var/lib/firebird/data/test.fdb?charset=UTF8"
    engine = create_async_engine(url)
    
    try:
        async with engine.connect() as conn:
            print("🔌 Connected")
            # Просто select 1
            res = await conn.execute(text("SELECT 1 FROM rdb$database"))
            print(f"📊 Result: {res.scalar()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
