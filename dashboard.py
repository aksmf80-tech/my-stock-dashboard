import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ 최상단 페이지 설정 (좌우 여백을 최소화하여 화면을 넓게 씁니다)
st.set_page_config(layout="wide")

# 🎯 [여백 파괴 및 대형화] 상단 여백을 극단적으로 줄이고 메인 콘텐츠를 키웁니다.
st.markdown("""
    <style>
    /* 전체 브라우저 상하좌우 여백을 완전히 제로에 가깝게 밀착 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    
    /* 타이틀 마진 축소 */
    h1 {
        margin-top: 10px !important;
        margin-bottom: 15px !important;
        font-size: 36px !important;
    }

    /* 📊 순수 데이터 표(st.table) 글자 크기를 왕글씨(26px)로 더 확대 */
    table {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    thead tr th {
        color: #FFD700 !important;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    tbody tr td {
        color: #FFFFFF !important;
        background-color: #1A1D24 !important;
    }
    
    /* 선택 상자 텍스트 크기 확대 */
    div[data-testid="stSelectbox"] label p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #FFD700 !important;
    }
    
    /* 서브 타이틀 대형화 */
    .stMarkdown h3 {
        font-size: 28px !important;
        font-weight: bold !important;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 🗑️ [기존 상단 st.info 홍보 배너 및 st.success 동기화 알림 완전 제거]
# ---------------------------------------------------------
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 데이터 로드 및 정제
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
theme_summary = df.groupby('테마')['등락률'].mean().reset_index()

theme_summary['정렬용'] = theme_summary['등락률'].abs()
theme_summary = theme_summary.sort_values(by='정렬용', ascending=False).reset_index(drop=True)
theme_summary['화면크기_가중치'] = theme_summary['정렬용'] + 5.0

def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

theme_summary['핀업라벨'] = theme_summary.apply(make_pinup_label, axis=1)

# ---------------------------------------------------------
# 직통 연동 선택 박스
# ---------------------------------------------------------
theme_list = theme_summary['테마'].unique().tolist()
chosen_theme = st.selectbox(
    "🔍 상세 정보를 조회할 테마를 선택하세요 (하단 시세판 자동 연동)", 
    options=theme_list,
    index=0,
    key="global_theme_selector"
)

# ---------------------------------------------------------
# 구역 1: 핀업 바둑판 트리맵 차트 (높이를 700으로 대폭 확대하여 전면 배치)
# ---------------------------------------------------------
COLOR_LIMIT = 5.0 

fig = px.treemap(
    theme_summary, 
    path=['핀업라벨'], 
    values='화면크기_가중치',    
    color='등락률',        # 🎯 오타 수정: '등rak률' ➡️ '등락률'로 변경 완료
    color_continuous_scale='RdBu_r', 
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], 
)

fig.update_traces(
    maxdepth=1, 
    textinfo="label",      
    marker=dict(line=dict(width=3.0, color='white')), 
    textfont=dict(size=22, color='white', weight='bold')
)

fig.update_traces(textposition="middle center") 

fig.update_layout(
    dragmode=False,    
    margin=dict(t=5, l=5, r=5, b=5), 
    height=700 
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

# ---------------------------------------------------------
# 구역 2: 하단 종목 시세판 및 뉴스 구역 (글자 크기 및 컴포넌트 업그레이드)
# ---------------------------------------------------------
st.subheader(f"📂 {chosen_theme} 관련 정보")

theme_df = df[df['테마'] == chosen_theme].copy().sort_values(by='등락률', ascending=False).reset_index(drop=True)
theme_df['등락률_정제'] = theme_df['등락률'].apply(lambda x: f"+{round(float(x), 2)}%" if float(x) > 0 else f"{round(float(x), 2)}%")

theme_df_clean = theme_df[['종목명', '등락률_정제']].copy()
theme_df_clean.columns = ['🔥 소속 대장 종목명', '📈 실시간 등락률 (%)']

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 📊 {chosen_theme} 소속 대장주 당일 시세판")
    st.table(theme_df_clean) # CSS 효과로 26px 크기의 대형 활자로 출력됩니다.
    
with col2:
    st.markdown(f"### 📰 {chosen_theme} 뉴스 브리핑")
    st.info(f"🔍 '{chosen_theme}' 시장 동향 및 주도주 흐름에 대한 실시간 뉴스 요약...")
    
    stock_news_url = "https://naver.com"
    st.markdown(f"📌 [📢 **[실시간 뉴스] '{chosen_theme}' 주도 테마, 대량 거래대금 몰리며 시장 강력 견인 (방금 전)**]({stock_news_url})")
    st.markdown(f"📌 [📢 **[시황 분석] 글로벌 공급망 재편 수혜주 부각... 블로그 본문에서 대장주 매매 타점 공개**]({stock_news_url})")

# 60초 자동 리셋 시스템 유지
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun() # 🎯 에러 유발 함수를 지우고 깔끔하게 바로 리런시킵니다.
