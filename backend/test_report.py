import re
import json
import time
import random
import logging
import os
from DrissionPage import ChromiumPage
from sqlalchemy import create_engine, text, inspect

# ==========================================
# CONFIGURAZIONE DATABASE
# ==========================================
DB_CONFIG = {
    "user": "postgres",
    "pass": "tua_password",  # <--- INSERISCI LA TUA PASSWORD QUI
    "name": "xpalermostat_db",
    "host": "localhost",
    "port": "5432"
}

LEAGUE = "Serie_A" 
SEASON = "2024" # <--- IMPOSTATO SULLA STAGIONE 2024

# ==========================================
# LOGICA ANTI-BAN MANIACALE
# ==========================================
JITTER_MIN = 3.5
JITTER_MAX = 7.2
HIBERNATION_TIME = 1800 # 30 minuti
PAUSA_CAFFE = 15
PAUSA_CAFFE_MIN = 45
PAUSA_CAFFE_MAX = 90

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class UnderstatJSExecutor:
    def __init__(self, db_config):
        db_uri = f"postgresql://{db_config['user']}:{db_config['pass']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        self.engine = create_engine(db_uri)
        self.mappings = self._detect_mappings()
        
        logging.info("Apertura di Chrome... Il browser è sotto controllo automatizzato.")
        self.page = ChromiumPage() 

    def _detect_mappings(self):
        """Mappatura che rispetta le MAIUSCOLE/minuscole esatte del tuo database"""
        inspector = inspect(self.engine)
        maps = {"matches": {}, "shots": {}, "rosters": {}}
        
        for table in ['matches', 'shots', 'rosters']:
            if not inspector.has_table(table): continue
            
            db_cols = {c['name'].lower(): c['name'] for c in inspector.get_columns(table)}
            
            if table == 'matches':
                for target, aliases in {
                    'm_id': ['id', 'match_id'], 'ht': ['home_team', 'h_team'], 
                    'at': ['away_team', 'a_team'], 'hg': ['home_goals', 'h_goals'], 
                    'ag': ['away_goals', 'a_goals'], 'dt': ['date', 'datetime']
                }.items():
                    for alias in aliases:
                        if alias in db_cols: maps['matches'][target] = db_cols[alias]; break
            
            if table == 'shots':
                for target, aliases in {
                    's_id': ['id', 'shot_id'], 'm_id': ['match_id'], 'min': ['minute', 'min'],
                    'p_id': ['player_id', 'id_player'], 'p_name': ['player', 'player_name'], 
                    'ha': ['team_h_a', 'h_a', 'side', 'team_type'], 
                    'xg': ['xg', 'expected_goals'], 
                    'res': ['result'], 'x_pos': ['x'], 'y_pos': ['y'],
                    's_type': ['shot_type', 'shottype'], 'sit': ['situation'],
                    'p_ast': ['player_assisted'], 'l_act': ['last_action', 'lastaction']
                }.items():
                    for alias in aliases:
                        if alias in db_cols: maps['shots'][target] = db_cols[alias]; break
                        
            if table == 'rosters':
                for target, aliases in {
                    'r_id': ['id', 'roster_id'], 'm_id': ['match_id'], 't_id': ['team_id'],
                    'p_id': ['player_id'], 'p_name': ['player', 'player_name'], 'pos': ['position'],
                    'gls': ['goals'], 'shts': ['shots'], 'xg': ['xg'], 'time': ['time', 'time_played'],
                    'yc': ['yellow_card'], 'rc': ['red_card'], 'kp': ['key_passes'], 'ast': ['assists'],
                    'xa': ['xa'], 'xgc': ['xgchain', 'xg_chain'], 'xgb': ['xgbuildup', 'xg_buildup']
                }.items():
                    for alias in aliases:
                        if alias in db_cols: maps['rosters'][target] = db_cols[alias]; break
        return maps

    def _simulate_human_behavior(self):
        try:
            scroll_amount = random.randint(300, 800)
            self.page.scroll.down(scroll_amount)
            time.sleep(random.uniform(0.5, 1.5))
            self.page.scroll.up(random.randint(100, 300))
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            pass 

    def _trigger_hibernation(self):
        logging.warning(f"Ibernazione di {HIBERNATION_TIME/60} minuti avviata causa blocchi.")
        time.sleep(HIBERNATION_TIME)
        logging.info("Ibernazione conclusa. Ripresa delle operazioni.")

    def get_match_ids(self, league, season):
        url = f"https://understat.com/league/{league}/{season}"
        self.page.get(url)
        logging.info("Attendo il caricamento della pagina Lega...")
        
        for _ in range(45):
            if "Just a moment..." in self.page.html or "cf-browser-verification" in self.page.html:
                logging.warning("Cloudflare in azione sulla pagina Lega. Mimetismo in corso...")
                time.sleep(3)
                continue

            if self.page.run_js("return typeof datesData !== 'undefined';"):
                break
            time.sleep(1)
        else:
            self._trigger_hibernation()
            return []
            
        self._simulate_human_behavior()
        js_command = "return datesData.filter(m => m.isResult === true || m.isResult === 'true').map(m => m.id);"
        giocati = self.page.run_js(js_command)
        return giocati if giocati else []

    def extract_with_js(self, match_id):
        url = f"https://understat.com/match/{match_id}"
        self.page.get(url)
        
        for _ in range(60):
            if "Just a moment..." in self.page.html or "cf-browser-verification" in self.page.html:
                logging.warning(f"Cloudflare bloccante su Match {match_id}. Risolvi il Captcha o attendo...")
                time.sleep(3)
                continue
                
            if self.page.run_js("return typeof shotsData !== 'undefined';"):
                break
            time.sleep(1)
        else:
            logging.error(f"Timeout blocchi per il match {match_id}.")
            self._trigger_hibernation()
            return None
            
        self._simulate_human_behavior()
        
        js_payload = """
        try {
            return {
                match_id: window.location.pathname.split('/').pop(),
                shots: typeof shotsData !== 'undefined' ? shotsData : {},
                rosters: typeof playersData !== 'undefined' ? playersData : {}
            };
        } catch (e) {
            return null;
        }
        """
        return self.page.run_js(js_payload)

    def sanitize(self, val, v_type=float):
        if val is None or str(val).strip().lower() in ["", "none", "null"]: return 0
        try:
            if v_type == int: return int(float(str(val).replace(',', '.')))
            return float(str(val).replace(',', '.'))
        except: return 0

    def inject_data(self, match_id, data):
        if not data or not data.get('shots'): return
            
        m_map = self.mappings.get('matches', {})
        s_map = self.mappings.get('shots', {})
        r_map = self.mappings.get('rosters', {})
        
        q_m = q_s = q_r = None
        
        # L'OMISSIONE DELLA COLONNA ASSORBE QUALSIASI ERRORE DI UNICITÀ (IDEMPOTENZA ASSOLUTA)
        if m_map:
            m_cols = ', '.join([f'"{v}"' for v in m_map.values()])
            m_vals = ', '.join([f":{k}" for k in m_map.keys()])
            q_m = text(f"INSERT INTO matches ({m_cols}) VALUES ({m_vals}) ON CONFLICT DO NOTHING")
            
        if s_map:
            s_cols = ', '.join([f'"{v}"' for v in s_map.values()])
            s_vals = ', '.join([f":{k}" for k in s_map.keys()])
            q_s = text(f"INSERT INTO shots ({s_cols}) VALUES ({s_vals}) ON CONFLICT DO NOTHING")
            
        if r_map:
            r_cols = ', '.join([f'"{v}"' for v in r_map.values()])
            r_vals = ', '.join([f":{k}" for k in r_map.keys()])
            q_r = text(f"INSERT INTO rosters ({r_cols}) VALUES ({r_vals}) ON CONFLICT DO NOTHING")

        with self.engine.begin() as conn:
            all_s = data['shots'].get('h', []) + data['shots'].get('a', [])
            if all_s and q_m is not None:
                sample = all_s[0]
                m_payload = {'m_id': int(match_id)}
                if 'ht' in m_map: m_payload['ht'] = sample.get('h_team')
                if 'at' in m_map: m_payload['at'] = sample.get('a_team')
                if 'hg' in m_map: m_payload['hg'] = self.sanitize(sample.get('h_goals'), int)
                if 'ag' in m_map: m_payload['ag'] = self.sanitize(sample.get('a_goals'), int)
                if 'dt' in m_map: m_payload['dt'] = sample.get('date')
                conn.execute(q_m, m_payload)

            if q_s is not None:
                for side in ['h', 'a']:
                    for s in data['shots'].get(side, []):
                        s_payload = {'m_id': int(match_id), 'ha': side}
                        if 's_id' in s_map: s_payload['s_id'] = self.sanitize(s.get('id'), int)
                        if 'min' in s_map: s_payload['min'] = self.sanitize(s.get('minute'), int)
                        if 'p_id' in s_map: s_payload['p_id'] = self.sanitize(s.get('player_id'), int)
                        if 'p_name' in s_map: s_payload['p_name'] = s.get('player', 'Unknown')
                        if 'xg' in s_map: s_payload['xg'] = self.sanitize(s.get('xG'))
                        if 'res' in s_map: s_payload['res'] = s.get('result')
                        if 'x_pos' in s_map: s_payload['x_pos'] = self.sanitize(s.get('X'))
                        if 'y_pos' in s_map: s_payload['y_pos'] = self.sanitize(s.get('Y'))
                        if 's_type' in s_map: s_payload['s_type'] = s.get('shotType', 'Unknown')
                        if 'sit' in s_map: s_payload['sit'] = s.get('situation', 'Unknown')
                        if 'p_ast' in s_map: s_payload['p_ast'] = s.get('player_assisted', '')
                        if 'l_act' in s_map: s_payload['l_act'] = s.get('lastAction', 'Unknown')
                        
                        conn.execute(q_s, s_payload)

            if q_r is not None:
                for side in ['h', 'a']:
                    for p_id, p_info in data['rosters'].get(side, {}).items():
                        r_payload = {'m_id': int(match_id), 't_id': self.sanitize(p_info.get('team_id'), int)}
                        if 'r_id' in r_map: r_payload['r_id'] = self.sanitize(p_info.get('id'), int)
                        if 'p_id' in r_map: r_payload['p_id'] = self.sanitize(p_info.get('player_id'), int)
                        if 'p_name' in r_map: r_payload['p_name'] = p_info.get('player')
                        if 'pos' in r_map: r_payload['pos'] = p_info.get('position')
                        if 'gls' in r_map: r_payload['gls'] = self.sanitize(p_info.get('goals'), int)
                        if 'shts' in r_map: r_payload['shts'] = self.sanitize(p_info.get('shots'), int)
                        if 'xg' in r_map: r_payload['xg'] = self.sanitize(p_info.get('xG'))
                        if 'time' in r_map: r_payload['time'] = self.sanitize(p_info.get('time'), int)
                        if 'yc' in r_map: r_payload['yc'] = self.sanitize(p_info.get('yellow_card'), int)
                        if 'rc' in r_map: r_payload['rc'] = self.sanitize(p_info.get('red_card'), int)
                        if 'kp' in r_map: r_payload['kp'] = self.sanitize(p_info.get('key_passes'), int)
                        if 'ast' in r_map: r_payload['ast'] = self.sanitize(p_info.get('assists'), int)
                        if 'xa' in r_map: r_payload['xa'] = self.sanitize(p_info.get('xA'))
                        if 'xgc' in r_map: r_payload['xgc'] = self.sanitize(p_info.get('xGChain'))
                        if 'xgb' in r_map: r_payload['xgb'] = self.sanitize(p_info.get('xGBuildup'))
                        conn.execute(q_r, r_payload)

    def run(self, league, season):
        logging.info(f"Avvio estrazione JS Automatica e Stealth per {league} {season}...")
        match_ids = self.get_match_ids(league, season)
        
        if not match_ids:
            logging.error("Nessun match trovato.")
            self.page.quit()
            return

        logging.info(f"Trovate {len(match_ids)} partite. Inizio estrazione sicura...")
        
        for index, m_id in enumerate(match_ids, start=1):
            data = self.extract_with_js(m_id)
            
            if data and data.get('shots'):
                try:
                    self.inject_data(m_id, data)
                    logging.info(f"[{index}/{len(match_ids)}] ✅ Match {m_id} estratto e iniettato.")
                except Exception as e:
                    logging.error(f"❌ Errore DB su match {m_id}: {e}")
            else:
                logging.warning(f"⚠️ Dati vuoti per Match {m_id}.")
            
            wait_time = random.uniform(JITTER_MIN, JITTER_MAX)
            time.sleep(wait_time)
            
            if index % PAUSA_CAFFE == 0 and index < len(match_ids):
                long_wait = random.uniform(PAUSA_CAFFE_MIN, PAUSA_CAFFE_MAX)
                logging.info(f"🍵 Pausa caffè raggiunta. Mimetismo in corso per {long_wait:.2f}s...")
                time.sleep(long_wait)
            
        logging.info("Scraping completato con successo. Chiusura del browser.")
        self.page.quit()

if __name__ == "__main__":
    scraper = UnderstatJSExecutor(DB_CONFIG)
    scraper.run(LEAGUE, SEASON)