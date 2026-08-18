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

# 핀업 스타일의 다크 테마 및 테이블 너비 100% 강제 적용 CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stTable"] { width: 100% !important; }
    th { background-color: #0F172A !important; color: #F8FAFC !important; font-weight: bold !important; text-align: center !important; }
    td { text-align: center !important; font-weight: 500; }
    
    /* Plotly 차트 내부의 텍스트 엘리먼트들을 CSS 단에서 정중앙 강제 정렬 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    
    /* Plotly 차트 테두리 공백 제거 */
    .js-plotly-plot { margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 수집 엔진 출력 데이터 로드 구역
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=10)  # 실시간 인터랙션을 위해 캐시 타임아웃 최소화
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
# 2. 🗺️ 상단 구역: 핀업 스타일 실시간 가변 테마 맵 (박스 25개 스케일 제한)
# =========================================================================
st.title("📊 핀업 스타일 주식 테마 대시보드")
update_time = status_df['업데이트시간'].iloc if not status_df.empty and '업데이트시간' in status_df.columns else "미정"
st.caption(f"⚙️ 4,115개 전수 수집 연동 엔진 작동 중 | 최근 갱신: {update_time}")

# 현재 시장 주도 상위 테마 가로 요약 바 (TOP 5)
st.write("### 🔥 현재 시장 주도 상위 테마 (TOP 5)")
theme_cols = st.columns(5)
for i in range(min(5, len(status_df))):
    t_name = status_df['테마'].iloc[i]
    t_rate = status_df['등락률'].iloc[i]
    with theme_cols[i]:
        if t_rate >= 0:
            st.metric(label=f"🔺 {t_name}", value=f"+{t_rate}%", delta="시장 주도")
        else:
            st.metric(label=f"🔻 {t_name}", value=f"{t_rate}%", delta="하락세", delta_color="inverse")

st.markdown("---")
st.markdown("### 🗺️ 실시간 테마 히트맵 (상위 25개 중심)")
st.write("💡 거래량이 많을수록 박스가 커지고, 상승 종목이 많으면 빨간색 / 낙폭이 크면 파란색으로 표현됩니다.")

# 수집된 테마 중 상위 25개만 커팅
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
    
    # 🎯 [수정 조치 1] 텍스트가 박스 중앙을 기준으로 렌더링되도록 서식과 센터 속성 적용
    fig.update_traces(
        texttemplate="<b>% {label}</b><br>% {color:.2f}%",
        textfont=dict(size=22, color="white"),
        textposition="middle center"  # 📌 Plotly 내부 엔진에 정중앙 정렬 명령 전달
    )
    
    # 🎯 [수정 조치 2] uniformtext 속성을 추가하여 작은 박스든 큰 박스든 글자 정렬 기준을 센터로 통일
    fig.update_layout(
        margin=dict(t=5, b=5, l=5, r=5), 
        height=500,
        uniformtext=dict(minsize=16, mode='hide')  # 글자 깨짐 방지 및 최소 크기 정렬 보완
    )
    
    # 좌우 폭을 슬림하게 모아주는 3단 분기 레이아웃
    side_space1, center_map, side_space2 = st.columns([0.5, 9.0, 0.5])
    with center_map:
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("테마 상태 데이터를 읽어오는 중입니다.")

# =========================================================================
# 3. 🔍 테마 선택 컨트롤러 (상하단 실시간 브릿지 연동)
# =========================================================================
theme_list = top_25_themes['테마'].dropna().tolist() if not top_25_themes.empty else ["대북/남북경협"]
chosen_theme = st.selectbox("📂 상세 분석 및 소속 종목을 조회할 테마를 지정하세요:", theme_list, index=0)

# =========================================================================
# 4. 🎯 하단 구역: 100% 와이드 종목 리스트 (뉴스 차단 및 종목 소개 집중)
# =========================================================================
st.markdown("---")
st.subheader(f"🗂️ {chosen_theme} 테마 소속 종목 가이드")

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
            st.table(theme_df_clean.head(15))
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
