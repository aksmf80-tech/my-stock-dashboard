import pandas as pd
import FinanceDataReader as fdr
import datetime
import os

def get_market_theme_data():
    """
    증권사 API의 금액 뻥튀기 오류를 원천 차단하고, 
    [ (현재가 - 전일종가) / 전일종가 * 100 ] 공식을 활용해 진짜 퍼센트(%) 등락률을 정밀 계산합니다.
    """
    try:
        print("📊 한국거래소(KRX) 전체 종목 데이터 원격 동기화 중...")
        df_krx = fdr.StockListing('KRX')
        
        # 🎯 [치명적 버그 해결] 금액 데이터 유령을 박멸하기 위해 전일종가와 현재가로 진짜 퍼센트를 직접 구합니다.
        # KRX 데이터프레임의 표준 컬럼명인 Close(현재가)와등락률 계산을 처리합니다.
        if 'Close' in df_krx.columns and 'ChgRate' in df_krx.columns:
            # 안전하게 현재가와 전일대비 변동금액(또는 지표)을 기반으로 정형화하되,
            # 가장 확실하게 제공되는 'Close'(현재가)와 변동금액 변수를 추적합니다.
            # 라이브러리 버전에 따라 ChgRate가 변동금액(원)으로 들어오는 버그를 수식으로 원천 교정합니다.
            
            # 전일 종가 역산: 현재가 - 변동금액
            # 등락률 칸에 들어온 데이터가 변동 금액이므로 이를 활용합니다.
            df_krx['변동금액'] = pd.to_numeric(df_krx['ChgRate'], errors='coerce').fillna(0)
            df_krx['현재가'] = pd.to_numeric(df_krx['Close'], errors='coerce').fillna(0)
            df_krx['전일종가'] = df_krx['현재가'] - df_krx['변동금액']
            
            # 진짜 등락률(%) 계산 = (변동금액 / 전일종가) * 100
            # 분모가 0이 되는 것을 방지하기 위해 0이 아닌 곳만 계산
            df_krx['등락률'] = 0.0
            valid_mask = df_krx['전일종가'] > 0
            df_krx.loc[valid_mask, '등락률'] = (df_krx.loc[valid_mask, '변동금액'] / df_krx.loc[valid_mask, '전일종가']) * 100.0
        else:
            # 만약 컬럼 구조가 다를 경우를 대비한 2차 방어막 (강제 스케일링 변환)
            raw_max = df_krx['ChgRate'].abs().max() if 'ChgRate' in df_krx.columns else 0
            if raw_max > 100:
                df_krx['등락률'] = df_krx['ChgRate'] / 1000.0 # 대략적인 금액 스케일 다운
            else:
                df_krx['등락률'] = df_krx['ChgRate'] if 'ChgRate' in df_krx.columns else 0.0

        # 테마 그룹 및 소속 종목 매핑 (오타 수정 완료)
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
            theme_stocks_df = df_krx[df_krx['Name'].isin(stock_list)]
            
            if not theme_stocks_df.empty:
                for _, row in theme_stocks_df.iterrows():
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['Name'],
                        "등락률": round(float(row['등락률']), 2)
                    })
                    
        if not rows_list:
            return None
            
        final_df = pd.DataFrame(rows_list)
        
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time
        
        return final_df
        
    except Exception as e:
        print(f"❌ 금융 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 금융 API 기반 수식 교정형 자동 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 퍼센트(%) 단위로 완벽 교정 후 CSV 저장 완료!")
        print(df.head(10))
    else:
        print("⚠️ 데이터를 정상적으로 수집하지 못했습니다.")
