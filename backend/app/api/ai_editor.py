"""
AI Editor module for x-ComoStat.
Generates match reports using LLMs (OpenAI/Gemini) with a cynical ex‑player tone.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

# -------------------- Configuration --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# -------------------- Prompt Templates --------------------
SYSTEM_PROMPT = (
    "Sei un ex calciatore di Serie A, cinico, che ha studiato a Coverciano. "
    "Commenti la partita in un bar ma con competenza tecnica assoluta. "
    "Non usare frasi fatte da IA, sii pungente, parla di PPDA e xG come se fossero pane quotidiano."
)

USER_PROMPT_TEMPLATE = """
Analizza la partita di calcio con i seguenti dati:

**DATI PARTITA**
- Data: {date}
- Squadra casa: {home_team} ({home_score} goal, {home_xg:.2f} xG, {home_possession:.1f}% possesso)
- Squadra ospite: {away_team} ({away_score} goal, {away_xg:.2f} xG, {away_possession:.1f}% possesso)
- PPDA: {ppda:.2f}

**TIRO SIGNIFICATIVI** (giocatore – minuto – xG – risultato)
{shots_text}

**ISTRUZIONI**
1. tactical_analysis: un paragrafo tecnico sul dominio del campo, pressione, transizioni, qualità delle occasioni.
2. top_flop: giudizi secchi sui protagonisti (massimo 3 giocatori), uno positivo e uno negativo per squadra se possibile.
3. headline: un titolo urlato in stile giornale sportivo (max 10 parole).

Rispondi ESCLUSIVAMENTE con un JSON valido contenente le tre chiavi:
{{
  "tactical_analysis": "...",
  "top_flop": "...",
  "headline": "..."
}}
"""

# -------------------- Helper Functions --------------------
def _format_shots(shots_data: List[Dict[str, Any]]) -> str:
    """Convert shots list into a readable text."""
    lines = []
    for i, shot in enumerate(shots_data[:10], 1):  # limit to 10 most relevant shots
        player = shot.get("player_name", "Sconosciuto")
        minute = shot.get("minute", "?")
        xg = shot.get("xg", 0.0)
        is_goal = shot.get("is_goal", False)
        team = "Casa" if shot.get("is_home_team", False) else "Ospite"
        outcome = "GOL" if is_goal else "NO‑GOL"
        lines.append(f"{i}. {player} ({team}) – min {minute} – xG {xg:.3f} – {outcome}")
    if len(shots_data) > 10:
        lines.append(f"... e altri {len(shots_data) - 10} tiri.")
    return "\n".join(lines)


def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI API and return the response text."""
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI library not installed.")
        return None
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable not set.")
        return None
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.exception("OpenAI API call failed: %s", e)
        return None


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API and return the response text."""
    if not GEMINI_AVAILABLE:
        logger.error("Gemini library not installed.")
        return None
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable not set.")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.exception("Gemini API call failed: %s", e)
        return None


# -------------------- Main Public Function --------------------
def generate_match_report(
    match_data: Dict[str, Any],
    shots_data: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Generate a cynical match report using an LLM.

    Parameters
    ----------
    match_data : dict
        Must contain keys:
            date (str), home_team (str), away_team (str),
            home_score (int), away_score (int),
            home_xg (float), away_xg (float),
            home_possession (float), away_possession (float),
            ppda (float or None)
    shots_data : list of dict
        Each dict must contain keys:
            player_name (str), minute (int), xg (float),
            is_home_team (bool), is_goal (bool)

    Returns
    -------
    dict with keys:
        tactical_analysis (str),
        top_flop (str),
        headline (str)
    """
    # Format shots
    shots_text = _format_shots(shots_data)

    # Build user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        date=match_data.get("date", "N/D"),
        home_team=match_data.get("home_team", "Squadra Casa"),
        away_team=match_data.get("away_team", "Squadra Ospite"),
        home_score=match_data.get("home_score", 0),
        away_score=match_data.get("away_score", 0),
        home_xg=match_data.get("home_xg", 0.0),
        away_xg=match_data.get("away_xg", 0.0),
        home_possession=match_data.get("home_possession", 50.0),
        away_possession=match_data.get("away_possession", 50.0),
        ppda=match_data.get("ppda", 0.0),
        shots_text=shots_text,
    )

    # Try OpenAI first, then Gemini, fallback to mock
    response_text = None
    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        logger.info("Using OpenAI...")
        response_text = _call_openai(user_prompt)
    elif GEMINI_AVAILABLE and GEMINI_API_KEY:
        logger.info("Using Gemini...")
        response_text = _call_gemini(user_prompt)
    else:
        logger.warning("No LLM provider configured. Returning mock response.")

    # Parse JSON response
    if response_text:
        try:
            # Remove possible markdown code blocks
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            parsed = json.loads(clean_text)
            # Ensure required keys exist
            if all(k in parsed for k in ("tactical_analysis", "top_flop", "headline")):
                return parsed
            else:
                logger.error("LLM response missing required keys.")
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse LLM response as JSON: %s", e)

    # Fallback mock response (for development / testing)
    return {
        "tactical_analysis": (
            "La partita è stata decisa da una transizione rapida dopo un PPDA alle stelle. "
            "La squadra di casa ha sofferto il pressing alto e ha prodotto xG solo da fuori area."
        ),
        "top_flop": (
            "TOP: Rossi (Casa) – ha smistato come un metronomo. "
            "FLOP: Bianchi (Ospite) – lento e sempre in ritardo sugli inserimenti."
        ),
        "headline": "ROSSI STENDE I NEMICI CON UN XG DA URLO, PPDA ALLE STELLE!"
    }


if __name__ == "__main__":
    # Example usage / quick test
    sample_match = {
        "date": "2024-03-10",
        "home_team": "Como",
        "away_team": "Palermo",
        "home_score": 2,
        "away_score": 1,
        "home_xg": 2.1,
        "away_xg": 0.8,
        "home_possession": 58.3,
        "away_possession": 41.7,
        "ppda": 12.5,
    }
    sample_shots = [
        {
            "player_name": "Rossi",
            "minute": 23,
            "xg": 0.45,
            "is_home_team": True,
            "is_goal": True,
        },
        {
            "player_name": "Bianchi",
            "minute": 67,
            "xg": 0.12,
            "is_home_team": False,
            "is_goal": False,
        },
    ]
    report = generate_match_report(sample_match, sample_shots)
    print(json.dumps(report, indent=2, ensure_ascii=False))