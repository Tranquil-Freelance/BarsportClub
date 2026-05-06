import os
import pandas as pd
from fastapi import APIRouter
from dotenv import load_dotenv
from sqlalchemy import text

from app.db.database import engine

load_dotenv()

router = APIRouter()


@router.get("/replacement/{player_name}")
async def get_clones(player_name: str):
    try:
        async with engine.connect() as conn:
            query = text("""
                SELECT
                    player,
                    MAX(position) as position,
                    SUM("xG") as xg,
                    SUM("xA") as xa,
                    SUM("xGChain") as xgchain,
                    SUM("xGBuildup") as xgbuildup
                FROM rosters
                GROUP BY player
            """)
            res = await conn.execute(query)
            rows = res.mappings().all()

            if not rows:
                return {"error": "Tabella rosters vuota."}

        df = pd.DataFrame(rows)
        features = ['xg', 'xa', 'xgchain', 'xgbuildup']
        df[features] = df[features].apply(pd.to_numeric).fillna(0)
        df['player'] = df['player'].astype(str).str.strip()

        for f in features:
            df[f'p_{f}'] = df[f].rank(pct=True) * 100

        target = df[df['player'].str.lower().str.contains(player_name.lower(), na=False)]

        if target.empty:
            return {"error": f"Giocatore '{player_name}' non trovato."}

        p_cols = [f'p_{f}' for f in features]
        target_vec = target[p_cols].iloc[0]
        sim = df[p_cols].corrwith(target_vec, axis=1)
        df['similarity_score'] = ((sim + 1) / 2) * 100

        target_name = target['player'].iloc[0]
        clones = (df[df['player'] != target_name]
                  .sort_values(by='similarity_score', ascending=False)
                  .head(5))

        return clones.to_dict(orient='records')

    except Exception as e:
        return {"error": str(e)}
