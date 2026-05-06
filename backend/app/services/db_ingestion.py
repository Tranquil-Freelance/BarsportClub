import logging
from typing import Optional
import pandas as pd
import numpy as np
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

# Importiamo i modelli esatti dal tuo file models.py
from app.db.models import League, Team, Match, Shot, PlayerStat

logger = logging.getLogger(__name__)

UNDERSTAT_SLUG_TO_NAME = {
    "Serie_A": "Serie A",
    "EPL": "Premier League",
    "La_Liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Ligue_1": "Ligue 1",
}

async def upsert_league(session: AsyncSession, league_id: int, name: str, understat_slug: str) -> None:
    stmt = insert(League).values(id=league_id, name=name, understat_slug=understat_slug)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={"name": stmt.excluded.name, "understat_slug": stmt.excluded.understat_slug}
    )
    await session.execute(stmt)
    await session.commit()

async def upsert_teams(session: AsyncSession, df: pd.DataFrame, league_id: int) -> None:
    if df.empty: return
    # Rimuoviamo colonne duplicate all'origine
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    home = df[["home_team_id", "home_team_name"]].rename(columns={"home_team_id": "id", "home_team_name": "name"})
    away = df[["away_team_id", "away_team_name"]].rename(columns={"away_team_id": "id", "away_team_name": "name"})
    teams_df = pd.concat([home, away]).dropna(subset=["id"]).drop_duplicates(subset=["id"])
    teams_df["id"] = teams_df["id"].astype(int)
    teams_df["league_id"] = league_id
    records = teams_df.to_dict(orient="records")
    
    stmt = insert(Team).values(records)
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_={"name": stmt.excluded.name, "league_id": stmt.excluded.league_id})
    await session.execute(stmt)
    await session.commit()

async def upsert_match_calendar(session: AsyncSession, df: pd.DataFrame, league_id: int) -> None:
    if df.empty: return
    # Rimuoviamo colonne duplicate
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    match_df = df.copy()
    if "datetime" in match_df.columns:
        match_df.rename(columns={"datetime": "match_datetime"}, inplace=True)
    match_df["match_datetime"] = pd.to_datetime(match_df["match_datetime"]).dt.tz_localize(None)
    match_df["league_id"] = league_id
    
    valid_cols = [c.name for c in Match.__table__.columns]
    records = [{k: v for k, v in r.items() if k in valid_cols} for r in match_df.to_dict(orient="records")]

    stmt = insert(Match).values(records)
    update_cols = {c.name: getattr(stmt.excluded, c.name) for c in Match.__table__.columns if c.name != 'id'}
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
    await session.execute(stmt)
    await session.commit()

async def upsert_shots(session: AsyncSession, df: pd.DataFrame) -> None:
    if df.empty: return
    # PULIZIA DUPLICATI
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    mapping = {
        "h_a": "team_type", "player_assisted": "assist", 
        "shotType": "shotType", "situation": "situation",
        "lastAction": "lastAction", "player_id": "player_id"
    }
    df_clean = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    valid_columns = [c.name for c in Shot.__table__.columns]
    
    records = []
    for _, row in df_clean.iterrows():
        record = {}
        for col in valid_columns:
            if col in df_clean.columns:
                val = row[col]
                # Controllo nullo a prova di Series ambigue
                is_null = pd.isna(val) if isinstance(val, (float, int, str, type(None))) else False
                
                if col in ['id', 'match_id', 'minute', 'player_id']:
                    record[col] = int(val) if not is_null else None
                elif col in ['xG', 'X', 'Y']:
                    record[col] = float(val) if not is_null else 0.0
                else:
                    record[col] = str(val) if not is_null else None
        if record.get("id"): records.append(record)

    if not records: return
    logger.info(f"🚀 Iniezione Chirurgica: {len(records)} tiri.")
    stmt = insert(Shot).values(records)
    update_dict = {c.name: getattr(stmt.excluded, c.name) for c in Shot.__table__.columns if c.name != 'id'}
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_dict)
    await session.execute(stmt)
    await session.commit()

async def upsert_player_match_stats(session: AsyncSession, df: pd.DataFrame) -> None:
    if df.empty: return
    # PULIZIA DUPLICATI
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    # Mapping Understat -> Tuo Modello
    mapping = {
        "player": "player_name", 
        "h_a": "team_type", 
        "team_id": "team_name",
        "key_passes": "key_passes",
        "yellow_card": "yellow_cards",
        "red_card": "red_cards"
    }
    df_clean = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    valid_columns = [c.name for c in PlayerStat.__table__.columns if c.name != 'id']
    
    records = []
    for _, row in df_clean.iterrows():
        record = {}
        for col in valid_columns:
            if col in df_clean.columns:
                val = row[col]
                # Controllo nullo corretto per evitare l'errore Ambiguous Truth Value
                is_null = pd.isna(val) if not isinstance(val, pd.Series) else pd.isna(val).all()
                
                if col in ['match_id', 'player_id', 'time', 'goals', 'assists', 'shots', 'yellow_cards', 'red_cards', 'key_passes']:
                    record[col] = int(val) if not is_null else 0
                elif col in ['xG', 'npxG', 'xA', 'xGChain', 'xGBuildup']:
                    record[col] = float(val) if not is_null else 0.0
                else:
                    record[col] = str(val) if not is_null else None
        records.append(record)

    stmt = insert(PlayerStat).values(records)
    # Vincolo unico: match_id + player_id
    update_cols = {c.name: getattr(stmt.excluded, c.name) for c in PlayerStat.__table__.columns if c.name not in ['id', 'match_id', 'player_id']}
    stmt = stmt.on_conflict_do_update(index_elements=["match_id", "player_id"], set_=update_cols)
    await session.execute(stmt)
    await session.commit()