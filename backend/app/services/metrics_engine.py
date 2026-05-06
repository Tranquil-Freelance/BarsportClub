"""
Motore di Calcolo delle Metriche Avanzate - xPalermoStat
Basato sul Technical Design Document ufficiale.
"""

import math
import statistics
from typing import List, Optional, Tuple, Dict, Any

# ==========================================
# 1. TEAM PERFORMANCE ANALYTICS
# ==========================================

def calculate_tts(xg: float, xga: float) -> float:
    """
    True Team Strength (TTS)
    Stima la reale forza eliminando la varianza dei risultati.
    > 1.0 = Dominante | < 0 = Debole
    """
    return round(xg - xga, 3)


def calculate_sqd(xg: float, shots: int, xga: float, shots_conceded: int) -> float:
    """
    Shot Quality Differential (SQD)
    Confronta la qualità delle occasioni create e concesse.
    Positivo = Crea occasioni migliori | Negativo = Concede occasioni migliori
    """
    attack_quality = (xg / shots) if shots > 0 else 0.0
    defense_quality = (xga / shots_conceded) if shots_conceded > 0 else 0.0
    return round(attack_quality - defense_quality, 4)


def calculate_ae(goals: int, xg: float) -> float:
    """
    Attacking Efficiency (AE)
    Misura l'efficienza nella finalizzazione.
    > 1 = Molto efficiente | < 1 = Inefficiente
    """
    return round(goals / xg, 3) if xg > 0 else 0.0


def calculate_pdi(shots: int, xg: float, key_passes: int) -> float:
    """
    Possession Danger Index (PDI)
    Misura quanto il possesso viene convertito in pericolo.
    """
    return round((0.4 * shots) + (0.4 * xg) + (0.2 * key_passes), 3)


def calculate_tci(xg: float, shots: int, xgchain: float, attacks: int, key_passes: int) -> float:
    """
    Threat Creation Index (TCI)
    Misura la capacità complessiva di generare pericolo offensivo.
    """
    if shots == 0 or attacks == 0:
        return 0.0
    
    shot_quality = xg / shots
    chain_participation = xgchain / attacks
    pass_danger = key_passes / attacks
    
    return round(shot_quality + chain_participation + pass_danger, 4)


def calculate_sas(attack_quality: float, creation_diversity: float, defensive_stability: float) -> float:
    """
    Squad Architecture Score (SAS) – future metric
    Misura quanto una squadra è strutturalmente efficiente.
    """
    return round(attack_quality + creation_diversity + defensive_stability, 3)


def calculate_dfi(xg_per_possession: float, key_passes_per_possession: float, shots_in_area_ratio: float) -> float:
    """
    Danger Flow Index (DFI)
    Misura la capacità di trasformare il possesso in pericolo.
    """
    return round((xg_per_possession + key_passes_per_possession + shots_in_area_ratio) / 3, 4)


# ==========================================
# 2. BETTING ANALYTICS
# ==========================================

def calculate_fli(goals: int, xg: float) -> float:
    """
    Finishing Luck Index (FLI)
    Misura quanto una squadra sovra-performa rispetto agli xG creati.
    Positivo alto = Molto fortunata (o cinica) | Negativo alto = Sfortunata (o sprecona)
    """
    return round(goals - xg, 2)


def calculate_dli(xga: float, goals_conceded: int) -> float:
    """
    Defensive Luck Index (DLI)
    Misura la fortuna difensiva (subisce meno gol degli xGA concessi).
    Positivo = Difesa fortunata/Portiere top | Negativo = Difesa sfortunata/Papere
    """
    return round(xga - goals_conceded, 2)


def calculate_rri(goals: int, xg: float, goals_conceded: int, xga: float) -> float:
    """
    Regression Risk Index (RRI)
    Misura il rischio di regressione verso la media.
    """
    attack_gap = abs(goals - xg)
    defense_gap = abs(goals_conceded - xga)
    return round(attack_gap + defense_gap, 2)


def calculate_mvi(xg_differences: List[float]) -> float:
    """
    Match Volatility Index (MVI)
    Misura la varianza delle differenze di xG per partita.
    """
    if len(xg_differences) < 2:
        return 0.0
    return round(statistics.variance(xg_differences), 4)


def calculate_epm(xpts_list: List[float], points_list: List[float]) -> float:
    """
    Expected Points Momentum (EPM)
    Differenza tra xPTS medi e punti reali medi nelle ultime partite.
    """
    if not xpts_list or not points_list:
        return 0.0
    avg_xpts = sum(xpts_list) / len(xpts_list)
    avg_points = sum(points_list) / len(points_list)
    return round(avg_xpts - avg_points, 3)


