import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지를 크롤링하여 
    전체 테마명, 해당 테마의 주도 종목명, 실제 테마 등락률 정보를 정확하게 수집합니다.
    """
    url = "https://finance.naver.com/sise/theme.nhn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    themes = []
    stocks = []
    rates = []
    
    # 안전하게 1페이지부터 3페이지까지 수집합니다.
    for page in range(1, 4):
        page_url = f"{url}?&page={page}"
        try:
            response = requests.get(page_url, headers=headers)
            response.encoding = 'euc-kr' # 네이버 금융 한글 깨짐 방지
            
            if response.status_code != 200:
                print(f"⚠️ 네이버 금융 {page}페이지 접속 실패")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "type_1"})
            
            if not table:
                continue
                
            rows = table.find_all("tr")
            
            for row in rows:
                cols = row.find_all("td")
                
                # 네이버 테마 테이블의 올바른 데이터 행 컬럼 수는 보통 7~8개입니다.
                if len(cols) >= 6:
                    theme_tag = cols[0].find("a") # 0번 인덱스에서 테마 태그 탐색
                    
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 🎯 [정밀 정정] 실제 테마 등락률은 1번 인덱스 칸의 텍스트에 들어있습니다.
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '').replace('\n', '').replace('\t', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue
                            
                        # 🎯 [정밀 정정] 5번 인덱스(3구역)에 배치된 실제 테마 내 대장 종목을 정확하게 맵핑합니다.
                        stock_name = "종목 정보 없음"
                        if len(cols) > 5:
                            stock_tag = cols[5].find("a")
                            if stock_tag:
                                stock_name = stock_tag.text.strip()
                        
                        # 데이터를 완벽하게 추출한 경우에만 리스트에 추가
                        if theme_name and stock_name != "종목 정보 없음" and theme_name != "":
                            themes.append(theme_name)
                            stocks.append(stock_name)
                            rates.append(rate)
                        
            time.sleep(0.2) # 서버 과부하 방지 딜레이
            
        except Exception as e:
            print(f"❌ {page}페이지 크롤링 중 오류 발생: {e}")
            continue

    if not themes:
        return None

    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {
        "테마": themes,
        "종목명": stocks,
        "등락률": rates,
        "업데이트시간": [now_time] * len(themes)
    }
    
    df = pd.DataFrame(data)
    
    # 🎯 중복 제거 및 주도력 기준 상위 15개 테마 추출
    df = df.drop_duplicates(subset=['테마'])
    df['정렬용'] = df['등락률'].abs()
    df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
    return df

if __name__ == "__main__":
    print("🚀 GitHub Actions 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    try:
        df = get_naver_data()
        
        if df is not None and not df.empty:
            # 🎯 [버그 해결] 기존에 꼬여있던 쓰레기 데이터를 완전히 지워버리기 위해 파일을 강제 삭제 후 재생성합니다.
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                print("🗑️ 기존 꼬여있던과거 CSV 파일을 완전히 삭제했습니다.")
                
            # 완전히 깨끗해진 상태에서 새 데이터만 기록합니다.
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            print("🎉 [성공] 완전히 새로운 테마 데이터로 갱신 완료!")
            print(df.head(5)) # 로그 출력으로 데이터 정상 변동 확인
        else:
            print("⚠️ 수집된 데이터가 없습니다.")
            
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
