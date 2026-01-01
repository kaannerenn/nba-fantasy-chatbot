# %%
import json
import os
# Eğer şu an 'notebooks' klasöründeysek ana dizine çık

    
if os.getcwd().endswith("notebooks"):
    os.chdir("..")
input_path = os.path.join("data", "nba_league_stats.json")
with open(input_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# 2. İstatistikleri Takım Bazlı Grupla
team_aggregates = {}

def parse_fraction(val):
    """'191/390' gibi değerleri pay ve payda olarak ayırır."""
    try:
        made, att = map(float, val.split('/'))
        return made, att
    except:
        return 0.0, 0.0

for week_id, matchups in raw_data.items():
    for team in matchups:
        name = team["team_name"]
        stats = team["stats"]
        
        if name not in team_aggregates:
            team_aggregates[name] = {
                "weeks_played": 0,
                "FGM": 0.0, "FGA": 0.0,
                "FTM": 0.0, "FTA": 0.0,
                "3PTM": 0.0, "PTS": 0.0,
                "REB": 0.0, "AST": 0.0,
                "ST": 0.0, "BLK": 0.0, "TO": 0.0
            }
        
        # Toplamları Güncelle
        team_aggregates[name]["weeks_played"] += 1
        
        fgm, fga = parse_fraction(stats.get("FGM/A", "0/0"))
        ftm, fta = parse_fraction(stats.get("FTM/A", "0/0"))
        
        team_aggregates[name]["FGM"] += fgm
        team_aggregates[name]["FGA"] += fga
        team_aggregates[name]["FTM"] += ftm
        team_aggregates[name]["FTA"] += fta
        team_aggregates[name]["3PTM"] += float(stats.get("3PTM", 0))
        team_aggregates[name]["PTS"] += float(stats.get("PTS", 0))
        team_aggregates[name]["REB"] += float(stats.get("REB", 0))
        team_aggregates[name]["AST"] += float(stats.get("AST", 0))
        team_aggregates[name]["ST"] += float(stats.get("ST", 0))
        team_aggregates[name]["BLK"] += float(stats.get("BLK", 0))
        team_aggregates[name]["TO"] += float(stats.get("TO", 0))

# 3. Ortalamaları Hesapla ve Format
final_summary = []

for team_name, totals in team_aggregates.items():
    wp = totals["weeks_played"]
    
    summary = {
        "team_name": team_name,
        "weeks_counted": wp,
        "totals": {
            "PTS": totals["PTS"],
            "REB": totals["REB"],
            "AST": totals["AST"],
            "ST": totals["ST"],
            "BLK": totals["BLK"],
            "3PTM": totals["3PTM"],
            "TO": totals["TO"],
            "FGM/A": f"{int(totals['FGM'])}/{int(totals['FGA'])}",
            "FTM/A": f"{int(totals['FTM'])}/{int(totals['FTA'])}"
        },
        "averages": {
            "PTS": round(totals["PTS"] / wp, 2),
            "REB": round(totals["REB"] / wp, 2),
            "AST": round(totals["AST"] / wp, 2),
            "ST": round(totals["ST"] / wp, 2),
            "BLK": round(totals["BLK"] / wp, 2),
            "3PTM": round(totals["3PTM"] / wp, 2),
            "TO": round(totals["TO"] / wp, 2),
            "FG%": round(totals["FGM"] / totals["FGA"], 3) if totals["FGA"] > 0 else 0,
            "FT%": round(totals["FTM"] / totals["FTA"], 3) if totals["FTA"] > 0 else 0
        }
    }
    final_data = f"{team_name} takımı {wp} hafta boyunca toplam {totals['PTS']} sayı attı ve maç başına {summary['averages']['PTS']} ortalama yakaladı."
    summary["text_description"] = final_data # RAG için açıklama metni
    final_summary.append(summary)

# 4. Kaydet
output_path = os.path.join("data", "nba_league_summary.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_summary, f, ensure_ascii=False, indent=4)

print(f"Lig özeti oluşturuldu: {output_path}")