def calculate_bvi(model_prob: float, odds: float) -> float:
    """
    Betting Value Index (BVI)
    Differenza tra probabilità stimata dal modello e probabilità implicita della quota.
    """
    bookmaker_prob = 1 / odds if odds != 0 else 0.0
    return round(model_prob - bookmaker_prob, 4)


def calculate_mii(model_prob: float, bookmaker_prob: float) -> float:
    """
    Market Inefficiency Index (MII)
    Identico a BVI ma con probabilità del bookmaker già calcolata.
    """
    return round(model_prob - bookmaker_prob, 4)


def calculate_opi(team_xg: float, opponent_xg: float) -> float:
    """
    Over/Under Pressure Index (OPI)
    Stima la probabilità che una partita produca molti gol.
    """
    return round(team_xg + opponent_xg, 2)


# ==========================================
# 3. PLAYER SCOUTING ANALYTICS
# ==========================================

def calculate_ois(xg: float, xa: float, xgchain: float, shots: int) -> float:
    """
    Offensive Impact Score (OIS)
    Misura l'impatto offensivo complessivo di un giocatore.
    Pesi: 0.40 × xG + 0.30 × xA + 0.20 × xGChain + 0.10 × Shots
    """
    return round(0.40 * xg + 0.30 * xa + 0.20 * xgchain + 0.10 * shots, 3)


def calculate_cii(xa: float, key_passes: int, xgbuildup: float) -> float:
    """
    Creative Influence Index (CII)
    Misura quanto un giocatore contribuisce alla creazione del gioco.
    Pesi: 0.50 × xA + 0.30 × Key Passes + 0.20 × xGBuildup
    """
    return round(0.50 * xa + 0.30 * key_passes + 0.20 * xgbuildup, 3)


def calculate_air(xgchain: float, minutes_played: int) -> float:
    """
    Attacking Involvement Rate (AIR)
    Quanto un giocatore partecipa alle azioni offensive per minuto.
    """
    if minutes_played == 0:
        return 0.0
    return round(xgchain / minutes_played, 6)


def calculate_bcs(xgbuildup: float, minutes_played: int) -> float:
    """
    Build-Up Contribution Score (BCS)
    Contributo nella costruzione delle azioni per minuto.
    """
    if minutes_played == 0:
        return 0.0
    return round(xgbuildup / minutes_played, 6)


def calculate_fes(goals: int, xg: float) -> float:
    """
    Finishing Efficiency Score (FES)
    Efficienza nella finalizzazione (goals / xG).
    """
    if xg == 0:
        return 0.0
    return round(goals / xg, 3)


def calculate_pir(
    ois: float,
    cii: float,
    air: float,
    bcs: float,
    fes: float,
) -> float:
    """
    Player Impact Rating (PIR)
    Indicatore complessivo del valore del giocatore.
    Pesi: 0.30 × OIS + 0.25 × CII + 0.20 × AIR + 0.15 × BCS + 0.10 × FES
    """
    return round(0.30 * ois + 0.25 * cii + 0.20 * air + 0.15 * bcs + 0.10 * fes, 3)


# ==========================================
# 4. SCOUTING INTELLIGENCE SYSTEMS
# ==========================================

def player_similarity(player_vector: List[float], database_vectors: Dict[Any, List[float]]) -> List[Tuple[Any, float]]:
    """
    Player Similarity Engine (PSE)
    Calcola similarità euclidea tra un vettore giocatore e un database di vettori.
    Restituisce lista ordinata (player_id, similarity_score).
    """
    similarities = []
    for player_id, vector in database_vectors.items():
        if len(vector) != len(player_vector):
            continue
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(player_vector, vector)))
        similarity = 1 / (1 + distance)
        similarities.append((player_id, similarity))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:10]


def calculate_ppi(
    xg_per90: float,
    xa_per90: float,
    xgchain_per90: float,
    xgbuildup_per90: float,
    conversion_gap: float,
    age_factor: float,
) -> float:
    """
    Player Potential Index (PPI)
    Identifica giocatori con alto potenziale di crescita.
    Pesi: 0.50 × UPS + 0.30 × Conversion Gap + 0.20 × Age Factor
    """
    ups = 0.35 * xg_per90 + 0.25 * xa_per90 + 0.20 * xgchain_per90 + 0.20 * xgbuildup_per90
    return round(0.50 * ups + 0.30 * conversion_gap + 0.20 * age_factor, 3)


def calculate_mvgi(performance_value_score: float, market_value: float) -> float:
    """
    Market Value Gap Index (MVGI)
    Differenza tra performance statistica e valore di mercato normalizzato.
    """
    normalized_value = math.log(market_value) if market_value > 0 else 0.0
    return round(performance_value_score - normalized_value, 3)


