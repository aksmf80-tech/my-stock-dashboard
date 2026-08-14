import pandas as pd
import requests
import datetime

def get_naver_data():
    # 월요일 주식 장이 열리면 사용자님의 원래 네이버 금융 크롤링 로직으로 완성해 드릴 예정입니다.
    # 우선은 자동화 로봇이 정상 작동하는지 테스트하기 위한 샘플 데이터를 배치해 둡니다.
    sample_data = {
        "테마": ["자동차 부품", "로봇", "시스템 반도체", "DDR5", "방산"],
        "종목명": ["현대모비스", "레인보우로보틱스", "네패스", "아비코전자", "한화에어로스페이스"],
        "등락률": [19.42, 16.90, 11.72, 8.21, -10.07],
        "업데이트시간": [str(datetime.datetime.now())] * 5
    }
    df = pd.DataFrame(sample_data)
    return df

if __name__ == "__main__":
    try:
        # 1. 데이터 수집
        df = get_naver_data()
        
        # 2. 저장소에 'theme_data.csv' 파일로 저장
        df.to_csv("theme_data.csv", index=False, encoding="utf-8-sig")
        print("데이터 수집 및 csv 파일 저장 성공!")
    except Exception as e:
        print(f"오류 발생: {e}")
