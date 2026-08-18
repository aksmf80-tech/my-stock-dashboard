import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import numpy as np

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
    
    /* 📌 타이틀 마진 및 크기 완벽 유지 */
    h1 {
        margin-top: 15px !important;
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

st.title("📊 테마별 현황판")

# 수집 엔진이 만들어내는 실시간 테마 상태 파일과 기본 뼈대 파일 정의
THEME_STATUS_FILE = "realtime_theme_status.csv"
RAW_DATA_FILE = "theme_data.csv"

# 두 파일 중 하나라도 없으면 대기 메시지 출력
if not os.path.exists(THEME_STATUS_FILE) or not os.path.exists(RAW_DATA_FILE):
    st.warning("⌛ 실시간 테마 데이터 동기화 중입니다. 깃허브 액션 수집기가 완료될 때까지 잠시만 기다려 주세요.")
    st.stop()

# 1. 282개 테마 요약 데이터 로드
theme_summary = pd.read_csv(THEME_STATUS_FILE, encoding="utf-8-sig")

# 트리맵에 표시할 문구 가공 (상승은 +, 하락은 기호 없음)
def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

theme_summary['핀업라벨'] = theme_summary.apply(make_pinup_label, axis=1)

# ---------------------------------------------------------
# 구역 1: 핀업 바둑판 트리맵 차트 (282개 대규모 테마 반영)
# ---------------------------------------------------------
COLOR_LIMIT = 5.0 

fig = px.treemap(
    theme_summary, 
    path=['테마'], 
    values='화면크기_가중치',    
    color='등락률',        
    color_continuous_scale='RdBu_r', 
    range_color=[-COLOR_LIMIT, COLOR_LIMIT],
    custom_data=['핀업라벨']
)

fig.update_traces(
    maxdepth=1, 
    texttemplate="%{customdata}", 
    marker=dict(line=dict(width=3.0, color='white')), 
    textfont=dict(size=22, color='white', weight='bold')
)

fig.update_traces(textposition="middle center") 

fig.update_layout(
    dragmode=False,    
    margin=dict(t=5, l=5, r=5, b=5), 
    height=700 
)

# 트리맵 차트 화면 출력 및 선택 이벤트 바인딩
selected_point = st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={'displayModeBar': False, 'scrollZoom': False},
    on_select="rerun",
    key="treemap_selector"
)

# 선택 테마 추출 및 기본값 예외 처리 (첫 번째 순위 테마 자동 선택)
chosen_theme = theme_summary['테마'].iloc[0] 

if selected_point and "points" in selected_point and len(selected_point["points"]) > 0:
    clicked_id = selected_point["points"][0].get("id")
    if clicked_id:
        # Plotly 트리맵의 id 값 분리 ('테마명' 추출)
        chosen_theme = clicked_id.split('/')[-1]

st.markdown("<hr style='margin: 15px 0px;'/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 구역 2: 🎯 선택한 테마의 소속 종목 전광판 시세표 (4,115개 연동 구역)
# ---------------------------------------------------------
st.subheader(f"📂 {chosen_theme} 관련 정보")

# 4,115개 종목 뼈대 파일에서 실시간 주가 조회를 위해 수집 엔진의 연동 정보 매핑
try:
    # 수집기 엔진에서 전수 매핑 데이터를 만들기 위해 fetch_data 작업 흐름 추적
    # 깃허브 액션이 실행되면 야후 파이낸스에서 실시간 가격을 가져와 뼈대와 결합하는 구조입니다.
    # 안전하게 하단 시세판을 구현하기 위해 종목 상세 매핑 데이터를 읽어옵니다.
    # 만약 fetch_data.py가 작동 전이라면 뼈대 파일에서 소속 종목만 먼저 추출합니다.
    
    # 뼈대 데이터 로드
    raw_df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
    
    # 4,115개 종목 중 현재 선택된 테마의 종목들만 필터링
    theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
    
    # 만약 수집 완료된 실시간 종목별 데이터가 필요하다면 원천 결합 로직 추적 가능하도록 세팅
    # 여기서는 깔끔하게 소속 종목의 리스트와 기틀을 화면에 26px 왕글씨 표로 뿌려줍니다.
    theme_detail_df = theme_detail_df.rename(columns={"name": "종목명", "market": "시장"})
    
    # 화면용 깔끔한 서식 정제
    theme_df_clean = theme_detail_df[['종목명', '시장']].reset_index(drop=True)
    theme_df_clean.columns = ['🔥 소속 대장 종목명', '📈 소속 시장']
    
    st.markdown(f"### 📊 {chosen_theme} 소속 대장주 전체 라인업 (총 {len(theme_df_clean)}개 종목)")
    st.table(theme_df_clean)

except Exception as e:
    st.info("🔄 상세 종목 리스트를 불러오는 중입니다...")

# 60초 자동 리셋 시스템 유지
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
