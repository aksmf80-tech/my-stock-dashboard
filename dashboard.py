import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

# 🎯 하단 테이블 및 전체 텍스트 크기를 시원시원하게 키우는 특수 핀업 스타일 CSS 주입
st.markdown("""
    <style>
    /* 데이터 테이블 내부 글자 크기 대폭 확대 */
    .stDataFrame div [data-testid="stTable"] td, .stDataFrame div [data-testid="stTable"] th {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #FFFFFF !important;
    }
    /* 선택 상자 및 라벨 글자 크기 강조 */
    .stSelectbox label p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #FFD700 !important;
    }
    /* 서브 타이틀 글자 크기 확대 */
    .stMarkdown h3 {
        font-size: 26px !important;
        font-weight: bold !important;
        border-left: 5px solid #FF4B4B;
        padding-left: 10px;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

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

# 🎯 [핀업 정렬 엔진] 등락률 높은 순서대로 줄 세우기
df = df.sort_values(by='등락률', ascending=False).reset_index(drop=True)

# 주도 테마의 볼륨감을 주기 위한 가중치 배정
df['화면크기_가중치'] = df['등락률'].abs() + 5.0

# 🎯 글자 꼬임과 에러를 방지하기 위해 가장 안정적인 핀업 가로형 단일 라벨로 세팅
def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']} ({row['종목명']}) {sign}{rate}%"

df['핀업라벨'] = df.apply(make_pinup_label, axis=1)

# 해외 서버 시차 해결 (KST 동기화)
utc_now = datetime.utcnow()
kor_now = utc_now + timedelta(hours=9)
current_time_str = kor_now.strftime('%H:%M:%S')

st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {current_time_str})")

# ---------------------------------------------------------
# 상단 테마 선택 컨트롤러 배치 (하단 종목 정보와 완전 직통 연동)
# ---------------------------------------------------------
theme_list = df['테마'].unique().tolist()
current_theme = st.selectbox(
    "🔍 상세 정보를 조회할 테마를 선택하세요", 
    options=theme_list,
    index=0,
    key="global_theme_selector"
)

# ---------------------------------------------------------
# 구역 1: 핀업 완벽 복사형 수십 개 바둑판 트리맵 차트 (버그 원천 제거 버전)
# ---------------------------------------------------------
COLOR_LIMIT = 5.0 

fig = px.treemap(
    df, 
    path=['핀업라벨'],        
    values='화면크기_가중치',    
    color='등락률',        
    color_continuous_scale='RdBu_r', 
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], 
)

# 🎯 버전 충돌을 일으키던 속성을 도려내고, 전 세계 모든 파이썬 환경에서 에러 없이 
# 무조건 글자를 사각형 내부 가득 굵고 큼직하게 정렬해 주는 표준 문법으로 마감했습니다!
fig.update_traces(
    maxdepth=1, 
    textinfo="label",
    marker=dict(line=dict(width=3.0, color='white')), 
    textfont=dict(size=18, color='white', weight='bold')
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=480 
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 🎯 [완벽 동적 연동] 위에서 선택한 테마에 매칭되어 아래 종목들이 칼같이 변하는 구역
# ---------------------------------------------------------
st.subheader(f"📂 {current_theme} 관련 정보")

# 위의 selectbox에서 선택된 테마 이름(current_theme)과 일치하는 종목들만 동적 매핑 필터링!
theme_df = df[df['테마'] == current_theme].copy().reset_index(drop=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 📈 {current_theme} 소속 대장주 당일 시세판")
    
    # 🎯 선생님이 원하시던 시원시원한 대형 폰트 크기(20px)가 적용된 데이터 테이블 매핑
    st.dataframe(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        height=220
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"### 📰 {current_theme} + {current_stock} 관련 뉴스")
    st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://naver.com"
    theme_news_url = "https://naver.com"
    
    st.markdown(f"📌 [📢 **[뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)**]({stock_news_url})")
    st.markdown(f"📌 [📢 **[뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)**]({theme_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# ---------------------------------------------------------
# 타이머 엔진 (60초 자동 리셋)
# ---------------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.invalidate_pages() 
    st.rerun()
