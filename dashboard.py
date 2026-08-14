import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("📊 네이버 금융 테마별 등락률 대시보드")

# 📂 깃허브 자동화 로봇이 실시간으로 채워줄 데이터 파일 이름
DATA_FILE = "theme_data.csv"

# 💡 데이터를 로드하는 함수
def load_data():
    if os.path.exists(DATA_FILE):
        # 내 저장소에 쌓인 가벼운 csv 파일만 빠르게 읽어옵니다.
        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        return df
    else:
        return None

df = load_data()

if df is not None:
    st.success("✅ 실시간 데이터 동기화 완료")
    st.dataframe(df, use_container_width=True)
else:
    # 월요일 장 개장 전이거나 아직 로봇이 첫 데이터 파일을 만들기 전 상태의 화면
    st.warning("⏳ 월요일 주식 시장 개장 및 데이터 동기화 대기 중입니다...")
    st.info("현재 대시보드는 500명 동시 접속을 버티기 위한 '자동 데이터 수집 시스템'으로 대기 중입니다.")
