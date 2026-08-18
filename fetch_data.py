import pandas as pd
import datetime
import os
import time
import yfinance as yf # yfinance 사용으로 안정성 확보

def get_yahoo_realtime_rate(ticker_code):
    """
    yfinance 라이브러리를 사용하여 안정적으로 실시간 등락률을 추출합니다.
    """
    try:
        ticker = yf.Ticker(ticker_code)
        # fast_info를 사용하면 불필요한 네트워크 요청 없이 빠르게 데이터를 가져옵니다.
        info = ticker.fast_info
        
        current_price = info.last_price
        previous_close = info.previous_close
        
        if current_price and previous_close:
            rate = ((current_price - previous_close) / previous_close) * 100
            return round(rate, 2)
        return 0.0
    except Exception as e:
        print(f"❌ 티커 {ticker_code} 수집 에러: {e}")
        return 0.0

def get_market_theme_data():
    """
    국내 테마 대장주 데이터를 수집하여 데이터프레임을 생성합니다.
    """
    print("📊 [yfinance 엔진] 실시간 시세 수집 가동...")
    
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    
    backup_themes = [
        "대북/남북경협", "반도체 후공정/OSAT", "DDR5/디램", "2차전지 급등주", 
        "반도체 장비/재료", "자율주행/스마트카", "방산 주도주", "로봇/AI", 
        "바이오시밀러", "화장품", "메타버스", "초전도체", "원자력발전"
    ]
    yahoo_tickers = [
        "047050.KQ", "067310.KQ", "356860.KQ", "247540.KQ", 
        "036930.KQ", "118990.KQ", "012450.KS", "277810.KQ", 
        "196170.KQ", "214420.KS", "124110.KQ", "044960.KQ", "034020.KS"
    ]
    
    realtime_rates = []
    
    for ticker in yahoo_tickers:
        rate = get_yahoo_realtime_rate(ticker)
        realtime_rates.append(rate)
        time.sleep(0.2) # 조금 더 안전한 버퍼 추가
            
    final_df = pd.DataFrame({
        "테마": backup_themes, 
        "종목명": ["코데즈컴바인", "하나마이크론", "티엘비", "에코프로비엠", "주성엔지니어링", "모트렉스", "한화에어로스페이스", "레인보우로보틱스", "알테오젠", "토니모리", "맥스트", "신성델타테크", "두산에너빌리티"], 
        "등락률": realtime_rates
    })
    
    final_df['정렬용'] = final_df['등락률'].abs()
    final_df = final_df.sort_values(by="정렬용", ascending=False).drop(columns=['정렬용']).reset_index(drop=True)
    final_df['업데이트시간'] = kst_now.strftime('%Y-%m-%d %H:%M:%S')
    
    return final_df

if __name__ == "__main__":
    DATA_FILE = "theme_data.csv"
    df = get_market_theme_data()
    if df is not None:
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 실시간 데이터 동기화 완료!")
