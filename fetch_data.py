import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import os
import time

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지(여러 페이지)를 크롤링하여 
    전체 테마명, 대장 종목명, 등락률 정보를 수집합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    themes = []
    stocks = []
    rates = []
    
    # 안전하게 상위 3페이지(테마 약 120개)까지 돌며 수집 (전체 수집을 원하면 범위를 늘리세요)
    for page in range(1, 4):
        url = f"https://finance.naver.com/sise/theme.nhn?&page={page}"
        
        try:
            response = requests.get(url, headers=headers)
            response.encoding = 'euc-kr' # 네이버 금융 한글 깨짐 방지
            
            if response.status_code != 200:
                print(f"⚠️ 네이버 금융 {page}페이지 접속 실패")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "type_1"})
            
            if not table:
                # 더 이상 페이지가 없으면 루프 종료
                break
                
            rows = table.find_all("tr")
            
            for row in rows:
                cols = row.find_all("td")
                
                # 데이터가 들어있는 유효한 행인지 필터링 (주요 데이터 열 크기 검증)
                if len(cols) >= 5:
                    theme_name_tag = cols[0].find("a")
                    if theme_name_tag:
                        theme_name = theme_name_tag.text.strip()
                        
                        # 1. 등락률 추출 및 정제 (cols[1])
                        rate_text = cols[1].text.strip()
                        # 공백, %, + 기호 제거 (마이너스 기호 '-'는 유지)
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '').replace('\n', '').replace('\t', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue # 숫자로 변환 불가능한 행은 스킵
                            
                        # 2. 대장주 추출 (실제 구조상 cols[4]에 위치)
                        stock_name = "종목 정보 없음"
                        stock_tag = cols[4].find("a")
                        if stock_tag:
                            stock_name = stock_tag.text.strip()
                        
                        themes.append(theme_name)
                        stocks.append(stock_name)
                        rates.append(rate)
            
            # 서버 과부하 방지를 위한 미세한 딜레이
            time.sleep(0.3)
            
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
            # 일회성으로 깔끔하게 csv 파일을 생성하고 프로그램을 종료합니다.
            df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
            print("🎉 [성공] theme_data.csv 갱신 완료!")
            print(df.head(5)) # 상위 5개 데이터 미리보기 출력
        else:
            print("⚠️ 수집된 데이터가 없습니다. 주소를 다시 확인하거나 장 시간인지 확인하세요.")
            
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
