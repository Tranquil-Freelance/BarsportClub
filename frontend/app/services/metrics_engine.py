"""
Motore di Calcolo delle Metriche Avanzate - xPalermoStat
Basato sul Technical Design Document ufficiale.
"""

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