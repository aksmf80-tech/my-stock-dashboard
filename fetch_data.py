import pandas as pd
import requests
import datetime
import time
import os

def get_naver_data():
    """
    네이버 금융 테마별 시세 테이블을 데이터프레임으로 직관적으로 추출하여
    테마명, 대장주, 실제 테마 등락률을 정확하게 매핑합니다.
    """
    url = "https://naver.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    all_dfs = []
    
    # 안전하게 1페이지부터 3페이지까지 수집
    for page in range(1, 4):
        page_url = f"{url}?&page={page}"
        try:
            response = requests.get(page_url, headers=headers)
            response.encoding = 'euc-kr' # 네이버 한글 깨짐 방지
            
            if response.status_code != 200:
                continue
                
            # HTML 내부의 데이터 테이블을 판다스로 직독직해합니다.
            dfs = pd.read_html(response.text)
            for table_df in dfs:
                # 네이버 테마 테이블은 컬럼명에 '테마명'과 '전일대비' 정보가 반드시 포함됩니다.
                if '테마명' in table_df.columns and '전일대비' in table_df.columns:
                    all_dfs.append(table_df)
                    
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ {page}페이지 읽기 오류: {e}")
            continue

    if not all_dfs:
        return None

    # 수집된 페이지별 테이블 통합
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # 쓰레기 데이터 행(NaN 또는 구분선 행) 완벽 청소
    full_df = full_df.dropna(subset=['테마명', '전일대비'])
    
    # 등락률 문자열 정제 및 수치화
    full_df['전일대비'] = full_df['전일대비'].astype(str).str.replace('%', '').str.replace('+', '').str.strip()
    full_df['등락률'] = pd.to_numeric(full_df['전일대비'], errors='coerce')
    full_df = full_df.dropna(subset=['등락률'])
    
    full_df = full_df.rename(columns={'테마명': '테마'})
    
    # 🎯 [문법 버그 수정 완료] 주요종목 텍스트에서 첫 번째 종목만 안전하게 잘라냅니다.
    def extract_first_stock(x):
        val = str(x).strip()
        if ',' in val:
            return val.split(',')[0].strip()
        return val

    if '주요종목' in full_df.columns:
        full_df['종목명'] = full_df['주요종목'].apply(extract_first_stock)
    elif '주요종목.1' in full_df.columns:
        full_df['종목명'] = full_df['주요종목.1'].apply(extract_first_stock)
    else:
        # 컬럼명이 유동적으로 깨질 경우를 대비해 4번째 열(인덱스 3) 데이터를 강제 파싱합니다.
        full_df['종목명'] = full_df.iloc[:, 3].apply(extract_first_stock)

    # 대시보드 필수 구조로 최종 압축
    final_df = full_df[['테마', '종목명', '등락률']].copy()
    final_df = final_df.drop_duplicates(subset=['테마'])
    
    # 시장 주도 테마 상위 15개 강제 소팅
    final_df['정렬용'] = final_df['등락률'].abs()
    final_df = final_df.sort_values(by="정렬용", ascending=False).head(15).drop(columns=['정렬용'])
    
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_df['업데이트시간'] = now_time
    
    return final_df

if __name__ == "__main__":
    print("🚀 구조 교정형 GitHub Actions 수집기 기동...")
    DATA_FILE = "theme_data.csv"
    try:
        df = get_naver_data()
        if df is not None and not df.empty:
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
                print("🗑️ 구형 유령 데이터를 삭제했습니다.")
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            print("🎉 [성공] 완전히 정제된 theme_data.csv 생성 완료!")
            print(df.head(5))
        else:
            print("⚠️ 파싱된 테이블이 비어있습니다.")
    except Exception as e:
        print(f"구동 중 에러 발생: {e}")
