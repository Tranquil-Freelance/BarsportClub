import os
import json
import logging
from typing import Dict, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# -------------------- Configurazione DeepSeek/OpenAI --------------------
# Usa le chiavi che hai già a sistema per il betting
API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY"))
# Se usi DeepSeek nativo, scommenta la riga sotto nel tuo ambiente o settala via OS
# openai.api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1") 
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# -------------------- Prompt Ingegnerizzati --------------------
SYSTEM_PROMPT = """Sei l'analista algoritmico supremo di xPalermoStat. Il tuo unico credo è l'Indice di Merito Reale (IMR).
Il tabellino dei gol è pura cronaca (spesso bugiarda legata agli episodi), mentre l'IMR è la verità matematica della produzione offensiva e dell'assedio.
Usa un tono freddo, spietato, giornalistico, cinico e autorevole. Non usare mai frasi fatte, buonismi o ovvietà.
REGOLE D'INGAGGIO:
1. Se la squadra che ha perso sul campo ha un IMR superiore di oltre 5 punti, DEVI denunciare il risultato come ingiusto. Spiega che ha dominato il gioco e ha perso solo per mancanza di cinismo o episodi avversi.
2. Se chi vince ha anche l'IMR più alto, esalta la sua superiorità totale (sia nel gioco che nel punteggio).
3. Se è un pareggio ma l'IMR pende drasticamente da una parte, parla di pareggio bugiardo e di dominio non capitalizzato.
4. Sii breve e letale (massimo 3-4 frasi)."""

USER_PROMPT_TEMPLATE = """
Analizza questo match ed emetti la tua sentenza definitiva.

**DATI REALI (Cronaca)**
Partita: {home_team} {home_score} - {away_score} {away_team}
Expected Goals (xG): {home_team} {home_xg:.2f} | {away_team} {away_xg:.2f}

**INDICE DI MERITO REALE (La Verità del Campo)**
Punti IMR {home_team}: {home_imr}
Punti IMR {away_team}: {away_imr}

Rispondi ESCLUSIVAMENTE con un JSON valido con questa esatta struttura, senza markdown aggiuntivi:
{{
  "ai_verdict": "Il tuo commento tagliente e spietato qui."
}}
"""

def generate_imr_verdict(match_data: Dict[str, Any]) -> str:
    """
    Chiama l'LLM (DeepSeek) per generare la sentenza sul Meritometro.
    Ritorna solo la stringa di testo del verdetto.
    """
    if not OPENAI_AVAILABLE or not API_KEY:
        logger.error("Libreria OpenAI mancante o API KEY non configurata.")
        return "Analisi AI temporaneamente non disponibile (API Key mancante)."

    openai.api_key = API_KEY
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        home_team=match_data.get("home_name", "Casa"),
        away_team=match_data.get("away_name", "Ospiti"),
        home_score=match_data.get("home_score", 0),
        away_score=match_data.get("away_score", 0),
        home_xg=match_data.get("home_xg", 0.0),
        away_xg=match_data.get("away_xg", 0.0),
        home_imr=match_data.get("home_imr", 0),
        away_imr=match_data.get("away_imr", 0)
    )

    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=250,
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Pulizia rigorosa del JSON (rimuove eventuali ```json ... ```)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        parsed = json.loads(response_text.strip())
        return parsed.get("ai_verdict", "Verdetto non generato correttamente.")
        
    except Exception as e:
        logger.exception("Fallimento chiamata API DeepSeek/OpenAI: %s", e)
        return "Errore di connessione al motore di analisi xPalermoStat."

if __name__ == "__main__":
    # Test Rapido
    test_data = {
        "home_name": "Bologna", "away_name": "Lazio",
        "home_score": 0, "away_score": 2,
        "home_xg": 1.33, "away_xg": 2.14,
        "home_imr": 30, "away_imr": 25
    }
    print("TEST SENTENZA:")
    print(generate_imr_verdict(test_data))