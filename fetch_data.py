# fetch_data.py 내부의 수정할 핵심 함수 구역입니다.

def get_hot_tickers_split(base_df):
    """마스터 뼈대에서 테마별 상위 주도주를 뽑아 A/B 그룹(홀짝)으로 반반 쪼개기"""
    
    # 🎯 [300종목 엔진 업그레이드] 테마당 상위 42개씩 추출 (7개 테마 X 42 = 총 294~300개 최정예 대장주)
    target_stocks = base_df.groupby('theme').head(42).copy()
    
    tickers_list = []
    ticker_to_name = {}
    
    if 'code' in target_stocks.columns:
        for _, row in target_stocks.iterrows():
            s_name = str(row['name']).strip()
            s_code = str(row['code']).strip()
            if s_code != '000000' and len(s_code) >= 5:
                ticker_ks = f"{s_code.zfill(6)}.KS"
                tickers_list.append(ticker_ks)
                ticker_to_name[ticker_ks] = s_name

    # 중복 종목 제거
    tickers_list = list(set(tickers_list))
    
    # 📌 총 300개를 반으로 쪼개어 A조(150개), B조(150개) 분할 처리 (야후 차단 완벽 회피)
    half = len(tickers_list) // 2
    group_a = tickers_list[:half]
    group_b = tickers_list[half:]
    
    return group_a, group_b, ticker_to_name
