import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os

def get_naver_data():
    """
    네이버 금융 테마별 시세 페이지의 HTML 태그를 직접 저격하여
    정확한 테마명, 해당 테마의 등락률, 그리고 실전 대장주(3구역)를 정확히 매핑합니다.
    """
    url = "https://finance.naver.com/sise/theme.nhn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    themes = []
    stocks = []
    rates = []
    
    for page in range(1, 4):
        page_url = f"{url}?&page={page}"
        try:
            response = requests.get(page_url, headers=headers)
            response.encoding = 'euc-kr' # 네이버 한글 깨짐 원천 방어
            
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 🎯 [핵심 타겟팅] 네이버 테마 테이블의 데이터 tr만 정확하게 타겟팅합니다.
            rows = soup.select("#contentarea_left table.type_1 tr")
            
            for row in rows:
                cols = row.find_all("td")
                # 정상적인 데이터가 채워진 행은 컬럼 수가 최소 6개 이상입니다.
                if len(cols) >= 6:
                    theme_tag = cols[0].find("a")
                    
                    # 진짜 테마 주소(themeId)가 적힌 태그만 완벽하게 걸러냅니다.
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 🎯 [등락률 저격] 1번 td 칸의 순수 전일대비 등락률 텍스트만 추출
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue
                            
                        # 🎯 [대장주 저격] 네이버 테마 우측 배너가 아닌, 테이블 3구역(cols[5])에 실존하는 대장주를 파싱합니다.
                        stock_name = "종목 정보 없음"
                        if len(cols) > 5:
                            stock_tag = cols[5].find("a")
                            if stock_tag:
                                stock_name = stock_tag.text.strip()
                        
                        # 이상 없는 데이터셋만 최종 리스트에 누적
                        if theme_name and stock_name != "종목 정보 없음" and theme_name != "":
                            themes.append(theme_name)
                            stocks.append(stock_name)
                            rates.append(rate)
                            
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ {page}페이지 크롤링 치명적 오류: {e}")
            continue

    if not themes:
        return None

    # 데이터 프레임 빌드 및 상위 15개 가동 정렬
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {"테마": themes, "종목명": stocks, "등락률": rates, "업데이트시간": [now_time] * len(themes)}
    df = pd.DataFrame(data)
    
    df = df.drop_duplicates(subset=['테마'])
    df['정렬용'] = df['등락률'].abs()
    df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
    return df

if __name__ == "__main__":
    print("🚀 태그 저격형 GitHub Actions 수집기 가동...")
    DATA_FILE = "theme_data.csv"
    try:
        df = get_naver_data()
        if df is not None and not df.empty:
            # 유령 데이터의 잔재를 지우기 위해 무조건 선 삭제 후 재생성
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                print("🗑️ 저장소 내 구형 CSV 파일을 완전 파괴했습니다.")
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            print("🎉 [성공] 완전히 정제된 실시간 theme_data.csv 갱신 완료!")
            print(df.head(5))
        else:
            print("⚠️ 파싱 결과가 비어있습니다.")
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
