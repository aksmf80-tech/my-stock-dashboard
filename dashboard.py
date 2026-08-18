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

THEME_STATUS_FILE = "realtime_theme_status.csv"
RAW_DATA_FILE = "theme_data.csv"

# 🚨 [원천 차단] 뼈대 파일마저 없으면 중단
if not os.path.exists(RAW_DATA_FILE):
    st.error("❌ 기초 뼈대 파일(theme_data.csv)이 깃허브에 없습니다. 파일 업로드를 확인해 주세요.")
    st.stop()

# 데이터 로드 로직 (실시간 수집 파일이 없으면 뼈대에서 가상 데이터 임시 생성하여 대시보드 무조건 실행)
if os.path.exists(THEME_STATUS_FILE):
    theme_summary = pd.read_csv(THEME_STATUS_FILE, encoding="utf-8-sig")
else:
    # 💡 깃허브 액션이 도는 중일 때 화면 멈춤 방지용 가상 데이터 빌드
    raw_df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
    
    # 열 이름 표준화 (수집 엔진과 동일하게 세팅)
    raw_df.columns = [str(col).strip().lower() for col in raw_df.columns]
    if '테마' in raw_df.columns: raw_df = raw_df.rename(columns={'테마': 'theme'})
    
    # 임시 테마 요약본 생성
    theme_list = raw_df['theme'].dropna().unique()
    theme_summary = pd.DataFrame({
        '테마': theme_list,
        '등락률': [0.0] * len(theme_list),
        '화면크기_가중치': [10.0] * len(theme_list)
    })
    st.info("🔄 야후 파이낸스 실시간 주가 동기화 파일 생성 중입니다. 현재 화면은 뼈대 기반 임시 배치입니다.")

# 트리맵에 표시할 문구 가공
def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

theme_summary['핀업라벨'] = theme_summary.apply(make_pinup_label, axis=1)

# ---------------------------------------------------------
# 구역 1: 핀업 바둑판 트리맵 차트 (282개 대규모 테마 완벽 표출)
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

# 트리맵 차트 화면 출력
selected_point = st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={'displayModeBar': False, 'scrollZoom': False},
    on_select="rerun",
    key="treemap_selector"
)

# 첫 번째 순위 테마 자동 선택 기본값
chosen_theme = theme_summary['테마'].iloc[0] if not theme_summary.empty else "선택된 테마 없음"

# 사용자 피드백 반영한 안전한 대형 인덱싱 수정
if selected_point and "points" in selected_point and len(selected_point["points"]) > 0:
    clicked_id = selected_point["points"][0].get("id")
    if clicked_id:
        chosen_theme = clicked_id.split('/')[-1]

st.markdown("<hr style='margin: 15px 0px;'/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 구역 2: 🎯 선택한 테마의 소속 종목 전광판 시세표 (4,115개 연동 구역)
# ---------------------------------------------------------
st.subheader(f"📂 {chosen_theme} 관련 정보")

try:
    raw_df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
    raw_df.columns = [str(col).strip().lower() for col in raw_df.columns]
    
    # 매핑 이름 통일화
    if '테마' in raw_df.columns: raw_df = raw_df.rename(columns={'테마': 'theme'})
    if '종목명' in raw_df.columns: raw_df = raw_df.rename(columns={'종목명': 'name'})
    if '시장' in raw_df.columns: raw_df = raw_df.rename(columns={'시장': 'market'})
    
    # 현재 선택된 테마 필터링
    theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
    
    theme_df_clean = theme_detail_df[['name', 'market']].reset_index(drop=True)
    theme_df_clean.columns = ['🔥 소속 대장 종목명', '📈 소속 시장']
    
    st.markdown(f"### 📊 {chosen_theme} 소속 대장주 전체 라인업 (총 {len(theme_df_clean)}개 종목)")
    st.table(theme_df_clean)

except Exception as e:
    st.info("🔄 상세 종목 리스트를 매핑하는 중입니다...")

# 60초 자동 리셋 시스템 유지
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
