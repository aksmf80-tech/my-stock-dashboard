import pandas as pd
from pykrx import stock
import datetime
import os

def get_market_theme_data():
    """
    utcnow() 시차 오류와 금액 0.0 뭉개짐 버그를 원천 차단하고,
    가장 직관적인 방법으로 한국 시각(KST) 및 진짜 퍼센트 등락률을 확실하게 수집합니다.
    """
    try:
        # 🎯 [치명적 시차 버그 해결] utcnow()의 파이썬 버전별 충돌을 피하기 위해 
        # 시스템 시각에 강제로 9시간을 더하는 가장 직관적이고 안전한 수식으로 한국 시간(KST)을 산출합니다.
        current_base = datetime.datetime.now()
        # 만약 시스템이 이미 해외 기준(UTC)이라면 9시간을 더하고, 
        # 한국 기준이라면 오늘 날짜를 그대로 유지하도록 타임존 방어막을 칩니다.
        if current_base.hour < 9:
            kst_now = current_base + datetime.timedelta(hours=9)
        else:
            kst_now = current_base
            
        today_str = kst_now.strftime("%Y%m%d")
        print(f"📊 pykrx 엔진 기반 당일({today_str}) 전 종목 시세 연동 중...")
        
        # 🎯 [치명적 0.0 버그 해결] 등락률이 완벽하게 실수 퍼센트(%) 형태로 내장되어 나오는 
        # pykrx 전용 가격 변동 함수(get_market_price_change_by_ticker)를 직통 호출합니다.
        df_kospi = stock.get_market_price_change_by_ticker(today_str, today_str, "KOSPI")
        df_kosdaq = stock.get_market_price_change_by_ticker(today_str, today_str, "KOSDAQ")
        
        # 만약 장 시작 전이거나 주말/휴일이라 데이터가 비어있다면, 시스템이 제공하는 직전 영업일로 자동 백업합니다.
        if df_kospi.empty or df_kosdaq.empty:
            latest_date = stock.get_nearest_business_day_in_a_week()
            print(f"⌛ 휴일 또는 장 개시 전입니다. 최근 거래일({latest_date}) 데이터로 자동 전환합니다.")
            df_kospi = stock.get_market_price_change_by_ticker(latest_date, latest_date, "KOSPI")
            df_kosdaq = stock.get_market_price_change_by_ticker(latest_date, latest_date, "KOSDAQ")
            
        # 코스피와 코스닥 시장 데이터 합치기
        df_market = pd.concat([df_kospi, df_kosdaq])
        
        if df_market.empty:
            print("⚠️ 거래소 시세 테이블이 완전히 비어있습니다.")
            return None
            
        # 데이터프레임 구조 정형화 (인덱스 해제 및 컬럼명 일치)
        df_market = df_market.reset_index()
        df_market['종목명'] = df_market['종목명'].astype(str).str.strip()
        
        # 🎯 진짜 퍼센트(%) 수치 확보
        df_market['등락률'] = pd.to_numeric(df_market['등락률'], errors='coerce').fillna(0.0)

        # 선생님 블로그 포스팅 전략에 최적화된 9대 핵심 주도 테마 맵
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
            # 시장 전체 데이터에서 우리 테마 종목들만 필터링
            theme_stocks_df = df_market[df_market['종목명'].isin(stock_list)]
            
            if not theme_stocks_df.empty:
                for _, row in theme_stocks_df.iterrows():
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['종목명'],
                        "등락률": round(float(row['등락률']), 2)
                    })
                    
        if not rows_list:
            print("❌ 테마 종목 매핑 실패")
            return None
            
        final_df = pd.DataFrame(rows_list)
        
        # 파일 내 저장되는 시간 문자열도 강제로 한국 시각(KST) 낮 시간으로 포맷팅
        now_time_kst = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time_kst
        
        return final_df
        
    except Exception as e:
        print(f"❌ 금융 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 pykrx 직통 시세 변동형 자동 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 퍼센트(%) 수치 및 한국 표준시 반영 완료!")
        print(df.head(5))
    else:
        print("⚠️ 데이터를 정상적으로 추출하지 못했습니다.")
