#!/usr/bin/env python3
import argparse
import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Импортируем алхимию (регистрация произойдет автоматически при импорте create_async_engine,
# если пакет установлен корректно)
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Твои модели (убедись, что этот импорт работает в окружении)
from db.sql_models import Signatures, Transactions

BASE_SQL_QUERY = """
SELECT
    t.UUID AS TRANS_UUID,
    t.HASH AS TRANS_HASH,
    t.BODY AS TRANS_BODY,
    s.SIGNATURE_XDR,
    d.DESCRIPTION AS DECISION_DESC
FROM T_TRANSACTIONS t
LEFT JOIN T_SIGNATURES s ON s.ADD_DT >= t.ADD_DT
LEFT JOIN T_DECISIONS d ON d.DESCRIPTION LIKE ('%' || t.UUID || '%')
ORDER BY CHAR_LENGTH(d.DESCRIPTION) DESC, s.ADD_DT ASC
"""

DEFAULT_DSN = "firebird+fdb_async://SYSDBA:sysdba@127.0.0.1///db/eurmtl.fdb"

def build_async_dsn(dsn: str, target_scheme: str = None) -> str:
    """
    Преобразует любой DSN в правильный асинхронный формат пакета.
    """
    # Если явно попросили конкретную схему
    if target_scheme:
        if "://" in dsn:
            base = dsn.split("://", 1)[1]
            return f"firebird+{target_scheme}://{base}"
        return f"firebird+{target_scheme}://{dsn}"

    # Автоматическая замена старых вариантов на новые стандартные
    if "firebird+fdb_async://" in dsn: return dsn
    if "firebird+firebirdsql_async://" in dsn: return dsn
    
    # Легаси маппинг (если вдруг кто-то пишет по-старому)
    if "async_fdb" in dsn: return dsn.replace("async_fdb", "fdb_async")
    if "async_pyfb" in dsn: return dsn.replace("async_pyfb", "firebirdsql_async")
    
    # Дефолт -> fdb_async
    if dsn.startswith("firebird://"):
        return dsn.replace("firebird://", "firebird+fdb_async://", 1)
        
    return dsn

def build_engine(dsn: str):
    # БОЛЬШЕ НЕТ РУЧНОЙ РЕГИСТРАЦИИ!
    # Если пакет установлен, create_async_engine сам найдет драйвер.
    return create_async_engine(
        dsn,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=50,
        pool_timeout=10,
        echo=False
    )

def build_raw_query(rows_limit: int | None) -> str:
    query = BASE_SQL_QUERY.strip()
    if rows_limit and rows_limit > 0:
        query = f"{query}\nROWS 1 TO {rows_limit}"
    return f"{query};"

async def run_worker(engine, worker_id: int, repeats: int, raw_query: str):
    results = []
    # Важный момент: ловим ошибки подключения, чтобы понять, работает ли драйвер
    try:
        async with engine.connect() as connection:
            worker_start = time.perf_counter()
            for i in range(repeats):
                start = time.perf_counter()
                rows = await connection.run_sync(
                    lambda sync_conn: sync_conn.execute(text(raw_query)).fetchall()
                )
                duration = time.perf_counter() - start
                row_count = len(rows)
                results.append((duration, row_count))
                print(f"[worker {worker_id}] rows={row_count} time={duration:.2f}s")
    except Exception as e:
        print(f"[worker {worker_id}] CRASHED: {e}")
        raise e
    return results

def build_orm_query(rows_limit: int | None):
    query = (
        select(
            Transactions.uuid.label("trans_uuid"),
            Transactions.hash.label("trans_hash"),
            Transactions.body.label("trans_body"),
            Signatures.signature_xdr,
        )
        .select_from(Transactions)
        .outerjoin(Signatures, Signatures.add_dt >= Transactions.add_dt)
        .order_by(Signatures.add_dt.asc())
    )
    if rows_limit and rows_limit > 0:
        query = query.limit(rows_limit)
    return query

async def run_worker_orm(session_maker, worker_id: int, repeats: int, orm_query):
    results = []
    async with session_maker() as session:
        for i in range(repeats):
            start = time.perf_counter()
            rows = await session.run_sync(lambda s: s.execute(orm_query).fetchall())
            duration = time.perf_counter() - start
            results.append((duration, len(rows)))
            print(f"[orm {worker_id}] rows={len(rows)} time={duration:.2f}s")
    return results

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--orm-threads", type=int, default=1)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--rows", type=int, default=100)
    # Можно передать просто строку подключения, скрипт сам подставит драйверы
    parser.add_argument("--dsn", type=str, default="firebird://SYSDBA:sysdba@127.0.0.1///db/eurmtl.fdb")
    return parser.parse_args()

async def run_test(args):
    # Тестируем оба драйвера по очереди
    drivers_to_test = [
        ("fdb_async", "Legacy FDB (Threaded)"),
        ("firebirdsql_async", "Native Async (firebirdsql)")
    ]

    for scheme, label in drivers_to_test:
        print("\n" + "="*60)
        print(f"🚀 TESTING DRIVER: {label}")
        print(f"   Scheme: firebird+{scheme}://...")
        
        target_dsn = build_async_dsn(args.dsn, target_scheme=scheme)
        print(f"   Full DSN: {target_dsn}")

        try:
            engine = build_engine(target_dsn)
            # Простая проверка соединения перед нагрузкой
            async with engine.connect() as conn:
                ver = await conn.scalar(text("SELECT rdb$get_context('SYSTEM','ENGINE_VERSION') from rdb$database"))
                print(f"   ✅ Connected! Engine Version: {ver}")
                print(f"   ✅ Dialect class: {engine.dialect.__class__}")
            
            # Если соединение ок, запускаем нагрузку
            session_maker = async_sessionmaker(engine, expire_on_commit=False)
            raw_query = build_raw_query(args.rows)
            orm_query = build_orm_query(args.rows)

            tasks = []
            if args.threads > 0:
                tasks += [run_worker(engine, i+1, args.repeat, raw_query) for i in range(args.threads)]
            if args.orm_threads > 0:
                tasks += [run_worker_orm(session_maker, i+1, args.repeat, orm_query) for i in range(args.orm_threads)]
            
            await asyncio.gather(*tasks)
            await engine.dispose()
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test(parse_args()))
