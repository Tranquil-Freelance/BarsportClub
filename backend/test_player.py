import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import math

def offensive_impact(xg, xa, xgchain, shots):
    return 0.40 * xg + 0.30 * xa + 0.20 * xgchain + 0.10 * shots

def creative_influence(xa, key_passes, xgbuildup):
    return 0.50 * xa + 0.30 * key_passes + 0.20 * xgbuildup

def attacking_involvement(xgchain_total, minutes):
    return xgchain_total / max(minutes, 1.0)

def buildup_contribution(xgbuildup_total, minutes):
    return xgbuildup_total / max(minutes, 1.0)

def finishing_efficiency(goals, xg):
    if xg == 0:
        return 0.0
    return goals / xg

def player_impact(ois, cii, air, bcs, fes):
    return 0.30 * ois + 0.25 * cii + 0.20 * air + 0.15 * bcs + 0.10 * fes

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/xpalermostat')
    async with engine.connect() as conn:
        # get aggregated row for Keinan Davis
        res = await conn.execute(text("""
            SELECT player_name,
                MAX(team_name)                        AS team_name,
                MAX(position)                         AS position,
                COALESCE(SUM(goals::float),      0)   AS goals,
                COALESCE(SUM(npg::float),        0)   AS npg,
                COALESCE(SUM(shots::float),      0)   AS shots,
                COALESCE(SUM(assists::float),    0)   AS assists,
                COALESCE(SUM(key_passes::float), 0)   AS key_passes,
                COALESCE(SUM(xg::float),         0)   AS xg,
                COALESCE(SUM(npxg::float),       0)   AS npxg,
                COALESCE(SUM(xa::float),         0)   AS xa,
                COALESCE(SUM(xgchain::float),    0)   AS xgchain,
                COALESCE(SUM(xgbuildup::float),  0)   AS xgbuildup,
                COALESCE(SUM(time::float),       1)   AS minutes,
                COALESCE(SUM(games::int),        0)   AS games
            FROM master_europe_players
            WHERE player_name ILIKE '%Keinan Davis%'
            GROUP BY player_name
            ORDER BY MAX(season::int) DESC
            LIMIT 1
        """))
        row = res.fetchone()
        if not row:
            print('No row')
            return
        print('Row:', row)
        goals = float(row[3] or 0)
        npg = float(row[4] or 0)
        shots = float(row[5] or 0)
        assists = float(row[6] or 0)
        key_passes = float(row[7] or 0)
        xg = float(row[8] or 0)
        npxg = float(row[9] or 0)
        xa = float(row[10] or 0)
        xgchain = float(row[11] or 0)
        xgbuildup = float(row[12] or 0)
        minutes = float(row[13] or 1)
        games = int(row[14] or 0)
        
        f90 = 90.0 / max(minutes, 1.0)
        xg_p90 = xg * f90
        npxg_p90 = npxg * f90
        xa_p90 = xa * f90
        xgchain_p90 = xgchain * f90
        xgbuildup_p90 = xgbuildup * f90
        shots_p90 = shots * f90
        key_passes_p90 = key_passes * f90
        goals_p90 = goals * f90
        assists_p90 = assists * f90
        
        ois = offensive_impact(xg_p90, xa_p90, xgchain_p90, shots_p90)
        cii = creative_influence(xa_p90, key_passes_p90, xgbuildup_p90)
        air = attacking_involvement(xgchain, minutes)
        bcs = buildup_contribution(xgbuildup, minutes)
        fes = finishing_efficiency(goals, xg)
        pir = player_impact(ois, cii, air, bcs, fes)
        
        print('Metrics:', ois, cii, air, bcs, fes, pir)
        print('Minutes:', minutes)
        print('Goals:', goals)
        print('xg:', xg)
        
        # grade and archetype placeholder
        grade = 'B+'
        archetype = 'Forward'
        print('Grade:', grade, 'Archetype:', archetype)

if __name__ == '__main__':
    asyncio.run(test())