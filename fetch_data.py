import pandas as pd
import datetime
import time
import yfinance as yf

def get_yahoo_stock_data(ticker_code):
    """
    yfinance를 통해 실시간 등락률과 거래대금(시가총액/활성도 가중치)을 동시에 추출합니다.
    """
    try:
        ticker = yf.Ticker(ticker_code)
        info = ticker.fast_info
        
        current_price = info.last_price
        previous_close = info.previous_close
        last_volume = info.last_volume
        
        rate = 0.0
        if current_price and previous_close:
            rate = round(((current_price - previous_close) / previous_close) * 100, 2)
            
        # 거래대금 산출 (가격 * 거래량, 데이터가 없으면 기본값 부여)
        trading_value = (current_price * last_volume) if (current_price and last_volume) else 1000000000
        
        return rate, trading_value
    except Exception as e:
        print(f"❌ 티커 {ticker_code} 수집 에러: {e}")
        return 0.0, 1000000000

def get_market_theme_data():
    print("📊 [핀업 고도화 엔진] 실시간 시세 및 거래대금 전수 수집 가동...")
    
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    
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
    realtime_values = []
    
    for ticker in yahoo_tickers:
        rate, t_val = get_yahoo_stock_data(ticker)
        realtime_rates.append(rate)
        realtime_values.append(t_val)
        time.sleep(0.2)
            
    final_df = pd.DataFrame({
        "테마": backup_themes, 
        "종목명": backup_stocks, 
        "등락률": realtime_rates,
        "거래대금": realtime_values
    })
    
    # 핀업 스타일 트리맵 사각형 크기 가중치 계산 (절대 등락률 + 거래대금 로그 스케일 조합)
    import numpy as np
    final_df['정렬용'] = final_df['등락률'].abs()
    final_df['화면크기_가중치'] = final_df['정렬용'] + np.log1p(final_df['거래대금']) / 2.0
    
    final_df = final_df.sort_values(by="화면크기_가중치", ascending=False).reset_index(drop=True)
    final_df['업데이트시간'] = kst_now.strftime('%Y-%m-%d %H:%M:%S')
    
    return final_df

if __name__ == "__main__":
    DATA_FILE = "theme_data.csv"
    df = get_market_theme_data()
    if df is not None:
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 핀업 고도화 데이터 동기화 완결!")
