import os
import json
import time
from dotenv import load_dotenv
import yahoo_fantasy_api as yfa
from yahoo_oauth import OAuth2

def safe_float(val):
    try:
        if val in (None, "-", "", " "): return 0.0
        return float(val)
    except: return 0.0

def chunk(lst, size=25):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]
# .env dosyasını yükle
load_dotenv()

data_folder = "data"
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

sc = OAuth2(
    os.getenv("YAHOO_CLIENT_ID"),
    os.getenv("YAHOO_CLIENT_SECRET")
)

gm = yfa.Game(sc, "nba")
league_id = os.getenv("YAHOO_LEAGUE_ID")
if league_id:
    # .env dosyanızdaki YAHOO_LEAGUE_ID'nizde bir sıkıntı yoksa o ligin ID'sine göre yükleme yapar
    lg = gm.to_league(league_id)
    print(f"Sabit Lig yüklendi: {league_id}")
else:
    # Eğer .env'deki YAHOO_LEAGUE_ID boşsa otomatik olarak ilk lig ID'sini alır
    # Eğer 2025 yılına ait aktif bir liginiz yoksa hata verir.
    league_id = gm.league_ids(year=2025)[0]
    lg = gm.to_league(league_id)
    print(f"Lig otomatik olarak bulundu: {league_id}")

# Kadro ve pozisyon bilgileri toplama
def clean_player_base_info(p, team_name):
    p_name = p.get('name')
    if isinstance(p_name, dict): p_name = p_name.get('full', 'Unknown')
    
    # Burada çıkardığımız pozisyonlar her oyuncuda olanlar onun için bir anlam taşımıyorlar.
    exclude_list = ['P', 'UTIL', 'IL', 'IL+', 'BN']
    all_pos = []
    ep = p.get('eligible_positions', [])
    if isinstance(ep, list):
        for item in ep:
            val = item.get('position') if isinstance(item, dict) else item
            if val and val.upper() not in exclude_list:
                all_pos.append(val.upper())
    
    unique_pos = sorted(list(set(all_pos)))
    return {
        "player_id": str(p['player_id']),
        "name": p_name,
        "current_team": team_name,
        "position": "/".join(unique_pos) if unique_pos else "N/A"
    }

player_base_map = {}
teams = lg.teams()
for t_key, t_val in teams.items():
    t_name = t_val['name']
    team_obj = lg.to_team(t_key)
    for p in team_obj.roster():
        info = clean_player_base_info(p, t_name)
        player_base_map[info["player_id"]] = info

try:
    fas = lg.free_agents('ALL')
    for p in fas[:200]:
        info = clean_player_base_info(p, "Free Agent")
        player_base_map[info["player_id"]] = info
except: pass

player_ids = list(player_base_map.keys())

# Average ve Total istatistikleri çekme ve birleştirme
final_data = []
print(f"{len(player_ids)} oyuncu için Total ve Average veriler birleştiriliyor")

for batch_ids in chunk(player_ids, 25):
    try:
        # 1. Ortalamaları Çek
        avg_stats = lg.player_stats(batch_ids, "average_season")
        # 2. Toplamları Çek
        total_stats = lg.player_stats(batch_ids, "season")
        
        total_map = {str(ts['player_id']): ts for ts in total_stats}

        for s in avg_stats:
            pid = str(s.get("player_id"))
            base = player_base_map.get(pid)
            ts = total_map.get(pid, {})
            
            if not base: continue

            combined_record = {
                "player_id": pid,
                "name": base.get("name"),
                "current_team": base.get("current_team"),
                "position": base.get("position"),
                # Ortalamalar (Per Game)
                "AVG_PTS": safe_float(s.get("PTS")),
                "AVG_REB": safe_float(s.get("REB")),
                "AVG_AST": safe_float(s.get("AST")),
                "AVG_ST": safe_float(s.get("ST", s.get("STL", 0))),
                "AVG_BLK": safe_float(s.get("BLK")),
                "AVG_3PTM": safe_float(s.get("3PTM", s.get("10", 0))),
                "AVG_TO": safe_float(s.get("TO")),
                "FG%": safe_float(s.get("FG%")),
                "FT%": safe_float(s.get("FT%")),
                # Toplamlar (Season Totals)
                "TOTAL_PTS": safe_float(ts.get("PTS")),
                "TOTAL_REB": safe_float(ts.get("REB")),
                "TOTAL_AST": safe_float(ts.get("AST")),
                "TOTAL_ST": safe_float(ts.get("ST", ts.get("STL", 0))),
                "TOTAL_BLK": safe_float(ts.get("BLK")),
                "TOTAL_3PTM": safe_float(ts.get("3PTM", ts.get("10", 0))),
                "TOTAL_TO": safe_float(ts.get("TO")),
                "FGM/A": ts.get("FGM/A", "0/0"),
                "FTM/A": ts.get("FTM/A", "0/0")
            }
            final_data.append(combined_record)
            
        print(f"İlerleme: {len(final_data)} / {len(player_ids)}")
        time.sleep(1) 
    except Exception as e:
        print(f"Batch hatası: {e}")

# Json dosyasına kaydetme işemi
output_path = os.path.join(data_folder, "nba_fantasy_players.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)
print(f"\nBAŞARILI: {len(final_data)} oyuncu kaydedildi.")