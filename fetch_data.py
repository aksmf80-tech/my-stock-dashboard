import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os

def get_naver_data():
    """
    네이버 금융의 크롤링 차단 보안망을 우회하여 
    진짜 실시간 테마명, 대장 종목명, 등락률 정보를 완벽하게 수집합니다.
    """
    url = "https://finance.naver.com/sise/theme.nhn"
    
    # 🎯 [핵심 교정] 네이버 보안망을 속이기 위해 실제 크롬 브라우저와 똑같은 유저 에이전트 및 헤더 정보 주입
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://naver.com"
    }
    
    themes = []
    stocks = []
    rates = []
    
    # 1페이지부터 3페이지까지 안전하게 순회
    for page in range(1, 4):
        page_url = f"{url}?&page={page}"
        try:
            response = requests.get(page_url, headers=headers)
            response.encoding = 'euc-kr' # 네이버 한글 깨짐 원천 방어
            
            if response.status_code != 200:
                print(f"⚠️ 네이버 금융 {page}페이지 접속 실패 (Status Code: {response.status_code})")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 네이버 금융 테마 테이블의 데이터 행(tr)만 정확하게 저격
            rows = soup.select("#contentarea_left table.type_1 tr")
            
            for row in rows:
                cols = row.find_all("td")
                
                # 데이터가 실존하는 올바른 행만 필터링 (컬럼 수가 6개 이상)
                if len(cols) >= 6:
                    theme_tag = cols[0].find("a")
                    
                    # 진짜 테마 링크(themeId=)가 들어있는 행인지 검증
                    if theme_tag and "themeId=" in theme_tag.get('href', ''):
                        theme_name = theme_tag.text.strip()
                        
                        # 🎯 [등락률 수집 구조 정밀 교정]
                        # 네이버 테이블상 cols[1]은 전일대비 등락률 텍스트입니다.
                        rate_text = cols[1].text.strip()
                        rate_text = rate_text.replace('%', '').replace('+', '').replace(' ', '')
                        rate_text = rate_text.replace('\n', '').replace('\t', '').replace('\r', '')
                        
                        try:
                            rate = float(rate_text)
                        except ValueError:
                            continue
                            
                        # 🎯 [대장 종목 수집 구조 정밀 교정]
                        # 네이버 테이블상 cols[3]은 해당 테마의 주요 3개 종목이 콤마로 연결된 칸입니다.
                        stock_name = "종목 정보 없음"
                        if len(cols) > 3:
                            stock_tag = cols[3].find("a")
                            if stock_tag:
                                # 여러 종목 중 맨 첫 번째 대장 종목 한 개만 도려냅니다.
                                stock_name = stock_tag.text.strip()
                        
                        # 완벽하게 필터링된 데이터만 최종 저장소에 누적
                        if theme_name and stock_name != "종목 정보 없음" and theme_name != "":
                            themes.append(theme_name)
                            stocks.append(stock_name)
                            rates.append(rate)
                            
            time.sleep(0.5) # 네이버 블로킹 방지용 안전 딜레이 증가
            
        except Exception as e:
            print(f"❌ {page}페이지 크롤링 중 치명적 오류 발생: {e}")
            continue

    if not themes:
        print("❌ [경고] 네이버 보안망에 막혀 데이터를 한 줄도 파싱하지 못했습니다.")
        return None

    # 수집 완료 시각 계산
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {
        "테마": themes,
        "종목명": stocks,
        "등락률": rates,
        "업데이트시간": [now_time] * len(themes)
    }
    
    df = pd.DataFrame(data)
    
    # 중복 테마 완벽 제거 및 등락률 절댓값 기준 상위 15개 주도 테마 추출
    df = df.drop_duplicates(subset=['테마'])
    df['정렬용'] = df['등락률'].abs()
    df = df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
    return df

if __name__ == "__main__":
    print("🚀 실전 네이버 금융 크롤링 엔진 가동...")
    DATA_FILE = "theme_data.csv"
    try:
        df = get_naver_data()
        if df is not None and not df.empty:
            # 과거에 하드코딩으로 박아두었던 꼬인 가짜 파일을 완전히 삭제
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                print("🗑️ 가짜/구형 CSV 데이터를 완전히 파괴했습니다.")
                
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            print("🎉 [성공] 진짜 실시간 네이버 금융 데이터로 theme_data.csv 갱신 완료!")
            print(df.head(5)) # 잘 긁어왔는지 상위 5개 미리보기 출력
        else:
            print("⚠️ 파싱된 데이터프레임이 완전히 비어있습니다.")
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
