import pandas as pd
import requests
import urllib.parse
import json
import re
from datetime import datetime
import os

# -----------------------------------------
# 🔐 Naver API 인증 정보 (Client ID/Secret)
# -----------------------------------------
client_id = "ugpa3NAgjlLEMj4dr9GP"
client_secret = "8xxn8DfZNq"

# -----------------------------------------
# 📂 기업명 리스트 불러오기 (담당 == '1번')
# -----------------------------------------
file_path = "enterprise_df_10k_utf8_data.csv"  # 👉 CSV 위치를 조정하세요
df = pd.read_csv(file_path)
corp_list = df[df['담당'] == '1번']['기업명'].dropna().unique().tolist()

# -----------------------------------------
# 📰 뉴스 수집 시작
# -----------------------------------------
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret,
    "User-Agent": "Mozilla/5.0"
}

news_data = []

for corp in corp_list:
    encoded_query = urllib.parse.quote(corp)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=10&start=1&sort=sim"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                news_data.append({
                    "기업명": corp,
                    "title": re.sub(r"<.*?>", "", item.get("title", "")),
                    "originallink": item.get("originallink", ""),
                    "link": item.get("link", ""),
                    "description": re.sub(r"<.*?>", "", item.get("description", "")),
                    "pubDate": item.get("pubDate", "")
                })
        else:
            print(f"[{corp}] ❌ 요청 실패: {response.status_code} {response.reason}")
    except Exception as e:
        print(f"[{corp}] ❌ 예외 발생: {str(e)}")

# -----------------------------------------
# 📄 결과 CSV 저장 (제출 포맷에 맞게 저장)
# -----------------------------------------
if news_data:
    df_result = pd.DataFrame(news_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"naver_news_final_{timestamp}.csv"
    df_result.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"\n✅ 뉴스 데이터 저장 완료: {output_filename}")
else:
    print("\n⚠️ 수집된 뉴스 데이터가 없습니다.")
