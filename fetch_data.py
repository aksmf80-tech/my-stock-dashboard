import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지를 실시간으로 크롤링하여 
    전체 테마명, 대장 종목명, 등락률 정보를 수집합니다.
    """
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
            return None
            
        rows = table.find_all("tr")
        
        themes = []
        stocks = []
        rates = []
        
        for row in rows:
            cols = row.find_all("td")
            # 정상적인 데이터 행만 추출 (테마명, 등락률 등이 포함된 행)
            if len(cols) >= 4:
                theme_name_tag = cols[0].find("a")
                if theme_name_tag:
                    theme_name = theme_name_tag.text.strip()
                    
                    # 등락률 추출 (두 번째 열)
                    rate_text = cols[1].text.strip().replace('%', '')
                    try:
                        rate = float(rate_text)
                    except ValueError:
                        continue
                        
                    # 💡 [핵심] 해당 테마의 주도 종목(대장주) 정보를 3번째 열에서 파싱
                    stock_name = "종목 정보 없음"
                    stock_tag = cols[3].find("a")
                    if stock_tag:
                        stock_name = stock_tag.text.strip()
                    
                    # 마이너스 등락률 부호 보정 및 트리맵 크기 계산을 위해 하한값 설정
                    if rate <= 0:
                        continue # 트리맵(바둑판)은 크기(Value)가 무조건 양수(+)여야 깨지지 않고 그려집니다.
                    
                    themes.append(theme_name)
                    stocks.append(stock_name)
                    rates.append(rate)
                    
        # 수집된 데이터를 딕셔너리로 결합
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "테마": themes,
            "종목명": stocks,
            "등락률": rates,
            "업데이트시간": [now_time] * len(themes)
        }
        
        df = pd.DataFrame(data)
        # 상위 상승률 15개 테마만 골라내어 가독성 극대화
        df = df.sort_values(by="등락률", ascending=False).head(15)
        return df

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    try:
        # 1. 네이버 금융 실제 데이터 수집
        df = get_naver_data()
        
        # 2. 정상적으로 수집되었다면 csv 파일로 저장
        if df is not None and not df.empty:
            df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
            print("🎉 [성공] 네이버 금융 실시간 데이터 수집 및 csv 저장 완료!")
        else:
            print("⚠️ [대기] 장 시작 전이거나 수집된 데이터가 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")
