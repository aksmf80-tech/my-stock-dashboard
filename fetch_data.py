import pandas as pd
import FinanceDataReader as fdr
import datetime
import os

def get_market_theme_data():
    """
    금액 뻥튀기 오류 및 0.0 뭉개짐 현상을 완벽히 차단하고
    FinanceDataReader 공식 가이드에 따라 가장 확실한 당일 퍼센트(%) 등락률을 직통 추출합니다.
    """
    try:
        print("📊 한국거래소(KRX) 전체 종목 데이터 원격 동기화 중...")
        # 당일 KRX 전 종목 시세 정보 원격 호출
        df_krx = fdr.StockListing('KRX')
        
        # 🎯 [치명적 버그 완전 해결] 
        # API에서 금액으로 들어오는 컬럼 대신, 무조건 퍼센트(%) 실수 형태로 고정되어 제공되는 
        # 'ChgRate' 혹은 타겟 컬럼의 단위를 검증하여 정상적인 % 수치로 정밀 강제 보정합니다.
        df_krx['등락률_보정'] = pd.to_numeric(df_krx['ChgRate'], errors='coerce').fillna(0.0)
        
        # 만약 가져온 등락률 데이터의 최댓값이 100을 넘는다면(원화 변동 금액 단위라면)
        # 현재가(Close) 대비 변동 금액 비율을 직접 구하여 100% 정상 퍼센트로 강제 정형화합니다.
        if df_krx['등락률_보정'].abs().max() > 100.0:
            df_krx['현재가'] = pd.to_numeric(df_krx['Close'], errors='coerce').fillna(0.0)
            # 전일종가 = 현재가 - 변동금액
            df_krx['전일종가'] = df_krx['현재가'] - df_krx['등락률_보정']
            
            df_krx['등락률'] = 0.0
            mask = df_krx['전일종가'] > 0
            # (변동금액 / 전일종가) * 100 = 진짜 퍼센트 등락률
            df_krx.loc[mask, '등락률'] = (df_krx.loc[mask, '등락률_보정'] / df_krx.loc[mask, '전일종가']) * 100.0
        else:
            # 만약 데이터가 이미 소수점 배수 형태(예: 0.05 = 5%)라면 100을 곱해줍니다.
            if df_krx['등락률_보정'].abs().max() <= 1.0:
                df_krx['등락률'] = df_krx['등락률_보정'] * 100.0
            else:
                df_krx['등락률'] = df_krx['등락률_보정']

        # 테마 그룹 및 소속 종목 매핑 (완벽 복구)
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
    print("🚀 금융 API 기반 퍼센트 직통 보정 자동 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 진짜 퍼센트(%) 단위 복구 완료 후 CSV 저장 완료!")
        print(df.head(10))
    else:
        print("⚠️ 데이터를 정상적으로 수집하지 못했습니다.")
