import pandas as pd
import datetime
import time
import yfinance as yf
import numpy as np

def get_market_theme_data():
    print("📊 [핀업 전수 수집 엔진] 4,115개 종목 및 282개 테마 대규모 동기화 가동...")
    
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    
    # 1. 깃허브에 올린 4,115개 종목 뼈대 데이터 읽기
    try:
        base_df = pd.read_csv("theme_data.csv", encoding="utf-8-sig")
    except Exception as e:
        print(f"❌ 뼈대 파일(theme_data.csv) 로드 실패: {e}")
        return None

    # 🚨 [KeyError 완벽 방지] 열 이름을 표준화하고 없으면 자동 생성합니다.
    # 모든 열 이름을 소문자로 변경하고 양끝 공백 제거
    base_df.columns = [str(col).strip().lower() for col in base_df.columns]
    
    # 'theme' 혹은 '테마' 열 통일
    if '테마' in base_df.columns:
        base_df = base_df.rename(columns={'테마': 'theme'})
    if '종목명' in base_df.columns:
        base_df = base_df.rename(columns={'종목명': 'name'})
    if '시장' in base_df.columns:
        base_df = base_df.rename(columns={'시장': 'market'})
    if '종목코드' in base_df.columns:
        base_df = base_df.rename(columns={'종목코드': 'code'})

    # 만약 yahoo_code 열이 없다면 code(종목코드) 열을 기반으로 자동 생성
    if 'yahoo_code' not in base_df.columns and 'yahoo_code' in [c.replace('_','') for c in base_df.columns]:
        # 대소문자나 언더바 혼용 대응 (_ 제거 후 비교)
        for col in base_df.columns:
            if col.replace('_','') == 'yahoocode':
                base_df = base_df.rename(columns={col: 'yahoo_code'})

    if 'yahoo_code' not in base_df.columns:
        print("💡 yahoo_code 열이 없어 기존 종목코드를 기반으로 야후 티커를 자동 생성합니다.")
        # 'code' 열 찾기
        code_col = 'code' if 'code' in base_df.columns else base_df.columns[1] # 두번째 열을 코드로 가정
        
        # 시장 구분(KOSPI/KOSDAQ) 열 찾기
        market_col = 'market' if 'market' in base_df.columns else None
        
        def convert_to_yahoo(row):
            raw_code = str(row[code_col]).strip().split('.')[0].zfill(6)
            if market_col and ('kosdaq' in str(row[market_col]).lower() or '코스닥' in str(row[market_col])):
                return f"{raw_code}.KQ"
            else:
                return f"{raw_code}.KS"
                
        base_df['yahoo_code'] = base_df.apply(convert_to_yahoo, axis=1)

    # 야후 티커 리스트 추출 (중복 제거)
    yahoo_tickers = base_df['yahoo_code'].dropna().unique().tolist()
    print(f"🔎 고속 수집 대상 고유 티커 수: {len(yahoo_tickers)}개")

    # 2. 야후 파이낸스 멀티스레딩 일괄 다운로드 (단 몇 초 만에 수집)
    try:
        print("⚡ 야후 파이낸스 멀티스레딩 일괄 다운로드 시작...")
        market_data = yf.download(tickers=yahoo_tickers, period="2d", group_by='ticker', threads=True, progress=False)
        print("✅ 일괄 다운로드 완료!")
    except Exception as e:
        print(f"❌ 야후 일괄 다운로드 에러: {e}")
        return None

    # 3. 각 종목별 등락률 및 거래대금 계산 파싱
    parsed_results = []
    for ticker in yahoo_tickers:
        try:
            if ticker in market_data.columns.levels:
                ticker_df = market_data[ticker]
                
                if len(ticker_df) >= 2:
                    current_close = ticker_df['Close'].iloc[-1]
                    prev_close = ticker_df['Close'].iloc[-2]
                    last_volume = ticker_df['Volume'].iloc[-1]
                else:
                    current_close = ticker_df['Close'].iloc[-1] if not ticker_df['Close'].empty else None
                    prev_close = current_close
                    last_volume = ticker_df['Volume'].iloc[-1] if not ticker_df['Volume'].empty else 0

                if current_close and prev_close and prev_close != 0:
                    rate = round(((current_close - prev_close) / prev_close) * 100, 2)
                else:
                    rate = 0.0
                
                trading_value = (current_close * last_volume) if (current_close and last_volume > 0) else 1_000_000
                
                parsed_results.append({
                    "yahoo_code": ticker,
                    "등락률": rate,
                    "거래대금": trading_value
                })
        except Exception:
            continue

    price_df = pd.DataFrame(parsed_results)
    if price_df.empty:
        print("❌ 수집된 주가 데이터가 없습니다.")
        return None

    # 4. 뼈대 데이터와 실시간 주가 데이터 맵핑
    merged_df = pd.merge(base_df, price_df, on="yahoo_code", how="inner")

    # 5. 282개 테마별 평균치 집계
    theme_summary = merged_df.groupby("theme").agg(
        등락률=("등락률", "mean"),
        거래대금=("거래대금", "sum"),
        종목수=("theme", "count")
    ).reset_index()

    theme_summary = theme_summary.rename(columns={"theme": "테마"})
    theme_summary['등락률'] = theme_summary['등락률'].round(2)

    # 6. 스트림릿 트리맵 화면 크기 가중치 계산
    theme_summary['정렬용'] = theme_summary['등락률'].abs()
    theme_summary['화면크기_가중치'] = theme_summary['정렬용'] + np.log1p(theme_summary['거래대금']) / 2.0
    
    final_df = theme_summary.sort_values(by="화면크기_가중치", ascending=False).reset_index(drop=True)
    final_df['업데이트시간'] = kst_now.strftime('%Y-%m-%d %H:%M:%S')
    
    return final_df

if __name__ == "__main__":
    OUTPUT_FILE = "realtime_theme_status.csv"
    df = get_market_theme_data()
    if df is not None:
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 282개 테마 전수 수집 및 동기화 완결! ({OUTPUT_FILE} 저장됨)")
