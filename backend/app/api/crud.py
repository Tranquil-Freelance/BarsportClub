"""
CRUD operations for Editorial CMS (Articles).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
import re
import math
import traceback

def sanitize_float(val):
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    return val

from typing import List, Optional

from app.db.models import Article, Match, Shot
from app.models.football import TeamSeasonStat, Team, MatchCalendar


def clean_int(value):
    """
    Convert a value to integer, handling strings like "45+2" (sums the parts).
    
    Parameters
    ----------
    value : Any
        Input value (int, float, str, None).
    
    Returns
    -------
    int
        Integer representation.
    
    Raises
    ------
    ValueError
        If the value cannot be converted to integer.
    """
    if value is None:
        raise ValueError("Cannot convert None to integer")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        # Remove whitespace
        s = value.strip()
        # Handle format "45+2"
        if '+' in s:
            parts = s.split('+')
            total = 0
            for part in parts:
                if part:
                    total += int(part)
            return total
        # Try direct conversion
        try:
            return int(s)
        except ValueError:
            # Try float first
            try:
                return int(float(s))
            except ValueError:
                raise ValueError(f"Invalid integer value: {value!r}")
    # For any other type, try conversion via int
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Cannot convert {type(value).__name__} to integer: {value!r}")


def clean_float(value):
    """
    Convert a value to float, handling strings and None.
    
    Parameters
    ----------
    value : Any
        Input value (int, float, str, None).
    
    Returns
    -------
    float
        Float representation. If value is None, returns 0.0.
    
    Raises
    ------
    ValueError
        If the value cannot be converted to float.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        s = value.strip()
        if not s:
            return 0.0
        try:
            result = float(s)
        except ValueError:
            raise ValueError(f"Invalid float value: {value!r}")
    else:
        try:
            result = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Cannot convert {type(value).__name__} to float: {value!r}")
    if math.isnan(result) or math.isinf(result):
        return 0.0
    return result


def slugify(text: str) -> str:
    """
    Convert a string into a URL‑friendly slug.
    """
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[\s_-]+', '-', slug)  # Replace spaces/hyphens with single hyphen
    slug = re.sub(r'^-+|-+$', '', slug)   # Trim hyphens from start/end
    return slug


async def create_article(
    db: AsyncSession,
    title: str,
    author: str,
    content: str,
    hero_image: Optional[str] = None,
    category: Optional[str] = None,
    league: Optional[str] = None,
    team: Optional[str] = None,
    is_featured: bool = False,
    match_id: Optional[int] = None,
) -> Article:
    """
    Create a new article with auto‑generated slug.
    """
    # Generate slug from title
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(
            select(Article).where(Article.slug == slug)
        )
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    article = Article(
        slug=slug,
        title=title,
        author=author,
        content=content,
        hero_image=hero_image,
        category=category,
        league=league,
        team=team,
        is_featured=is_featured,
        match_id=match_id,
    )
    db.add(article)
    try:
        await db.commit()
        await db.refresh(article)
    except IntegrityError as e:
        await db.rollback()
        raise e
    return article


async def get_article_by_slug(db: AsyncSession, slug: str) -> Optional[Article]:
    """
    Retrieve a single article by its slug.
    """
    result = await db.execute(
        select(Article).where(Article.slug == slug)
    )
    return result.scalar_one_or_none()


async def get_articles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    order_by: str = "created_at_desc",
    league: Optional[str] = None,
    category: Optional[str] = None,
    team: Optional[str] = None,
    is_featured: Optional[bool] = None,
) -> List[Article]:
    """
    Retrieve a list of articles with pagination and ordering, optionally filtered.
    """
    stmt = select(Article)
    
    if league:
        stmt = stmt.where(Article.league == league)
    if category:
        stmt = stmt.where(Article.category == category)
    if team:
        stmt = stmt.where(Article.team == team)
    if is_featured is not None:
        stmt = stmt.where(Article.is_featured == is_featured)
    
    if order_by == "created_at_desc":
        stmt = stmt.order_by(Article.created_at.desc())
    elif order_by == "created_at_asc":
        stmt = stmt.order_by(Article.created_at.asc())
    elif order_by == "title_asc":
        stmt = stmt.order_by(Article.title.asc())
    elif order_by == "title_desc":
        stmt = stmt.order_by(Article.title.desc())
    else:
        stmt = stmt.order_by(Article.created_at.desc())
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_article(
    db: AsyncSession,
    slug: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    content: Optional[str] = None,
    hero_image: Optional[str] = None,
    category: Optional[str] = None,
    league: Optional[str] = None,
    team: Optional[str] = None,
    is_featured: Optional[bool] = None,
    match_id: Optional[int] = None,
) -> Optional[Article]:
    """
    Update an existing article.
    """
    article = await get_article_by_slug(db, slug)
    if not article:
        return None
    if title is not None:
        article.title = title
        # Optionally regenerate slug if title changed? For simplicity we keep same slug.
    if author is not None:
        article.author = author
    if content is not None:
        article.content = content
    if hero_image is not None:
        article.hero_image = hero_image
    if category is not None:
        article.category = category
    if league is not None:
        article.league = league
    if team is not None:
        article.team = team
    if is_featured is not None:
        article.is_featured = is_featured
    if match_id is not None:
        article.match_id = match_id
    await db.commit()
    await db.refresh(article)
    return article


