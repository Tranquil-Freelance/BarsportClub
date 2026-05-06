#!/usr/bin/env python3
"""
Comprehensive verification script for Backend-to-Database pipeline.
Tests that an article can be POSTed to the FastAPI backend and persists in PostgreSQL.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# Load environment variables from backend/.env
_load_dotenv = None
_has_dotenv = False
try:
    from dotenv import load_dotenv as _load_dotenv_fn
    _load_dotenv = _load_dotenv_fn
    _has_dotenv = True
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

if not _has_dotenv:
    logger.warning("python-dotenv not installed, using simple .env parser.")


def _parse_env_file(path: str) -> Dict[str, str]:
    """Simple parser for KEY=VALUE lines in .env file."""
    env = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def load_env() -> Dict[str, str]:
    """Load PostgreSQL credentials from backend/.env file."""
    env_path = os.path.join("backend", ".env")
    if not os.path.exists(env_path):
        logger.error(f"Environment file not found: {env_path}")
        sys.exit(1)

    if _has_dotenv:
        _load_dotenv(env_path, override=True)
        # Read from os.environ
        env = {}
    else:
        env = _parse_env_file(env_path)
        # Inject into os.environ for compatibility
        for k, v in env.items():
            os.environ.setdefault(k, v)

    required_vars = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_SERVER",
        "POSTGRES_DB",
    ]
    env_dict = {}
    missing = []
    for var in required_vars:
        value = env.get(var) if not _has_dotenv else os.getenv(var)
        if value is None:
            missing.append(var)
        else:
            env_dict[var] = value

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Optional port, default to 5432
    port = env.get("POSTGRES_PORT") if not _has_dotenv else os.getenv("POSTGRES_PORT")
    env_dict["POSTGRES_PORT"] = port if port else "5432"
    logger.info("Environment variables loaded successfully.")
    return env_dict


def test_http_post() -> Optional[int]:
    """Send a POST request to the backend articles endpoint.
    
    Returns:
        HTTP status code if request succeeded, None otherwise.
    """
    try:
        import requests
    except ImportError:
        logger.error("requests module not installed. Install with: pip install requests")
        return None

    url = "http://127.0.0.1:8000/api/admin/articles"
    payload = {
        "title": "Test Connection",
        "author": "System",
        "content": "Checking if the pipeline is open.",
        "match_id": None,
        "is_featured": False,
    }
    headers = {"Content-Type": "application/json"}

    try:
        logger.info(f"Sending POST to {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info(f"HTTP status code: {response.status_code}")
        if response.status_code == 200:
            logger.info("POST succeeded.")
            try:
                data = response.json()
                logger.info(f"Response: {data}")
                return response.status_code
            except Exception as e:
                logger.warning(f"Could not parse JSON response: {e}")
        else:
            logger.error(f"POST failed with status {response.status_code}")
            logger.error(f"Response text: {response.text}")
        return response.status_code
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to backend. Is the FastAPI server running?")
        return None
    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during HTTP request: {e}")
        return None


def verify_database(env: Dict[str, str]) -> bool:
    """Connect to PostgreSQL and verify the article was stored.
    
    Args:
        env: Dictionary containing POSTGRES_* credentials.
    
    Returns:
        True if article found, False otherwise.
    """
    # Try psycopg2 first (fastest)
    try:
        import psycopg2
        from psycopg2.extras import DictCursor
        logger.debug("Using psycopg2 for database connection.")
        return _verify_via_psycopg2(env, psycopg2, DictCursor)
    except ImportError:
        logger.warning("psycopg2 not installed, falling back to SQLAlchemy.")
    
    # Fallback to SQLAlchemy sync engine
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        logger.debug("Using SQLAlchemy sync engine.")
        return _verify_via_sqlalchemy(env, create_engine, text, SQLAlchemyError)
    except ImportError:
        logger.error("Neither psycopg2 nor SQLAlchemy are installed.")
        logger.error("Install with: pip install psycopg2-binary sqlalchemy")
        return False


def _verify_via_psycopg2(env: Dict[str, str], psycopg2, DictCursor) -> bool:
    """Verify using psycopg2."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=env["POSTGRES_SERVER"],
            port=env["POSTGRES_PORT"],
            database=env["POSTGRES_DB"],
            user=env["POSTGRES_USER"],
            password=env["POSTGRES_PASSWORD"],
        )
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            "SELECT id, title, author FROM articles WHERE title = %s;",
            ("Test Connection",)
        )
        row = cur.fetchone()
        if row:
            logger.info(f"SUCCESS: Data persisted in PostgreSQL. Record ID: {row['id']}")
            logger.info(f"Title: {row['title']}, Author: {row['author']}")
            return True
        else:
            logger.error("FAILURE: Request sent but database is empty.")
            return False
    except psycopg2.OperationalError as e:
        logger.error(f"Cannot connect to PostgreSQL: {e}")
        return False
    except Exception as e:
        logger.error(f"Database verification error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def _verify_via_sqlalchemy(env: Dict[str, str], create_engine, text, SQLAlchemyError) -> bool:
    """Verify using SQLAlchemy sync engine."""
    # Build sync connection URL (without async driver)
    sync_url = (
        f"postgresql://{env['POSTGRES_USER']}:{env['POSTGRES_PASSWORD']}"
        f"@{env['POSTGRES_SERVER']}:{env['POSTGRES_PORT']}/{env['POSTGRES_DB']}"
    )
    engine = None
    try:
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, author FROM articles WHERE title = :title"),
                {"title": "Test Connection"}
            )
            row = result.fetchone()
            if row:
                logger.info(f"SUCCESS: Data persisted in PostgreSQL. Record ID: {row.id}")
                logger.info(f"Title: {row.title}, Author: {row.author}")
                return True
            else:
                logger.error("FAILURE: Request sent but database is empty.")
                return False
    except SQLAlchemyError as e:
        logger.error(f"Cannot connect to PostgreSQL via SQLAlchemy: {e}")
        return False
    except Exception as e:
        logger.error(f"Database verification error: {e}")
        return False
    finally:
        if engine:
            engine.dispose()


def main() -> None:
    """Orchestrate the verification pipeline."""
    logger.info("=== Starting Backend-to-Database Pipeline Verification ===")
    
    # 1. Load environment
    env = load_env()
    
    # 2. HTTP test
    logger.info("--- Step 1: HTTP POST to backend ---")
    status = test_http_post()
    if status is None or status != 200:
        logger.error("HTTP test failed. Aborting database verification.")
        sys.exit(1)
    
    # 3. Database verification
    logger.info("--- Step 2: Database verification ---")
    success = verify_database(env)
    if success:
        logger.info("=== VERIFICATION PASSED ===")
        sys.exit(0)
    else:
        logger.error("=== VERIFICATION FAILED ===")
        sys.exit(1)


if __name__ == "__main__":
    main()