def percentile(value: float, distribution: List[float]) -> float:
    """
    Calcola il percentile di un valore rispetto a una distribuzione.
    """
    if not distribution:
        return 0.0
    rank = sum(v < value for v in distribution)
    return round(rank / len(distribution) * 100, 1)


# ==========================================
# 5. PREDICTION MODELS
# ==========================================

def poisson_probability(lam: float, k: int) -> float:
    """
    Probabilità di k gol data una media λ (distribuzione di Poisson).
    """
    if lam <= 0 or k < 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def match_probabilities(home_xg: float, away_xg: float, max_goals: int = 10) -> Tuple[float, float, float]:
    """
    Calcola probabilità di vittoria casa, pareggio, vittoria ospite.
    Utilizza il modello Poisson.
    """
    home_probs = [poisson_probability(home_xg, i) for i in range(max_goals)]
    away_probs = [poisson_probability(away_xg, i) for i in range(max_goals)]
    
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    
    for h in range(max_goals):
        for a in range(max_goals):
            p = home_probs[h] * away_probs[a]
            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p
    
    return round(home_win, 4), round(draw, 4), round(away_win, 4)


def over_under_probabilities(home_xg: float, away_xg: float, threshold: float = 2.5) -> Tuple[float, float]:
    """
    Probabilità Over / Under rispetto a una soglia di gol totali.
    """
    max_goals = 10
    home_probs = [poisson_probability(home_xg, i) for i in range(max_goals)]
    away_probs = [poisson_probability(away_xg, i) for i in range(max_goals)]
    
    over = 0.0
    under = 0.0
    
    for h in range(max_goals):
        for a in range(max_goals):
            p = home_probs[h] * away_probs[a]
            total = h + a
            if total >= threshold:
                over += p
            else:
                under += p
    
    return round(over, 4), round(under, 4)


def expected_match_outcome(
    home_attack_strength: float,
    away_defense_weakness: float,
    away_attack_strength: float,
    home_defense_weakness: float,
    league_avg_goals: float,
    home_advantage: float = 1.10,
) -> Tuple[float, float]:
    """
    Calcola gli expected goals per casa e ospite.
    """
    home_xg = home_attack_strength * away_defense_weakness * league_avg_goals * home_advantage
    away_xg = away_attack_strength * home_defense_weakness * league_avg_goals
    return round(home_xg, 3), round(away_xg, 3)


# ==========================================
# 6. TACTICAL INTELLIGENCE & FUTURE METRICS (stubs)
# ==========================================

def calculate_tii(
    chance_consistency: float,
    attacking_pattern_stability: float,
    chance_creation_structure: float,
    defensive_stability: float,
) -> float:
    """
    Tactical Identity Index (TII)
    Misura quanto una squadra possiede un’identità tattica chiara e coerente.
    """
    return round(
        0.25 * chance_consistency +
        0.25 * attacking_pattern_stability +
        0.25 * chance_creation_structure +
        0.25 * defensive_stability,
        3,
    )


def calculate_sci(
    role_balance: float,
    creative_distribution: float,
    creation_finishing_balance: float,
    defensive_stability: float,
) -> float:
    """
    Squad Composition Index (SCI)
    Misura quanto una rosa è costruita in modo equilibrato.
    """
    return round(
        0.30 * role_balance +
        0.30 * creative_distribution +
        0.20 * creation_finishing_balance +
        0.20 * defensive_stability,
        3,
    )


def calculate_gmfi(
    chance_creation_fit: float,
    role_suitability: float,
    buildup_participation: float,
    finishing_structure: float,
) -> float:
    """
    Game Model Fit Index (GMFI)
    Misura quanto la rosa è compatibile con il sistema di gioco dell’allenatore.
    """
    return round(
        0.30 * chance_creation_fit +
        0.30 * role_suitability +
        0.20 * buildup_participation +
        0.20 * finishing_structure,
        3,
    )


def detect_tactical_style(
    possession_score: float,
    direct_score: float,
    transition_score: float,
) -> str:
    """
    Identifica automaticamente lo stile di gioco di una squadra.
    Restituisce il nome dello stile con punteggio più alto.
    """
    scores = {
        "possession": possession_score,
        "direct": direct_score,
        "transition": transition_score,
    }
    return max(scores, key=scores.get)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def entropy(distribution: List[float]) -> float:
    """
    Calcola l'entropia di una distribuzione di probabilità.
    """
    total = sum(distribution)
    if total == 0:
        return 0.0
    norm = [p / total for p in distribution]
    return -sum(p * math.log(p) if p > 0 else 0.0 for p in norm)