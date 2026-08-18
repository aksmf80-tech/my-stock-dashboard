import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import os

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지를 크롤링하여 
    전체 테마명, 대장 종목명, 등락률 정보를 수집합니다.
    """
    # 💡 [정석 주소] 실제 테마 시세 데이터가 위치한 네이버 금융 경로
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
            # 네이버 금융 테마 테이블 구조상 데이터 행은 6개 이상의 td를 가집니다.
            if len(cols) >= 6:
                theme_name_tag = cols[0].find("a")
                if theme_name_tag:
                    theme_name = theme_name_tag.text.strip()
                    
                    # 등락률 추출 (두 번째 열)
                    rate_text = cols[1].text.strip().replace('%', '').replace('+', '')
                    try:
                        rate = float(rate_text)
                    except ValueError:
                        continue
                        
                    # 대장주 추출 (여섯 번째 열)
                    stock_name = "종목 정보 없음"
                    stock_tag = cols[5].find("a")
                    if stock_tag:
                        stock_name = stock_tag.text.strip()
                    
                    # 마이너스 등락률도 정상 수집 (대시보드에서 절댓값 보정 처리함)
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
        # 시장 주도력(등락률 절댓값 변동 폭)이 큰 순서대로 상위 15개 추출
        df['정렬용'] = df['등락률'].abs()
        df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
        return df

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    print("🚀 GitHub Actions 수집기 기동...")
    try:
        df = get_naver_data()
        
        if df is not None and not df.empty:
            # 💡 일회성으로 깔끔하게 csv 파일을 생성하고 프로그램을 종료합니다.
            df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
            print("🎉 [성공] theme_data.csv 갱신 완료!")
        else:
            print("⚠️ 수집된 데이터가 없습니다. 주소를 다시 확인하거나 장 시간인지 확인하세요.")
            
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
