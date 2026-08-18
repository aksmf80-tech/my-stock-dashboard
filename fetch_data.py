import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지를 크롤링하여 
    전체 테마명, 대장 종목명, 등락률 정보를 수집합니다.
    """
    url = "https://naver.com"
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
                
                # 데이터가 존재하는 행인지 확실하게 검증 (주요 td 크기 조건 추가)
                if len(cols) >= 6:
                    # 첫 번째 td(cols[0]) 안에서 테마명 태그를 안전하게 찾습니다.
                    theme_tag = cols[0].find("a")
                    
                    # 진짜 테마 주소가 포함된 유효한 행만 필터링
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 1. 등락률 추출 및 숫자로 정제 (두 번째 td인 cols[1]에 위치)
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '').replace('\n', '').replace('\t', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue
                            
                        # 2. 대장주 추출 (종목코드 링크 탐색)
                        stock_name = "종목 정보 없음"
                        for col in cols[4:]:
                            stock_tag = col.find("a")
                            if stock_tag and "item.nhn?code=" in stock_tag.get('href', ''):
                                stock_name = stock_tag.text.strip()
                                break
                        
                        themes.append(theme_name)
                        stocks.append(stock_name)
                        rates.append(rate)
                        
            time.sleep(0.2) # 서버 과부하 방지 딜레이
            
        except Exception as e:
            print(f"❌ {page}페이지 크롤링 중 오류 발생: {e}")
            continue

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

if __name__ == "__main__":
    print("🚀 GitHub Actions 수집기 기동...")
    try:
        df = get_naver_data()
        
        if df is not None and not df.empty:
            df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
            print("🎉 [성공] theme_data.csv 갱신 완료!")
        else:
            print("⚠️ 수집된 데이터가 없습니다.")
            
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
