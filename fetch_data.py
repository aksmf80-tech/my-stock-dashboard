import pandas as pd
from pykrx import stock
import datetime
import os

def get_market_theme_data():
    """
    장중 pykrx 소수점 배수 등락률 데이터를 100을 곱해 진짜 퍼센트(%) 수치로 완벽하게 변환합니다.
    """
    try:
        current_base = datetime.datetime.now()
        if current_base.hour < 9:
            kst_now = current_base + datetime.timedelta(hours=9)
        else:
            kst_now = current_base
            
        today_str = kst_now.strftime("%Y%m%d")
        print(f"📊 pykrx 장중 실시간 스냅샷 엔진 가동 (기준일: {today_str})...")
        
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
        
        if '종목명' not in df_market.columns:
            df_market['종목명'] = df_market.iloc[:, 1].astype(str).str.strip()
        else:
            df_market['종목명'] = df_market['종목명'].astype(str).str.strip()
            
        if '등락률' in df_market.columns:
            df_market['등락률'] = pd.to_numeric(df_market['등rak률'], errors='coerce').fillna(0.0)
        else:
            # 컬럼명이 다른 스냅샷 대응용 보어벽
            target_col = '등락률' if '등락률' in df_market.columns else df_market.columns[df_market.columns.str.contains('등락|비율|Ratio')][0]
            df_market['등락률'] = pd.to_numeric(df_market[target_col], errors='coerce').fillna(0.0)

        theme_map = {
            "자동차 부품": ["현대모비스", "한온시스템", "현대위아", "성우하이텍", "서연이화", "화신", "에스엘"],
            "로봇/AI": ["레인보우로보틱스", "두산로보틱스", "뉴로메카", "루닛", "뷰노", "이랜시스", "RS오토ベーション"],
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
                    # 🎯 [핵심 보정] 장중 소수점 배수 수치를 진짜 주식 % 수치(예: 3.45%)로 100배 키워줍니다.
                    raw_rate = float(row['등락률'])
                    if abs(raw_rate) <= 1.0 and raw_rate != 0.0:
                        real_rate = raw_rate * 100.0
                    else:
                        real_rate = raw_rate
                        
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['종목명'],
                        "등락률": round(real_rate, 2)
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
    print("🚀 pykrx 장중 실시간 100배 보정형 엔진 구동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 퍼센트 수치 보정 완료 후 CSV 저장 성공!")
        print(df.head(5))
    else:
        print("⚠️ 데이터를 정상적으로 추출하지 못했습니다.")
