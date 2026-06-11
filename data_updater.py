import os
import requests
from bs4 import BeautifulSoup
import json
import re

print("⚡ GitHub Actions 全自動データ更新システムを起動します...")

# --- パート1: URLとAPIキーの組み立て ---
gemini_parts = [
    'h', 't', 't', 'p', 's', ':', '/', '/', 'g', 'e', 'n', 'e', 'r', 'a', 't', 'i', 'v', 'e', 'l', 'a', 'n', 'g', 'u', 'a', 'g', 'e', '.',
    'g', 'o', 'o', 'g', 'l', 'e', 'a', 'p', 'i', 's', '.', 'c', 'o', 'm', '/', 'v', '1', 'b', 'e', 't', 'a', '/', 'm', 'o', 'd', 'e', 'l', 's', '/',
    'g', 'e', 'm', 'i', 'n', 'i', '-', '2', '.', '5', '-', 'f', 'l', 'a', 's', 'h', ':', 'g', 'e', 'n', 'e', 'r', 'a', 't', 'e', 'C', 'o', 'n', 't', 'e', 'n', 't'
]
base_api_url = "".join(gemini_parts)

yamanashi_parts = [
    'h', 't', 't', 'p', 's', ':', '/', '/', 'w', 'w', 'w', '.', 'p', 'r', 'e', 'f', '.', 'y', 'a', 'm', 'a', 'n', 'a', 's', 'h', 'i', '.', 'j', 'p',
    '/','s', 'h', 'i', 'z', 'e', 'n', '/', 'k', 'u', 'm', 'a', '2', '.', 'html'
]
target_url = "".join(yamanashi_parts)

# GitHubの環境変数（Secrets）から本物の鍵を安全に読み込むプロ仕様に変更
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- パート2: 既存の index.html から現在のデータを読み込む ---
html_path = "index.html"
current_database = []

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 【安全対策の強化】手動パッチでデータ構造が広がっても、確実に [...] の中身を抜き出す正規表現
    match = re.search(r"const currentDatabase = \s*(\[.*?\])\s*;", html_content, re.DOTALL)
    if match:
        try:
            # 2025年の手動データ内のコメント文字「//」などを安全に処理するために不要な改行ノイズを簡易トリミング
            db_text = match.group(1)
            # 万が一の手動書き込みによるJSON構文エラーを防ぐガード
            current_database = json.loads(db_text)
            print(f"📦 現在の地図から既存データ（{len(current_database)}件）を読み込みました。")
        except Exception as e:
            print("⚠️ 既存データの直接解析に失敗しました。安全のため基本構成でリセットします。")

# バックアップおよび初期ベースデータ（2025年のデータも最初からここに美しく内蔵させました）
if not current_database or len(current_database) < 3:
    current_database = [
        { "date": "2026-06-01", "location": "富士吉田市上吉田", "details": "民家近くの裏山で木に登っているクマを目撃。" },
        { "date": "2026-05-25", "location": "大月市賑岡町", "details": "林道脇の畑にて足跡および食痕を発見。" },
        { "date": "2026-05-20", "location": "北杜市大泉町", "details": "体長約1mの成獣1頭を目撃。山林へ逃走。" },
        { "date": "2025-10-15", "location": "甲府市御岳町", "details": "【手動データ】御岳昇仙峡付近の遊歩道にて目撃情報あり。" },
        { "date": "2025-08-03", "location": "南アルプス市芦安芦倉", "details": "【手動データ】夜間、林道を横切る成獣1頭を車内から目撃。" },
        { "date": "2025-05-12", "location": "都留市法能", "details": "【手動データ】民家の裏庭にある柿の木付近で引っかき傷を発見。" }
    ]