async def delete_article(db: AsyncSession, slug: str) -> bool:
    """
    Delete an article by slug.
    """
    article = await get_article_by_slug(db, slug)
    if not article:
        return False
    await db.delete(article)
    await db.commit()
    return True


async def get_featured_articles(db: AsyncSession, limit: int = 5) -> List[Article]:
    """
    Retrieve featured articles for homepage hero section.
    """
    stmt = (
        select(Article)
        .where(Article.is_featured == True)
        .order_by(Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def save_match_shots(
    db: AsyncSession,
    match_id: int,
    home_team: str,
    away_team: str,
    shots_data: dict,
) -> None:
    """
    Save shot data for a given match.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    match_id : int
        Understat match identifier.
    home_team : str
        Home team name.
    away_team : str
        Away team name.
    shots_data : dict
        Dictionary with keys 'h' and 'a', each containing a list of shot dicts.
        Each shot dict must have keys:
            'minute', 'player', 'xG', 'result', 'X', 'Y'
        Optional keys: 'situation', 'shotType', 'assist'
        (team_type is derived from the parent key 'h' or 'a').

    Raises
    ------
    ValueError
        If shots_data does not contain both 'h' and 'a' keys.
    """
    if "h" not in shots_data or "a" not in shots_data:
        raise ValueError("shots_data must contain 'h' and 'a' keys")

    # Clean match ID (ensure it's an integer)
    clean_match_id = clean_int(match_id)

    # Upsert match record
    match = await db.get(Match, clean_match_id)
    if match is None:
        match = Match(id=clean_match_id, home_team=home_team, away_team=away_team)
        db.add(match)
    else:
        match.home_team = home_team
        match.away_team = away_team

    # Prepare shot records for bulk upsert
    shot_records = []
    for team_type, shot_list in (("h", shots_data["h"]), ("a", shots_data["a"])):
        for shot_dict in shot_list:
            record = {
                "match_id": clean_match_id,
                "minute": clean_int(shot_dict["minute"]),
                "player": shot_dict["player"],
                "xG": clean_float(shot_dict["xG"]),
                "result": shot_dict["result"],
                "team_type": team_type,
                "X": clean_float(shot_dict["X"]),
                "Y": clean_float(shot_dict["Y"]),
                "situation": shot_dict.get("situation"),
                "shotType": shot_dict.get("shotType"),
                "assist": shot_dict.get("assist"),
            }
            # Forza NaN/Inf a 0.0 (sicurezza aggiuntiva)
            for key in ("xG", "X", "Y"):
                if math.isnan(record[key]) or math.isinf(record[key]):
                    record[key] = 0.0
            shot_records.append(record)

    # Bulk upsert using PostgreSQL ON CONFLICT DO UPDATE
    if shot_records:
        stmt = insert(Shot).values(shot_records)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_shot_unique",
            set_={
                "xG": stmt.excluded.xG,
                "result": stmt.excluded.result,
                "X": stmt.excluded.X,
                "Y": stmt.excluded.Y,
                "situation": stmt.excluded.situation,
                "shotType": stmt.excluded.shotType,
                "assist": stmt.excluded.assist,
                # Note: match_id, minute, player, team_type are part of the constraint
                # and are not updated.
            }
        )
        await db.execute(stmt)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise e


async def get_match_shots(db: AsyncSession, match_id: int) -> dict:
    """
    Retrieve shot data for a match, formatted with match metadata and shots.

    Parameters
    ----------
    db : AsyncSession
        Database session.
    match_id : int
        Understat match identifier.

    Returns
    -------
    dict
        Dictionary with keys:
            'match': {'home_team': str, 'away_team': str},
            'shots': {'h': list, 'a': list}
        The shot dicts have the same fields as stored (minute, player, xG, result, X, Y, situation, shotType, assist).

    Raises
    ------
    ValueError
        If no match with the given ID exists in the database.
    """
    # Verify match exists
    clean_match_id = clean_int(match_id)
    match = await db.get(Match, clean_match_id)
    if match is None:
        raise ValueError(f"Match {clean_match_id} not found in database")

    # Query shots for this match, ordered by team_type and minute
    stmt = select(Shot).where(Shot.match_id == clean_match_id).order_by(Shot.team_type, Shot.minute)
    result = await db.execute(stmt)
    shots = result.scalars().all()

    # Group by team_type
    grouped = {"h": [], "a": []}
    for shot in shots:
        shot_dict = {
            "minute": shot.minute,
            "player": shot.player,
            "xG": sanitize_float(shot.xG),
            "result": shot.result,
            "X": sanitize_float(shot.X),
            "Y": sanitize_float(shot.Y),
            "situation": shot.situation,
            "shotType": shot.shotType,
            "assist": shot.assist,
        }
        grouped[shot.team_type].append(shot_dict)

    return {
        "match": {
            "home_team": match.home_team,
            "away_team": match.away_team,
        },
        "shots": grouped,
    }


async def get_matches(db: AsyncSession, round_number: Optional[int] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[dict]:
    """
    Retrieve matches from MatchCalendar with optional round filter, pagination, and limit.
    Returns a list of dicts with keys: id, date, home_team, away_team,
    home_score, away_score, home_xg, away_xg, round.
    """
    from sqlalchemy.orm import selectinload
    import logging

    logger = logging.getLogger(__name__)

    stmt = select(MatchCalendar).options(
        selectinload(MatchCalendar.home_team),
        selectinload(MatchCalendar.away_team)
    ).order_by(MatchCalendar.match_datetime.desc())

    if round_number is not None:
        stmt = stmt.where(MatchCalendar.round == round_number)

    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)

    result = await db.execute(stmt)
    matches = result.scalars().all()

    matches_list = []
    for match in matches:
        try:
            matches_list.append({
                "id": match.id,
                "date": match.match_datetime.isoformat() if match.match_datetime else None,
                "home_team": match.home_team.name if match.home_team else None,
                "away_team": match.away_team.name if match.away_team else None,
                "home_score": match.home_goals,
                "away_score": match.away_goals,
                "home_xg": sanitize_float(match.home_xG),
                "away_xg": sanitize_float(match.away_xG),
                "round": match.round,
            })
        except Exception as e:
            logger.warning("Skipping match %d due to processing error: %s", match.id, e, exc_info=True)
            continue
    return matches_list


async def get_standings(db: AsyncSession):
    """
    Retrieve standings from TeamSeasonStat for the most recent season,
    ordered by points descending.
    Returns a list of dicts with keys: pos, name, season, matches, wins, draws, losses,
    goals_for, goals_against, pts, gd, xg, xga, xpts, ppda, isComo, xg_diff, xga_diff, xpts_diff.
    """
    from sqlalchemy import select, desc, func

    # Determine the most recent season available
    subq = select(func.max(TeamSeasonStat.season)).scalar_subquery()
    # Use subquery in filter
    stmt = (
        select(TeamSeasonStat, Team)
        .join(Team, TeamSeasonStat.team_id == Team.id)
        .where(TeamSeasonStat.season == subq)
        .order_by(desc(TeamSeasonStat.points))
    )

    result = await db.execute(stmt)
    rows = result.all()

    standings = []
    for idx, (stat, team) in enumerate(rows, start=1):
        gd = stat.goals_for - stat.goals_against
        gd_str = f"+{gd}" if gd > 0 else str(gd)

        # Extract advanced metrics with defensive fallback
        xg = getattr(stat, 'xG_for', 0.0)
        xga = getattr(stat, 'xG_against', 0.0)
        xpts = getattr(stat, 'xpts', 0.0)  # column now present
        ppda = getattr(stat, 'ppda', 0.0)

        # Convert None to 0.0
        if xg is None:
            xg = 0.0
        if xga is None:
            xga = 0.0
        if xpts is None:
            xpts = 0.0
        if ppda is None:
            ppda = 0.0

        # Safe casting to float and rounding
        xg = round(float(xg), 2)
        xga = round(float(xga), 2)
        xpts = round(float(xpts), 2)
        ppda = round(float(ppda), 2)

        # Points also rounded (though integer)
        pts = round(float(stat.points), 2) if stat.points is not None else 0.0

        # Compute deltas
        xg_diff = round(float(xg - stat.goals_for), 2)
        xga_diff = round(float(xga - stat.goals_against), 2)
        xpts_diff = round(float(xpts - stat.points), 2)

        standings.append({
            "pos": idx,
            "name": team.name,
            "season": stat.season,
            "matches": stat.matches_played,
            "wins": stat.wins,
            "draws": stat.draws,
            "losses": stat.losses,
            "goals_for": stat.goals_for,
            "goals_against": stat.goals_against,
            "pts": pts,
            "gd": gd_str,
            "xg": xg,
            "xga": xga,
            "xpts": xpts,
            "ppda": ppda,
            "xg_diff": xg_diff,
            "xga_diff": xga_diff,
            "xpts_diff": xpts_diff,
            "isComo": team.name == "Como"
        })

    return standings
