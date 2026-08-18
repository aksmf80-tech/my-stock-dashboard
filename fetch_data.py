import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time

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
                    theme_tag = cols[0].find("a")
                    
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 🎯 [수정 1] 실제 테마 등락률은 cols[1] 칸의 텍스트에 들어있습니다.
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '').replace('\n', '').replace('\t', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue
                            
                        # 🎯 [수정 2] 해당 행 내부(cols[0]~cols[3])가 아닌, 3구역(cols[5])에 배치된 실제 테마 내 대장 종목을 가져옵니다.
                        stock_name = "종목 정보 없음"
                        if len(cols) > 5:
                            stock_tag = cols[5].find("a")
                            if stock_tag:
                                stock_name = stock_tag.text.strip()
                        
                        # 예외 방어: 만약 데이터를 정상적으로 추출했다면 리스트에 추가
                        if theme_name and stock_name != "종목 정보 없음":
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
    
    # 🎯 [수정 3] 주도력 기준 정렬 후 상위 15개 추출 (중복 제거 포함)
    df = df.drop_duplicates(subset=['테마'])
    df['정렬용'] = df['등락률'].abs()
    df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
    return df

if __name__ == "__main__":
    print("🚀 GitHub Actions 수집기 기동...")
    try:
        df = get_naver_data()
        
        if df is not None and not df.empty:
            df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
            print("🎉 [성공] theme_data.csv 갱신 완료!")
            print(df.head(5)) # 로그로 상위 5개 데이터 미리보기 출력
        else:
            print("⚠️ 수집된 데이터가 없습니다.")
            
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
