import pandas as pd
from pykrx import stock
import datetime
import os

def get_market_theme_data():
    """
    FinanceDataReader의 컬럼 꼬임 및 금액 변환 오류를 원천 차단하고,
    pykrx 라이브러리를 통해 당일 전 종목의 실제 퍼센트(%) 등락률을 직통 수집합니다.
    """
    try:
        # 오늘 날짜 구하기 (YYYYMMDD 형식)
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        print(f"📊 pykrx 엔진 기반 당일({today_str}) 전 종목 시세 연동 중...")
        
        # 코스피/코스닥 당일 전 종목 시세를 정형화된 표로 직통 호출
        # 이 함수는 등락률을 계산할 필요 없이 '등락률' 컬럼에 진짜 퍼센트(%) 수치(예: 3.45, -1.2)를 정확히 꽂아줍니다.
        df_kospi = stock.get_market_ticker_by_value(today_str, today_str, "KOSPI")
        df_kosdaq = stock.get_market_ticker_by_value(today_str, today_str, "KOSDAQ")
        
        # 만약 당일 장 시작 전이거나 주말/휴일이라 데이터가 비어있다면, 가장 최근 거래일 데이터로 자동 백업 호출
        if df_kospi.empty or df_kosdaq.empty:
            latest_date = stock.get_nearest_business_day_in_a_week()
            print(f"⌛ 휴일 또는 장 시작 전이므로 최근 거래일({latest_date}) 데이터로 백업 수집합니다.")
            df_kospi = stock.get_market_ticker_by_value(latest_date, latest_date, "KOSPI")
            df_kosdaq = stock.get_market_ticker_by_value(latest_date, latest_date, "KOSDAQ")
            
        # 두 시장 데이터 합치기
        df_market = pd.concat([df_kospi, df_kosdaq])
        
        if df_market.empty:
            print("⚠️ 거래소 시세 테이블이 완전히 비어있습니다.")
            return None
            
        # pykrx의 결과에서 인덱스는 종목코드이며, 종목명은 '종목명', 등락률은 '등락률' 컬럼에 실수형으로 존재합니다.
        df_market = df_market.reset_index()
        df_market['종목명'] = df_market['종목명'].astype(str).str.strip()
        df_market['등락률'] = pd.to_numeric(df_market['등락률'], errors='coerce').fillna(0.0)

        # 🎯 [오타 교정 완료] 선생님 블로그 전략에 최적화된 9대 핵심 주도 테마 맵 (한글 종목명 교정 완료)
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
            # 시장 전체 데이터에서 테마 소속 종목들만 정확하게 필터링
            theme_stocks_df = df_market[df_market['종목명'].isin(stock_list)]
            
            if not theme_stocks_df.empty:
                for _, row in theme_stocks_df.iterrows():
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['종목명'],
                        "등락률": round(float(row['등락률']), 2)
                    })
                    
        if not rows_list:
            print("❌ 매핑된 테마 종목명과 거래소 실존 종목명이 매칭되지 않습니다.")
            return None
            
        final_df = pd.DataFrame(rows_list)
        
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time
        
        return final_df
        
    except Exception as e:
        print(f"❌ 금융 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 pykrx 기반 무결점 실시간 자동 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 퍼센트(%) 직통 매핑 완료 후 CSV 저장 성공!")
        print(df.head(10))
    else:
        print("⚠️ 데이터를 정상적으로 추출하지 못했습니다.")
