import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import time

# =========================================================================
# 0. 🛠️ 대시보드 기본 환경 및 100% 와이드 레이아웃 설정
# =========================================================================
st.set_page_config(
    page_title="핀업 스타일 테마 맵 대시보드",
    layout="wide",  # 📰 뉴스 없는 와이드 100% 레이아웃 강제 활성화
    initial_sidebar_state="collapsed"
)

# 🎯 [수정 조치] 화면 상단의 모든 마진, 패딩, 여백을 극단적으로 줄여 요소를 위로 끌어올리는 CSS
st.markdown("""
    <style>
    /* 전체 화면 여백 최소화 */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    
    /* 요소 간의 기본 간격(Gap) 줄이기 */
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    
    /* 구분선(hr) 마진 압축 */
    hr { margin: 0.5rem 0 !important; }
    
    /* 테이블 스타일 튜닝 */
    div[data-testid="stTable"] { width: 100% !important; margin-top: 0rem !important; }
    th { background-color: #0F172A !important; color: #F8FAFC !important; font-weight: bold !important; text-align: center !important; padding: 6px !important; }
    td { text-align: center !important; font-weight: 500; padding: 6px !important; }
    
    /* Plotly 차트 내부의 텍스트 엘리먼트 정중앙 강제 정렬 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    .js-plotly-plot { margin-bottom: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 수집 엔진 출력 데이터 로드 구역
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=10)
def load_market_data():
    if os.path.exists(BASE_FILE):
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code'})
    else:
        sample = {
            'theme': ['대북/남북경협', '대북/남북경협', '반도체 후공정', '시스템 반도체', '시스템 반도체'], 
            'name': ['코데즈컴바인', '좋은사람들', '한미반도체', '삼성전자', '코데즈컴바인'], 
            'code': ['047770', '033340', '042700', '005930', '047770'], 
            'market': ['KOSDAQ', 'KOSDAQ', 'KOSPI', 'KOSPI', 'KOSDAQ']
        }
        base_df = pd.DataFrame(sample)

    if os.path.exists(STATUS_FILE):
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
    else:
        current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        status_df = pd.DataFrame({
            '테마': ['대북/남북경협', '반도체 후공정', '시스템 반도체', '수소차', '전기차 부품', '로봇', '제약/바이오'],
            '등락률': [24.75, 16.37, -11.09, -13.62, -13.36, -14.47, -14.78],
            '화면크기_가중치': [35.0, 28.0, 20.0, 18.0, 15.0, 12.0, 10.0],
            '업데이트시간': [current_time_str] * 7
        })
        
    return base_df, status_df

raw_df, status_df = load_market_data()

# =========================================================================
# 2. 🗺️ 상단 구역: 타이틀 및 실시간 주도 테마 TOP 5 (한 줄 배치로 축소)
# =========================================================================
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

# 🎯 [수정 조치] 타이틀과 갱신 안내 텍스트를 한 줄로 결합하여 세로 공간 대폭 절약
title_col, time_col = st.columns([7, 3])
with title_col:
    st.markdown("<h2 style='margin:0; padding:0;'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin-top:10px; color:#94A3B8; font-size:13px;'>⏱️ {update_time}</p>", unsafe_allow_html=True)

# 🎯 [수정 조치] "현재 시장 주도 상위 테마" 같은 중간 안내 텍스트 라인 전부 삭제 후 즉시 메트릭 배치
theme_cols = st.columns(5)
for i in range(min(5, len(status_df))):
    t_name = status_df['테마'].iloc[i]
    t_rate = status_df['등락률'].iloc[i]
    with theme_cols[i]:
        if t_rate >= 0:
            st.metric(label=f"🔺 {t_name}", value=f"+{t_rate}%")
        else:
            st.metric(label=f"🔻 {t_name}", value=f"{t_rate}%", delta_color="inverse")

st.markdown("---")

# =========================================================================
# 3. 🗺️ 중간 구역: 실시간 테마 히트맵 (상위 25개 중심)
# =========================================================================
# 🎯 [수정 조치] 히트맵 상단의 불필요한 가이드 텍스트 및 전수 수집 관련 잔여 설명글 전면 삭제
top_25_themes = status_df.head(25).copy()

if not top_25_themes.empty and '테마' in top_25_themes.columns and '화면크기_가중치' in top_25_themes.columns:
    fig = px.treemap(
        top_25_themes,
        path=['테마'],
        values='화면크기_가중치',    
        color='등락률',             
        color_continuous_scale='RdBu_r',  
        color_continuous_midpoint=0      
    )
    
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%%{color:.2f}%",
        textfont=dict(size=20, color="white"),
        textposition="middle center"
    )
    
    # 🎯 하단 종목을 끌어올리기 위해 히트맵 세로 높이를 500px -> 420px로 콤팩트하게 다이어트
    fig.update_layout(
        margin=dict(t=2, b=2, l=2, r=2), 
        height=420,
        treemapcolorway=["#1E293B"]
    )
    
    side_space1, center_map, side_space2 = st.columns([0.5, 9.0, 0.5])
    with center_map:
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("테마 상태 데이터를 읽어오는 중입니다.")

# =========================================================================
# 4. 🔍 테마 선택 및 하단 100% 와이드 종목 리스트 연동 구역 (바짝 끌어올림)
# =========================================================================
# 🎯 [수정 조치] 중간 구분선(hr)과 중복 텍스트 제목들을 전부 제거하고, 셀렉트박스와 테이블을 바로 붙임
theme_list = top_25_themes['테마'].dropna().tolist() if not top_25_themes.empty else ["대북/남북경협"]

# 셀렉트박스와 리스트 제목을 결합하여 한눈에 들어오게 처리
chosen_theme = st.selectbox("📂 조회할 테마를 지정하면 아래 대장 종목 리스트가 즉시 연동됩니다:", theme_list, index=0)

try:
    if not raw_df.empty and 'theme' in raw_df.columns:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
        avail_cols = []
        col_names = []
        
        if 'name' in theme_detail_df.columns: avail_cols.append('name'); col_names.append('종목명')
        if 'code' in theme_detail_df.columns: avail_cols.append('code'); col_names.append('종목코드')
        if 'market' in theme_detail_df.columns: avail_cols.append('market'); col_names.append('시장구분')
            
        theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
        theme_df_clean.columns = col_names
        
        if not theme_df_clean.empty:
            st.table(theme_df_clean.head(12)) # 화면 컷에 맞게 최대 12개 깔끔하게 노출
        else:
            st.info(f"현재 `{chosen_theme}` 테마에 매핑된 실시간 종목 정보가 존재하지 않습니다.")
    else:
        st.error("데이터셋에 'theme' 열이 존재하지 않거나 데이터 구조가 올바르지 않습니다.")
except Exception as e:
    st.info("🔄 실시간 동기화 데이터를 그리드에 바인딩하는 중입니다...")

# =========================================================================
# 5. ⏱️ 60초 간격 세션 자동 갱신 및 캐시 제어 타이머
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
