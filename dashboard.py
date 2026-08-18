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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 화면 상단의 모든 마진, 패딩, 여백을 최소화하여 요소를 위로 끌어올리는 CSS
st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
    hr { margin: 0.4rem 0 !important; }
    div[data-testid="stTable"] { width: 100% !important; margin-top: 0rem !important; }
    th { background-color: #0F172A !important; color: #F8FAFC !important; font-weight: bold !important; text-align: center !important; padding: 6px !important; }
    td { text-align: center !important; font-weight: 500; padding: 6px !important; }
    
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    .js-plotly-plot { margin-bottom: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 수집 엔진 출력 데이터 로드 및 정제 구역 (텍스트 매핑 정밀 보완)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5) # 연동 딜레이를 없애기 위해 캐시 타임아웃 최소화
def load_market_data():
    # 1. 종목 뼈대 데이터 로드
    if os.path.exists(BASE_FILE):
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        # 무조건 공백을 제거하여 텍스트 매핑 불일치 차단
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code'})
        if 'theme' in base_df.columns:
            base_df['theme'] = base_df['theme'].astype(str).str.strip()
    else:
        sample = {
            'theme': ['대북/남북경협', '대북/남북경협', '반도체 후공정', '시스템 반도체', '시스템 반도체'], 
            'name': ['코데즈컴바인', '좋은사람들', '한미반도체', '삼성전자', '코데즈컴바인'], 
            'code': ['047770', '033340', '042700', '005930', '047770'], 
            'market': ['KOSDAQ', 'KOSDAQ', 'KOSPI', 'KOSPI', 'KOSDAQ']
        }
        base_df = pd.DataFrame(sample)

    # 2. 실시간 테마 상태 데이터 로드
    if os.path.exists(STATUS_FILE):
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
        if '테마' in status_df.columns:
            status_df['테마'] = status_df['테마'].astype(str).str.strip()
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
# 2. 🗺️ 상단 구역: 타이틀 및 실시간 주도 테마 TOP 5
# =========================================================================
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

title_col, time_col = st.columns([7, 3])
with title_col:
    st.markdown("<h2 style='margin:0; padding:0; font-size:26px;'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin-top:8px; color:#94A3B8; font-size:13px; font-weight:bold;'>⏱️ 장마감 동기화: {update_time}</p>", unsafe_allow_html=True)

theme_cols = st.columns(5)
for i in range(min(5, len(status_df))):
    t_name = status_df['테마'].iloc[i]
    t_rate = status_df['등락률'].iloc[i]
    with theme_cols[i]:
        if t_rate >= 0:
            st.metric(label=f"🔺 {t_name}", value=f"+{t_rate}%")
        else:
            st.metric(label=f"🔻 {t_name}", value=f"{t_rate}%")

st.markdown("---")

# =========================================================================
# 3. 🗺️ 중간 구역: 실시간 테마 히트맵 (상위 25개 중심)
# =========================================================================
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
        texttemplate="<b>%{label}</b><br>%{color:.2f}%",
        textfont=dict(size=19, color="white"),
        textposition="middle center"
    )
    
    fig.update_layout(
        margin=dict(t=2, b=2, l=2, r=2), 
        height=400,
        treemapcolorway=["#1E293B"]
    )
    
    side_space1, center_map, side_space2 = st.columns([0.3, 9.4, 0.3])
    with center_map:
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("테마 상태 데이터를 읽어오는 중입니다.")

# =========================================================================
# 4. 🔍 [핵심 수정 완료] 상하단 연동 제어 및 종목 노출 구역
# =========================================================================
theme_list = top_25_themes['테마'].dropna().tolist() if not top_25_themes.empty else ["대북/남북경협"]

# 💡 사용자가 위 히트맵이나 셀렉트박스에서 고른 테마명이 대칭되도록 정렬
chosen_theme = st.selectbox("📂 조회할 시장 테마를 선택하세요:", theme_list, index=0)

try:
    if not raw_df.empty and 'theme' in raw_df.columns:
        # 데이터 정합성 불일치 문제를 완벽하게 패치 (양끝 공백 제거 후 1:1 하드 매핑)
        target_theme = str(chosen_theme).strip()
        theme_detail_df = raw_df[raw_df['theme'] == target_theme].copy()
        
        avail_cols = []
        col_names = []
        
        if 'name' in theme_detail_df.columns: avail_cols.append('name'); col_names.append('종목명')
        if 'code' in theme_detail_df.columns: avail_cols.append('code'); col_names.append('종목코드')
        if 'market' in theme_detail_df.columns: avail_cols.append('market'); col_names.append('시장구분')
            
        theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
        theme_df_clean.columns = col_names
        
        # 📌 텅 비는 문제를 차단하고 리스트 상위 대장 종목 무조건 출력 (최대 12개)
        if not theme_df_clean.empty:
            st.table(theme_df_clean.head(12))
        else:
            # 💡 혹시라도 매핑이 비었을 때 원인을 파악할 수 있도록 로깅 방어막 마련
            st.warning(f"⚠️ 현재 수집된 전체 데이터셋(`theme_data.csv`) 내에 '{target_theme}' 테마와 정확히 일치하는 소속 종목명이 없습니다. 텍스트 철자나 공백을 확인해 주세요.")
    else:
        st.error("데이터셋에 'theme' 열이 존재하지 않거나 구조가 올바르지 않습니다.")
except Exception as e:
    st.info(f"🔄 주가 데이터를 바인딩하는 중 오류 발생: {e}")

# =========================================================================
# 5. ⏱️ 세션 타이머 제어
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
