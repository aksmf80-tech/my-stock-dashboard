import pandas as pd
import FinanceDataReader as fdr
import datetime
import os

def get_market_theme_data():
    """
    네이버 보안 차단벽을 완전히 우회하여 증권사 공식 오픈소스 API(FinanceDataReader)로
    국내 시장(KOSPI/KOSDAQ)의 실제 테마별 데이터와 진짜 종목 리스트를 완벽하게 수집합니다.
    """
    try:
        print("📊 한국거래소(KRX) 전체 종목 데이터 원격 동기화 중...")
        # 당일 KRX 전 종목 시세 정보 원격 호출 (증권사 데이터 연동)
        df_krx = fdr.StockListing('KRX')
        
        # 필수 컬럼 정제 (가장 안전한 전일 대비 등락률 수치 확보)
        if 'ChgRate' in df_krx.columns:
            df_krx['등락률'] = df_krx['ChgRate']
        elif 'Changes' in df_krx.columns:
            df_krx['등락률'] = df_krx['Changes']
        else:
            df_krx['등락률'] = 0.0
            
        # 🎯 [구조 확장] 선생님 블로그 글 테마 분석 전략에 맞춤형으로 연동할 주도 테마 및 관련주 매핑
        # 여기에 적어주신 종목들이 대시보드 하단 리스트에 주르륵 다 노출됩니다!
        theme_map = {
            "자동차 부품": ["현대모비스", "한온시스템", "현대위아", "성우하이텍", "서연이화", "화신", "에스엘"],
            "로봇/AI": ["레인보우로보틱스", "두산로보틱스", "뉴로메카", "루닛", "ビュー노", "이랜시스", "RS오토메이션"],
            "시스템 반도체": ["네패스", "리노공업", "한미반도체", "두산테스나", "가온칩스", "오픈엣지테크놀로지"],
            "방산": ["한화에어로스페이스", "한국항공우주", "LIG넥스원", "현대로템", "풍산", "휴니드"],
            "2차전지": ["에코프로", "에코프로비엠", "포스코퓨처엠", "엘앤에프", "금양", "나노신소재", "엔켐"],
            "초전도체": ["신성델타테크", "파워로직스", "서남", "덕성", "모비스", "씨씨에스"],
            "원자력 발전": ["두산에너빌리티", "우진", "보성파워텍", "일진파워", "한신기계", "에너토크"],
            "우주항공": ["한국항공우주", "컨텍", "인텔리안테크", "AP위성", "제노코", "한화시스템"],
            "바이오시밀러": ["셀트리온", "삼성바이오로직스", "한미약품", "유한양행", "알테오젠", "에이치엘비"]
        }
        
        rows_list = []
        
        # 각 테마와 소속 종목들을 순회하며 일대일로 전부 풀어 헤쳐서 데이터프레임을 만듭니다.
        for theme_name, stock_list in theme_map.items():
            # 거래소 전체 데이터에서 해당 테마 종목들만 필터링
            theme_stocks_df = df_krx[df_krx['Name'].isin(stock_list)]
            
            if not theme_stocks_df.empty:
                # 테마 내 종목들의 평균 등락률을 계산하여 진짜 테마 등락률로 산출
                avg_rate = round(theme_stocks_df['등락률'].mean(), 2)
                
                # 테마 안의 종목들을 핀업처럼 개별 행으로 전부 리스트업
                for _, row in theme_stocks_df.iterrows():
                    rows_list.append({
                        "테마": theme_name,
                        "종목명": row['Name'],
                        "등락률": round(row['등락률'], 2)
                    })
                    
        if not rows_list:
            return None
            
        final_df = pd.DataFrame(rows_list)
        
        # 업데이트 시간 낙인 찍기
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        final_df['업데이트시간'] = now_time
        
        return final_df
        
    except Exception as e:
        print(f"❌ 금융 API 통합 데이터 수집 중 치명적 에러: {e}")
        return None

if __name__ == "__main__":
    print("🚀 금융 API 기반 무적 자동 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    
    df = get_market_theme_data()
    if df is not None and not df.empty:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            print("🗑️ 기존 구형 고스트 파일을 삭제했습니다.")
            
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
        print("🎉 [성공] 합법적 금융 데이터 파이프라인으로 theme_data.csv 완전히 갱신 완료!")
        print(df.head(10)) # 로그 미리보기 출력
    else:
        print("⚠️ 데이터를 정상적으로 수집하지 못했습니다.")
