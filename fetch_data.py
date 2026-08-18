import pandas as pd
import datetime
import time
import yfinance as yf
import numpy as np

def get_market_theme_data():
    print("📊 [핀업 전수 수집 엔진] 4,115개 종목 및 282개 테마 대규모 동기화 가동...")
    
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    
    # 1. 우리가 구축한 4,115개 종목 뼈대 데이터 읽기
    try:
        # 깃허브에 업로드한 테마/종목 매핑 파일 로드
        base_df = pd.read_csv("theme_data.csv")
    except Exception as e:
        print(f"❌ 뼈대 파일(theme_data.csv) 로드 실패: {e}")
        return None

    # 야후 티커 리스트 추출 (중복 제거하여 API 요청량 최적화)
    yahoo_tickers = base_df['yahoo_code'].dropna().unique().tolist()
    print(f"🔎 고속 수집 대상 고유 티커 수: {len(yahoo_tickers)}개")

    # 2. 야후 파이낸스 멀티스레딩 일괄 다운로드 (핵심: 단 몇 초 만에 4,000개 수집)
    try:
        print("⚡ 야후 파이낸스 멀티스레딩 일괄 다운로드 시작...")
        # period='2d'로 오늘과 어제 데이터를 가져와 등락률 계산의 안정성 확보
        market_data = yf.download(tickers=yahoo_tickers, period="2d", group_by='ticker', threads=True, progress=False)
        print("✅ 일괄 다운로드 완료!")
    except Exception as e:
        print(f"❌ 야후 일괄 다운로드 에러: {e}")
        return None

    # 3. 각 종목별 등락률 및 거래대금(시가총액 대용) 계산 파싱
    parsed_results = []
    
    for ticker in yahoo_tickers:
        try:
            if ticker in market_data.columns.levels[0]:
                ticker_df = market_data[ticker]
                
                # 가장 최근 거래일과 그 전 거래일 데이터 확보
                if len(ticker_df) >= 2:
                    current_close = ticker_df['Close'].iloc[-1]
                    prev_close = ticker_df['Close'].iloc[-2]
                    last_volume = ticker_df['Volume'].iloc[-1]
                else:
                    current_close = ticker_df['Close'].iloc[-1] if not ticker_df['Close'].empty else None
                    prev_close = current_close
                    last_volume = ticker_df['Volume'].iloc[-1] if not ticker_df['Volume'].empty else 0

                # 등락률 계산
                if current_close and prev_close and prev_close != 0:
                    rate = round(((current_close - prev_close) / prev_close) * 100, 2)
                else:
                    rate = 0.0
                
                # 거래대금 산출 (종가 * 거래량) / 데이터 미존재 시 기본값
                trading_value = (current_close * last_volume) if (current_close and last_volume > 0) else 1_000_000
                
                parsed_results.append({
                    "yahoo_code": ticker,
                    "등락률": rate,
                    "거래대금": trading_value
                })
        except Exception as ticker_err:
            continue

    # 파싱된 주가 데이터를 판다스로 변환
    price_df = pd.DataFrame(parsed_results)
    
    if price_df.empty:
        print("❌ 수집된 주가 데이터가 없습니다.")
        return None

    # 4. 뼈대 데이터와 실시간 주가 데이터 맵핑 (종목별 결합)
    merged_df = pd.merge(base_df, price_df, on="yahoo_code", how="inner")

    # 5. [테마별 그룹화 및 집계] 282개 테마별 평균치 산출
    # 테마 스코어 = 소속 종목들의 평균 등락률
    theme_summary = merged_df.groupby("theme").agg(
        등락률=("등락률", "mean"),
        거래대금=("거래대금", "sum"),
        종목수=("theme", "count")
    ).reset_index()

    # 테마명을 기존 이미지 UI의 '테마' 컬럼명과 일치시킵니다.
    theme_summary = theme_summary.rename(columns={"theme": "테마"})
    
    # 소속 종목 중 가장 많이 오른 종목(대장주) 정보 찾기 기틀
    # (이 로직은 추후 대시보드 하단 당일 시세판에 연동됩니다)
    theme_summary['등락률'] = theme_summary['등락률'].round(2)

    # 6. 스트림릿 트리맵 화면 크기 가중치 계산 (절대 등락률 + 거래대금 로그 스케일)
    theme_summary['정렬용'] = theme_summary['등락률'].abs()
    theme_summary['화면크기_가중치'] = theme_summary['정렬용'] + np.log1p(theme_summary['거래대금']) / 2.0
    
    # 가중치 순으로 정렬하여 대시보드 격자 크기 최적화
    final_df = theme_summary.sort_values(by="화면크기_가중치", ascending=False).reset_index(drop=True)
    final_df['업데이트시간'] = kst_now.strftime('%Y-%m-%d %H:%M:%S')
    
    return final_df

if __name__ == "__main__":
    # 대시보드가 읽어갈 최종 실시간 결과 파일
    OUTPUT_FILE = "realtime_theme_status.csv"
    
    df = get_market_theme_data()
    if df is not None:
        # 인코딩 에러 방지를 위해 utf-8-sig 사용
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"🎉 [성공] 282개 테마 전수 수집 및 동기화 완결! ({OUTPUT_FILE} 저장됨)")
