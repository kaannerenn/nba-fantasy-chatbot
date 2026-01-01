import os
import json
from dotenv import load_dotenv
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

# .env dosyasını yükle
load_dotenv()

def get_league_stats():
    # 1. ENV DEĞİŞKENLERİNİ ALMA
    client_id = os.getenv('YAHOO_CLIENT_ID')
    client_secret = os.getenv('YAHOO_CLIENT_SECRET')
    league_id = os.getenv('YAHOO_LEAGUE_ID')

    # ID gelmediyse işlemi durdur
    if not league_id:
        print(".env dosyasında YAHOO_LEAGUE_ID bulunamadı")
        return

    # Data klasörünü kontrol et, yoksa oluştur
    if not os.path.exists("data"):
        os.makedirs("data")

    # 2. AUTH VE BAĞLANTI
    # OAuth2 için geçici dosya oluşturma
    auth_config = {
        'consumer_key': client_id, 
        'consumer_secret': client_secret
    }
    
    with open('temp_auth.json', 'w') as f:
        json.dump(auth_config, f)

    try:
        sc = OAuth2(None, None, from_file='temp_auth.json')
        gm = yfa.Game(sc, 'nba')
        lg = gm.to_league(league_id)
        print(f"Bağlantı Başarılı: {lg.settings()['name']} (ID: {league_id})")

        # 3. İSİMLENDİRME MAPPINGI YAHOO STATS ID'LERİ İÇİN
        custom_mapping = {
            "9004003": "FGM/A",
            "5": "FG%",
            "9007006": "FTM/A",
            "8": "FT%",
            "10": "3PTM",
            "12": "PTS",
            "15": "REB",
            "16": "AST",
            "17": "ST",
            "18": "BLK",
            "19": "TO"
        }

        current_week = lg.current_week()
        all_stats_data = {}

        # 4-HAFTALIK VERİ TOPLAMA
        # range(1, current_week) -> 1. haftadan başlar, şu anki haftadan BİR ÖNCEKİ haftayı alır.
        # Şu anki haftayı almamamızın sebebi hafta tamamlanmamış olabilir.
        for week in range(1, current_week):
            print(f"Hafta {week} verileri alınıyor...")
            week_data = []
            
            try:
                m_raw = lg.matchups(week)

                # takımları bulma fonksiyonu
                def find_teams(obj):
                    if isinstance(obj, dict):
                        if 'team' in obj: yield obj['team']
                        for v in obj.values(): yield from find_teams(v)
                    elif isinstance(obj, list):
                        for item in obj: yield from find_teams(item)

                for team_content in find_teams(m_raw):
                    team_name = "Unknown"
                    stats_dict = {}
                    
                    for part in team_content:
                        # Takım İsmi Bulma
                        if isinstance(part, list):
                            for sub in part:
                                if isinstance(sub, dict) and 'name' in sub:
                                    team_name = sub['name']
                        
                        # İstatistik Bulma ve İsimlendirme
                        if isinstance(part, dict) and 'team_stats' in part:
                            for s in part['team_stats']['stats']:
                                s_id = str(s['stat']['stat_id'])
                                stat_label = custom_mapping.get(s_id, s_id)
                                s_val = s['stat']['value']
                                stats_dict[stat_label] = s_val
                    
                    if team_name != "Unknown":
                        week_data.append({"team_name": team_name, "stats": stats_dict})
                
                # Takımları tekilleştir
                seen_teams = set()
                unique_week_data = []
                for d in week_data:
                    if d['team_name'] not in seen_teams:
                        unique_week_data.append(d)
                        seen_teams.add(d['team_name'])

                all_stats_data[f"week_{week}"] = unique_week_data
                
            except Exception as e:
                print(f"Hafta {week} hatası: {str(e)}")

        # 5. Kayıt
        output_path = os.path.join("data", "nba_league_stats.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_stats_data, f, ensure_ascii=False, indent=4)
        
        print(f"\nİşlem Tamam! Veriler '{output_path}' dosyasına kaydedildi.")

    except Exception as e:
        print(f"Kritik Bağlantı Hatası: {e}")
    # Geçici dosyayı silme
    finally:
        if os.path.exists('temp_auth.json'): 
            os.remove('temp_auth.json')

if __name__ == "__main__":
    get_league_stats()