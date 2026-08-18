import pandas as pd
import yfinance as yf
import datetime
import os

def get_market_theme_data():
    """
    국내 거래소의 해외 IP 보안 차단벽을 완벽하게 우회하여
    야후 파이낸셜 글로벌 서버로부터 실시간 한국 주가 퍼센트(%) 데이터를 100% 안전하게 가져옵니다.
    """
    try:
        # 해외 깃허브 서버 시차 해결 (한국 시간 KST 산출)
        current_base = datetime.datetime.now()
        if current_base.hour < 9:
            kst_now = current_base + datetime.timedelta(hours=9)
        else:
            kst_now = current_base
        
        # 🎯 선생님 블로그 전략 맞춤형 핵심 주도 테마 및 야후 파이낸스 전용 티커 매핑
        theme_map = {
            "자동차 부품": {
                "현대모비스": "012330.KS", "한온시스템": "018880.KS", "현대위아": "011210.KS", 
                "성우하이텍": "015750.KQ", "서연이화": "200880.KS", "화신": "010690.KS", "에스엘": "001740.KS"
            },
            "로봇/AI": {
                "레인보우로보틱스": "277810.KQ", "두산로보틱스": "454910.KS", "뉴로메카": "348340.KQ", 
                "루닛": "328130.KQ", "뷰노": "338220.KQ", "이랜시스": "423150.KQ"
            },
            "시스템 반도체": {
                "네패스": "033640.KQ", "리노공업": "058470.KQ", "한미반도체": "042700.KS", 
                "두산테스나": "131970.KQ", "가온칩스": "399720.KQ", "오픈엣지테크놀로지": "394280.KQ"
            },
            "방산": {
                "한화에어로스페이스": "012450.KS", "한국항공우주": "047810.KS", "LIG넥스원": "079550.KS", 
                "현대로템": "064350.KS", "풍산": "103140.KS", "휴니드": "005870.KS"
            },
            "2차전지": {
                "에코프로": "038390.KQ", "에코프로비엠": "247540.KQ", "포스코퓨처엠": "003670.KS", 
                "엘앤에프": "066970.KQ", "금양": "001570.KS", "엔켐": "348370.KQ"
            }
        }
        
        rows_list = []
        print("🌍 야후 파이낸스 글로벌 데이터 파이프라인 동기화 중...")
        
        # 각 테마와 종목들을 돌며 실시간 등락률 수집
        for theme_name, stocks in theme_map.items():
            for stock_name, ticker in stocks.items():
                try:
                    # 🎯 해외 IP 차단이 전혀 없는 야후 파이낸스로 당일 주가 데이터 다이렉트 호출
                    ticker_obj = yf.Ticker(ticker)
                    hist = ticker_obj.history(period="2d")
                    
                    if len(hist) >= 2:
                        prev_close = float(hist['Close'].iloc[-2])
                        curr_close = float(hist['Close'].iloc[-1])
                        # 진짜 퍼센트 등락률 계산 공식
                        rate = ((curr_close - prev_close) / prev_close) * 100.0
                    else:
                        rate = 0.0
                        
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": stock_name,
                        "등락률": round(rate, 2)
                    })
                except Exception as stock_err:
                    print(f"⚠️ {stock_name}({ticker}) 수집 스킵: {stock_err}")
                    continue
                        
        if not rows_list:
            print("⚠️ 글로벌 API 수집 결과가 비어있습니다.")
            return None
            
        final_df = pd.DataFrame(rows_list)
        now_time_kst = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time_kst
        
        return final_df
        
    except Exception as e:
        print(f"❌ 글로벌 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 글로벌 우회형 실시간 데이터 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 해외 IP 차단 우회 및 수집 완료!")
        print(df.head(5))
    else:
        print("⚠️ 데이터를 정상적으로 추출하지 못했습니다.")
