import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(layout="wide")
st.title("📊 테마별 현황판")

# 깃허브 자동화 로봇이 실시간으로 채워줄 데이터 파일 이름
DATA_FILE = "theme_data.csv"

# 🟢 [핵심] 60초마다 이 안의 표만 화면 깜빡임 없이 새로고침하는 함수
@st.fragment(run_every=60)
def show_realtime_board():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        
        # 언제 마지막으로 데이터가 바뀌었는지 실시간으로 시간을 보여줍니다.
        st.success(f"✅ 실시간 데이터 동기화 완료! (최근 갱신 시각: {time.strftime('%H:%M:%S')})")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⏳ 월요일 주식 시장 개장 및 데이터 동기화 대기 중입니다...")

# 화면에 보드 실행하기
show_realtime_board()
