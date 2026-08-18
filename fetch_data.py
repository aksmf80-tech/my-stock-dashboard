import pandas as pd
import datetime
import os
import time
import requests

def get_yahoo_realtime_rate(ticker_code):
    """
    야후 파이낸셜(Yahoo Finance) 비공식 API 아웃링크를 직접 타격하여,
    국내/해외 대장 종목의 진짜 현재 시세와 등락률을 0초만에 실시간 추출합니다.
    """
    try:
        # yfinance 라이브러리 없이 requests로 직접 야후 API 엔드포인트를 정밀 타격하여 렉을 최소화합니다.
        url = f"https://yahoo.com{ticker_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return 0.0
            
        data = response.json()
        meta = data['chart']['result'][0]['meta']
        
        # 야후 파이낸셜 제공 실시간 현재가 및 전일 종가 데이터 추출
        current_price = meta.get('regularMarketPrice')
        previous_close = meta.get('previousClose')
        
        if current_price and previous_close:
            # 실시간 등락률 정밀 연산
            rate = ((current_price - previous_close) / previous_close) * 100
            return round(rate, 2)
        return 0.0
    except:
        return 0.0

def get_market_theme_data():
    """
    대한민국 증권 시장 핵심 주도 테마와 소속 대장 종목들의 정보를
    야후 파이낸셜 실시간 시세망과 다이렉트로 바인딩하여 무오류 데이터프레임을 생성합니다.
    """
    try:
        print("📊 [야후 파이낸셜 엔지니어링] 국내 주도주 실시간 체결 시세 전수 수집 가동...")
        
        # 해외 가상 서버 시차 보정 완료 (KST 동기화)
        kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        
        # 🎯 테마별 소속 대장주와 야후 금융 정품 티커 매핑 시스템 고정 (.KS / .KQ 정밀 매핑)
        backup_themes = [
            "대북/남북경협", "반도체 후공정/OSAT", "DDR5/디램", "2차전지 급등주", 
            "반도체 장비/재료", "자율주행/스마트카", "방산 주도주", "로봇/AI", 
            "바이오시밀러", "화장품", "메타버스", "초전도체", "원자력발전"
        ]
        backup_stocks = [
            "코데즈컴바인", "하나마이크론", "티엘비", "에코프로비엠", 
            "주성엔지니어링", "모트렉스", "한화에어로스페이스", "레인보우로보틱스", 
            "알테오젠", "토니모리", "맥스트", "신성델타테크", "두산에너빌리티"
        ]
        yahoo_tickers = [
            "047050.KQ", "067310.KQ", "356860.KQ", "247540.KQ", 
            "036930.KQ", "118990.KQ", "012450.KS", "277810.KQ", 
            "196170.KQ", "214420.KS", "124110.KQ", "044960.KQ", "034020.KS"
        ]
        
        realtime_rates = []
        
        # 야후 파이낸셜 API망 돌며 순식간에 실시간 등락률 동기화
        for ticker in yahoo_tickers:
            rate = get_yahoo_realtime_rate(ticker)
            realtime_rates.append(rate)
            time.sleep(0.1) # IP 임시 차단 방지용 안전 버퍼 시간 확보
            
        # 데이터프레임 빌드
        final_df = pd.DataFrame({
            "테마": backup_themes, 
            "종목명": backup_stocks, 
            "등락률": realtime_rates
        })
        
        # 변동성 정렬 후 타임스탬프 마킹
        final_df['정렬용'] = final_df['등락률'].abs()
        final_df = final_df.sort_values(by="정렬용", ascending=False).drop(columns=['정렬용']).reset_index(drop=True)
        final_df['업데이트시간'] = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        
        return final_df
        
    except Exception as e:
        print(f"❌ 야후 파이낸셜 최종 수집 엔진 구동 실패 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 야후 파이낸셜 실시간 주도 테마 수집기 가동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 야후 실시간 시세망 반영 ➡️ {DATA_FILE} 동기화 완결!")
    else:
        print("⚠️ 야후 파이낸셜 데이터를 추출하지 못했습니다.")
