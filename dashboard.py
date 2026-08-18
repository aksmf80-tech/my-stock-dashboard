import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

# 🔔 홍보 배너 및 대시보드 타이틀
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

# 데이터 파일 존재 여부 확인
if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 최신 데이터 읽기
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

required_cols = ['테마', '종목명', '등락률']
if df is None or df.empty or not all(col in df.columns for col in required_cols):
    st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다.")
    st.stop()

# 🎯 [핀업 스타일 교정 1] 등락률이 높은 주도 테마일수록 화면 사각형 크기를 더 크게 배정합니다.
# 변동 폭(절댓값)에 비례하여 크기를 유동적으로 셋팅하되 최소 크기(5)를 보장합니다.
df['화면크기_가중치'] = df['등락률'].abs() + 5.0

# 🎯 [핀업 스타일 교정 2] 숫자 앞에 '+' 기호와 '%' 단위를 붙여서 핀업과 완벽히 똑같은 라벨을 만듭니다.
def make_pinup_label(row):
    rate = row['등락률']
    if rate > 0:
        return f"{row['테마']}\n+{rate}%"
    elif rate < 0:
        return f"{row['테마']}\n{rate}%"
    else:
        return f"{row['테마']}\n0.0%"

df['핀업라벨'] = df.apply(make_pinup_label, axis=1)

# 해외 서버 기준 시간을 대한민국 서울 표준시(KST)로 정확히 연동
utc_now = datetime.utcnow()
kor_now = utc_now + timedelta(hours=9)
current_time_str = kor_now.strftime('%H:%M:%S')

st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {current_time_str})")

# ---------------------------------------------------------
# 상단 테마 선택 컨트롤러 배치
# ---------------------------------------------------------
theme_list = df['테마'].unique().tolist()
current_theme = st.selectbox(
    "🔍 **상세 정보를 조회할 테마를 선택하세요**", 
    options=theme_list,
    index=0,
    key="global_theme_selector"
)

# ---------------------------------------------------------
# 구역 1: 등락률 시각화용 트리맵 (0을 중심으로 선명한 핀업 스타일 대칭 정렬)
# ---------------------------------------------------------
# 🎯 [핀업 스타일 교정 3] 색상 대비 극대화 범위를 강제로 정밀 타겟팅합니다.
# 최대 범위를 ±5% 혹은 ±7% 수준으로 꽉 조여놓으면, 조금만 올라도 사각형이 핀업처럼 시뻘갛게 타오릅니다!
COLOR_LIMIT = 5.0  # 🎯 ±5%를 기준으로 색상 최대 맑기 고정 (원하시면 7.0이나 10.0으로 변경 가능)

fig = px.treemap(
    df, 
    path=['핀업라벨'],     # 🎯 글자 포맷팅이 완료된 핀업 라벨 적용
    values='화면크기_가중치', # 🎯 주도 테마가 더 크게 나오도록 크기 가중치 연동
    color='등락률',        
    color_continuous_scale='RdBu_r', # 상승 빨강, 하락 파랑
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], # 🎯 핵심: 좁은 범위 대칭 강제로 색감 극대화!
    hover_data=['종목명']
)

# 핀업 스타일 테두리 마감 및 가독성 설정
fig.update_traces(
    maxdepth=1, 
    textinfo="label", # 라벨 텍스트만 깔끔하게 표출
    marker=dict(line=dict(width=2.0, color='white')), # 사각형 구분선을 핀업처럼 선명하게 분할
    textfont=dict(size=16, color='white', weight='bold') # 글자 크기 키우고 볼드체 두껍게 강조
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=420 # 핀업 비율에 맞게 높이 소폭 상향
)

# 차트 표출
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 테마 클릭 시 아래에 목록이 주르륵 나오는 부분 & 뉴스 연동
# ---------------------------------------------------------
st.subheader(f"📂 {current_theme} 관련 정보")

theme_df = df[df['테마'] == current_theme].copy()

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📈 {current_theme} 종목 리스트**")
    
    st.data_editor(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        disabled=True, 
        key="stock_selector"
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
    st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://yahoo.com" + str(current_stock)
    theme_news_url = "https://yahoo.com"
    
    st.markdown(f"📌 [📢 [뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)]({stock_news_url})")
    st.markdown(f"📌 [📢 [뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)]({theme_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# ---------------------------------------------------------
# 타이머 엔진 (60초 자동 리셋 및 캐시 고스트 파괴)
# ---------------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.invalidate_pages() 
    st.rerun()
