import asyncio
import asyncpg

async def list_databases():
    conn = None
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='postgres',
            host='localhost',
            port=5432,
            database='postgres'
        )
        rows = await conn.fetch('SELECT datname FROM pg_database')
        databases = [row['datname'] for row in rows]
        print('Existing databases:', databases)
        return databases
    except Exception as e:
        print('Error listing databases:', e)
        return []
    finally:
        if conn:
            await conn.close()

async def create_database(db_name):
    conn = None
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='postgres',
            host='localhost',
            port=5432,
            database='postgres'
        )
        await conn.execute(f'CREATE DATABASE {db_name}')
        print(f'Database {db_name} created.')
        return True
    except asyncpg.exceptions.DuplicateDatabaseError:
        print(f'Database {db_name} already exists.')
        return True
    except Exception as e:
        print(f'Error creating database {db_name}:', e)
        return False
    finally:
        if conn:
            await conn.close()

async def main():
    dbs = await list_databases()
    target_db = 'xpalermostat_db'
    if target_db not in dbs:
        print(f'Database {target_db} not found, creating...')
        success = await create_database(target_db)
        if not success:
            print('Failed to create database.')
            return
    else:
        print(f'Database {target_db} exists.')

if __name__ == '__main__':
    asyncio.run(main())