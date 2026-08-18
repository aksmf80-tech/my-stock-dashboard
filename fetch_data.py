import pandas as pd
from pykrx import stock
import datetime
import os

def get_market_theme_data():
    """
    pykrx 장중 스냅샷의 등락률 누락 버그를 완벽히 해결하기 위해
    [ (현재가 - 전일종가) / 전일종가 * 100 ] 공식을 활용해 진짜 등락률을 강제 정밀 역산합니다.
    """
    try:
        current_base = datetime.datetime.now()
        if current_base.hour < 9:
            kst_now = current_base + datetime.timedelta(hours=9)
        else:
            kst_now = current_base
            
        today_str = kst_now.strftime("%Y%m%d")
        print(f"📊 pykrx 장중 실시간 강제 역산 엔진 가동 (기준일: {today_str})...")
        
        # 🎯 [0.0 버그 완전 박멸 핵심]
        # 등락률 컬럼이 비어있을 때를 대비해, 거래소 종가(현재가)와 전일대비 변동폭 데이터를 함께 긁어옵니다.
        df_kospi = stock.get_market_snapshot_by_ticker("KOSPI")
        df_kosdaq = stock.get_market_snapshot_by_ticker("KOSDAQ")
        
        if df_kospi.empty or df_kosdaq.empty:
            latest_date = stock.get_nearest_business_day_in_a_week()
            print(f"⌛ 휴일 또는 장 개시 전입니다. 최근 마감일({latest_date}) 시세로 전환합니다.")
            df_kospi = stock.get_market_price_change_by_ticker(latest_date, latest_date, "KOSPI")
            df_kosdaq = stock.get_market_price_change_by_ticker(latest_date, latest_date, "KOSDAQ")
            
        df_market = pd.concat([df_kospi, df_kosdaq])
        
        if df_market.empty:
            print("⚠️ 거래소 시세 테이블이 완전히 비어있습니다.")
            return None
            
        df_market = df_market.reset_index()
        
        # 종목명 컬럼 정제
        if '종목명' not in df_market.columns:
            df_market['종목명'] = df_market.iloc[:, 1].astype(str).str.strip()
        else:
            df_market['종목명'] = df_market['종목명'].astype(str).str.strip()
            
        # 🎯 [진짜 등락률 공식 강제 연동]
        # 라이브러리가 등락률을 0.0으로 뱉더라도, '종가(현재가)'와 '대비(변동금액)' 컬럼을 이용해 진짜 %를 직접 계산합니다.
        # 공식: (변동금액 / (현재가 - 변동금액)) * 100
        df_market['현재가'] = pd.to_numeric(df_market['종가'], errors='coerce').fillna(0)
        df_market['변동금액'] = pd.to_numeric(df_market['대비'], errors='coerce').fillna(0)
        df_market['전일종가'] = df_market['현재가'] - df_market['변동금액']
        
        df_market['진짜등락률'] = 0.0
        mask = df_market['전일종가'] > 0
        df_market.loc[mask, '진짜등락률'] = (df_market.loc[mask, '변동금액'] / df_market.loc[mask, '전일종가']) * 100.0

        theme_map = {
            "자동차 부품": ["현대모비스", "한온시스템", "현대위아", "성우하이텍", "서연이화", "화신", "에스엘"],
            "로봇/AI": ["레인보우로보틱스", "두산로보틱스", "뉴로메카", "루닛", "뷰노", "이랜시스", "RS오토메이션"],
            "시스템 반도체": ["네패스", "리노공업", "한미반도체", "두산테스나", "가온칩스", "오픈엣지테크놀로지"],
            "방산": ["한화에어로스페이스", "한국항공우주", "LIG넥스원", "현대로템", "풍산", "휴니드"],
            "2차전지": ["에코프로", "에코프로비엠", "포스코퓨처엠", "엘앤에프", "금양", "나노신소재", "엔켐"],
            "초전도체": ["신성델타테크", "파워로직스", "서남", "덕성", "모비스", "씨씨에스"],
            "원자력 발전": ["두산에너빌리티", "우진", "보성파워텍", "일진파워", "한신기계", "에너토크"],
            "우주항공": ["한국항공우주", "컨텍", "인텔리안테크", "AP위성", "제노코", "한화시스템"],
            "바이오시밀러": ["셀트리온", "삼성바이오로직스", "한미약품", "유한양행", "알테오젠", "에이치엘비"]
        }
        
        rows_list = []
        
        for theme_name, stock_list in theme_map.items():
            theme_stocks_df = df_market[df_market['종목명'].isin(stock_list)]
            
            if not theme_stocks_df.empty:
                for _, row in theme_stocks_df.iterrows():
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['종목명'],
                        "등락률": round(float(row['진짜등락률']), 2)
                    })
                    
        if not rows_list:
            return None
            
        final_df = pd.DataFrame(rows_list)
        
        now_time_kst = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time_kst
        
        return final_df
        
    except Exception as e:
        print(f"❌ 금융 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 pykrx 장중 실시간 강제 역산형 엔진 구동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 수식 계산 완료 후 CSV 저장 성공!")
        print(df.head(5))
    else:
        print("⚠️ 데이터를 정상적으로 추출하지 못했습니다.")
