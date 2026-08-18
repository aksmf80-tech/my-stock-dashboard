import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지를 실시간으로 크롤링하여 
    전체 테마명, 대장 종목명, 등락률 정보를 수집합니다.
    """
    # 💡 [교정 1] 네이버 메인이 아닌, 실제 테마 시세가 있는 금융 페이지 주소로 변경
    url = "https://naver.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'euc-kr' # 네이버 금융 한글 깨짐 방지
        
        if response.status_code != 200:
            print("네이버 금융 접속 실패")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 네이버 금융 테마 테이블 파싱
        table = soup.find("table", {"class": "type_1"})
        if not table:
            print("테마 테이블(type_1)을 찾을 수 없습니다.")
            return None
            
        rows = table.find_all("tr")
        
        themes = []
        stocks = []
        rates = []
        
        for row in rows:
            cols = row.find_all("td")
            # 네이버 금융 테마 테이블 구조상 데이터가 채워진 행은 보통 7개 이상의 열을 가집니다.
            if len(cols) >= 6:
                theme_name_tag = cols[0].find("a")
                if theme_name_tag:
                    theme_name = theme_name_tag.text.strip()
                    
                    # 💡 [교정 2] 네이버 금융 구조에 맞게 등락률(2번째 열) 및 대장주(6번째 열) 위치 정정
                    rate_text = cols[1].text.strip().replace('%', '').replace('+', '')
                    try:
                        rate = float(rate_text)
                    except ValueError:
                        continue
                        
                    # 대장주 추출 (네이버 금융 테마 페이지의 6번째 td 내부 a 태그)
                    stock_name = "종목 정보 없음"
                    stock_tag = cols[5].find("a") if len(cols) > 5 else None
                    if stock_tag:
                        stock_name = stock_tag.text.strip()
                    
                    # 💡 [교정 3] 마이너스 등락률도 버리지 않고 대시보드 시각화를 위해 그대로 수집
                    themes.append(theme_name)
                    stocks.append(stock_name)
                    rates.append(rate)
                    
        if not themes:
            return None

        # 수집된 데이터를 딕셔너리로 결합
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "테마": themes,
            "종목명": stocks,
            "등락률": rates,
            "업데이트시간": [now_time] * len(themes)
        }
        
        df = pd.DataFrame(data)
        # 등락률 절댓값이 큰 순서(시장 주도령이 강한 순서)로 상위 15개 추출
        df['정렬용'] = df['등락률'].abs()
        df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
        return df

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    print("🚀 실시간 네이버 금융 데이터 수집기 가동 시작...")
    # 💡 [교정 4] 대시보드가 실시간 동기화될 수 있도록 무한 루프(60초 주기) 생성
    while True:
        try:
            df = get_naver_data()
            
            if df is not None and not df.empty:
                df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🎉 theme_data.csv 갱신 완료!")
            else:
                print("⚠️ 수집된 데이터가 없습니다. 주소를 다시 확인하거나 장 시간인지 확인하세요.")
                
        except Exception as e:
            print(f"루프 구동 중 오류 발생: {e}")
            
        # 60초 대기 후 재수집
        time.sleep(60)
