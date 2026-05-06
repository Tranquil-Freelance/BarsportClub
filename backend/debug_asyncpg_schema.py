"""
Debug: Check what asyncpg actually sees for substitutions table columns.
"""
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        user='postgres',
        password='your_secure_password',
        host='127.0.0.1',
        port=5432,
        database='xpalermostat_db'
    )
    
    # Check what asyncpg thinks the columns are
    attrs = await conn.fetch("""
        SELECT a.attname, a.attnum, t.typname
        FROM pg_class c
        JOIN pg_attribute a ON a.attrelid = c.oid
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE c.relname = 'substitutions'
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
    """)
    
    print("asyncpg sees these columns for substitutions:")
    for r in attrs:
        print(f"  {r['attname']} ({r['typname']})")
    
    # Try querying with different column names
    print("\nTrying different column names...")
    
    # With player_out
    try:
        rows = await conn.fetch("SELECT player_out, player_in, minute FROM substitutions LIMIT 3")
        print(f"  player_out works: {rows}")
    except Exception as e:
        print(f"  player_out fails: {e}")
    
    # With player_out_id
    try:
        rows = await conn.fetch("SELECT player_out_id, player_in_id, minute FROM substitutions LIMIT 3")
        print(f"  player_out_id works: {rows}")
    except Exception as e:
        print(f"  player_out_id fails: {e}")
    
    # With quoted player_out
    try:
        rows = await conn.fetch('SELECT "player_out", "player_in", "minute" FROM substitutions LIMIT 3')
        print(f"  quoted player_out works: {rows}")
    except Exception as e:
        print(f"  quoted player_out fails: {e}")
    
    await conn.close()

asyncio.run(test())