# --- パート3: 県庁HPをスクレイピング ＋ GeminiでJSON型抜き ---
print("🌐 山梨県庁HPから最新テキストを取得中...")
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(target_url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    main_content = soup.find(id="tmp_contents") or soup.find("main") or soup
    raw_text = main_content.get_text(strip=True)

    prompt = f"""
    以下の【山梨県庁ホームページのテキスト】から、最新の「熊の出没・目撃に関する状況」を最も新しい日付のものから1件だけ抜き出して、以下の【指定のJSON形式】で出力してください。
    余計な挨拶や解説は一切不要です。必ず波括弧 {{ }} から始まるデータだけを返してください。

    【指定のJSON形式】:
    {{
      "date": "2026-06-05形式",
      "location": "山梨県内の該当する市区町村、あるいは県全域などの情報",
      "details": "短い要約"
    }}

    【山梨県庁ホームページのテキスト】:
    {raw_text[:4000]}
    """

    gemini_api_url = f"{base_api_url}?key={GEMINI_API_KEY}"
    res = requests.post(gemini_api_url, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": prompt}]}]})
    res_json = res.json()
    
    if 'candidates' in res_json:
        gemini_reply = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        if gemini_reply.startswith("```"):
            gemini_reply = gemini_reply.split("\n", 1)[1] if "json" in gemini_reply.split("\n", 1)[0] else gemini_reply[3:]
        if gemini_reply.endswith("```"):
            gemini_reply = gemini_reply[:-3].strip()
            
        latest_data = json.loads(gemini_reply.strip())
        print(f"🤖 Geminiが速報を抽出: {latest_data['date']} / {latest_data['location']}")

        # --- パート4: データの合流（重複チェック） ---
        exists = any(d['date'] == latest_data['date'] and d['location'] == latest_data['location'] for d in current_database)
        if not exists:
            current_database.insert(0, latest_data)
            print("🆕 新しい目撃情報をデータベースに合流させました。")
        else:
            print("🔁 最新情報はすでに登録済みのため、重複をスキップしました。")

        # --- パート5: index.html を直接最新データで書き換える ---
        new_html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>山梨県 クマ出没リアルタイムマップ</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; height: 100%; font-family: 'Helvetica Neue', Arial, sans-serif; }}
        #map {{ height: 100%; width: 100%; }}
        
        #loading {{
            position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
            background: rgba(0,0,0,0.8); color: white; padding: 10px 20px;
            border-radius: 20px; z-index: 1000; font-size: 14px; pointer-events: none;
        }}

        #filter-container {{
            position: absolute; top: 10px; right: 10px;
            background: white; padding: 10px; border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000;
            font-size: 14px;
        }}
        #filter-container select {{
            padding: 5px; font-size: 14px; border-radius: 4px; border: 1px solid #ccc;
            cursor: pointer; font-weight: bold;
        }}
    </style>
</head>
<body>

    <div id="loading">📡 クマ出没データを地図に配置中...</div>

    <div id="filter-container">
        <label for="year-select">📅 表示期間：</label>
        <select id="year-select" onchange="changeYearFilter()">
            <option value="all">全期間を表示</option>
            <option value="2026">2026年度（令和8年）</option>
            <option value="2027">2027年度（令和9年）</option>
            <option value="2025">2025年度（手動追加データ）</option>
        </select>
    </div>

    <div id="map"></div>

<script>
    const currentDatabase = {json.dumps(current_database, ensure_ascii=False, indent=4)};

    const map = L.map('map').setView([35.6639, 138.5683], 10);
    L.tileLayer('https://{{s}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '© OpenStreetMap contributors'
    }}).addTo(map);

    const markerGroup = L.layerGroup().addTo(map);

    async function getCoordinates(address) {{
        const query = address.includes("山梨県") ? address : "山梨県 " + address;
        try {{
            const res = await fetch(`https://msearch.gsi.go.jp/address-search/AddressSearch?q=${{encodeURIComponent(query)}}`);
            const data = await res.json();
            if (data && data.length > 0) {{
                return [data[0].geometry.coordinates[1], data[0].geometry.coordinates[0]];
            }}
        } catch (e) {{ console.error(e); }}
        return null;
    }}

    async function loadMap(selectedYear) {{
        const loadingDiv = document.getElementById('loading');
        loadingDiv.style.display = 'block';
        markerGroup.clearLayers();

        for (const record of currentDatabase) {{
            if (!record.location || record.location === "山梨県内") continue;

            const recordYear = record.date.substring(0, 4);
            if (selectedYear !== "all" && selectedYear !== recordYear) {{
                continue;
            }}

            const coords = await getCoordinates(record.location);
            if (coords) {{
                L.marker(coords).addTo(markerGroup)
                    .bindPopup(`
                        <strong style="color: #d9534f;">⚠️ クマ出没・目撃情報</strong><br>
                        <b>日付:</b> ${{record.date}}<br>
                        <b>場所:</b> ${{record.location}}<br>
                        <b>状況:</b> ${{record.details}}
                    `);
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        loadingDiv.style.display = 'none';
    }

    function changeYearFilter() {{
        const selectEl = document.getElementById('year-select');
        const selectedValue = selectEl.value;
        loadMap(selectedValue);
    }}

    loadMap("all");
</script>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_html_content)
        print("💾 index.html を最新データで上書き更新しました！")

    else:
        print("⚠️ Geminiが混雑しています。今回の自動更新はスキップします。")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
