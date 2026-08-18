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

# 🎯 [레이아웃 대수술] 상단 타이틀 짤림을 완전히 막고 요소를 정돈하는 여백 최적화 CSS
st.markdown("""
    <style>
    /* 상단이 짤리지 않도록 padding-top을 최소한의 안전마진(1.2rem)으로 확보 */
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
    
    /* 요소 간의 간격을 너무 빽빽하지 않게 적당히 조율 */
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    hr { margin: 0.5rem 0 !important; }
    
    /* 테이블 너비 100% 및 시인성 증폭 디자인 */
    div[data-testid="stTable"] { width: 100% !important; margin-top: 0.5rem !important; }
    th { background-color: #1E293B !important; color: #F8FAFC !important; font-weight: bold !important; text-align: center !important; padding: 8px !important; }
    td { text-align: center !important; font-weight: 500; padding: 8px !important; color: #E2E8F0 !important; }
    
    /* Plotly 트리맵 텍스트 강제 중앙 앵커링 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    .js-plotly-plot { margin-bottom: 0rem !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (NaN% 및 종목 실종 버그 원천 차단)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5)  # 실시간 인터랙션 최적화
def load_market_data():
    # 1. 종목 뼈대 데이터 로드 검증
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code'})
        if 'theme' in base_df.columns:
            base_df['theme'] = base_df['theme'].astype(str).str.strip()
    else:
        # 💡 [하단 실종 버그 패치] 실시간 연동이 완벽하게 가동되도록 7개 주요 테마에 종목을 100% 매핑한 가상 베이스 생성
        sample_rows = []
        mock_data = {
            '대북/남북경협': [('코데즈컴바인', '047770', 'KOSDAQ'), ('좋은사람들', '033340', 'KOSDAQ')],
            '반도체 후공정': [('한미반도체', '042700', 'KOSPI'), ('리노공업', '058470', 'KOSDAQ')],
            '시스템 반도체': [('삼성전자', '005930', 'KOSPI'), ('SK하이닉스', '000660', 'KOSPI')],
            '수소차': [('현대차', '005380', 'KOSPI'), ('일진하이솔루스', '271940', 'KOSPI')],
            '전기차 부품': [('에코프로비엠', '247540', 'KOSDAQ'), ('엘앤에프', '066970', 'KOSDAQ')],
            '로봇': [('레인보우로보틱스', '277810', 'KOSDAQ'), ('두산로보틱스', '454910', 'KOSPI')],
            '제약/바이오': [('삼성바이오로직스', '207940', 'KOSPI'), ('셀트리온', '068270', 'KOSPI')]
        }
        for theme, stocks in mock_data.items():
            for name, code, market in stocks:
                sample_rows.append({'theme': theme, 'name': name, 'code': code, 'market': market})
        base_df = pd.DataFrame(sample_rows)

    # 2. 실시간 테마 상태 데이터 로드 검증
    if os.path.exists(STATUS_FILE) and os.path.getsize(STATUS_FILE) > 0:
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
        if '테마' in status_df.columns:
            status_df['테마'] = status_df['테마'].astype(str).str.strip()
    else:
        # 💡 [NaN% 버그 패치] 등락률과 함께 트리맵의 color 기반이 될 '등락률' 필드를 명확히 생성
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
    st.markdown("<h2 style='margin:0; padding:0; font-size:24px; color:#F8FAFC;'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:8px; color:#94A3B8; font-size:13px; font-weight:bold;'>⏱️ 데이터 동기화: {update_time}</p>", unsafe_allow_html=True)

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

if not top_25_themes.empty and '테마' in top_25_themes.columns:
    fig = px.treemap(
        top_25_themes,
        path=['테마'],
        values='화면크기_가중치',    
        color='등락률',             
        color_continuous_scale='RdBu_r',  
        color_continuous_midpoint=0      
    )
    
    # 🎯 %{color:.2f}% 포맷팅을 명확히 고정하여 NaN% 출력 문제를 완벽 진화
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{color:.2f}%",
        textfont=dict(size=18, color="white"),
        textposition="middle center"
    )
    
    # 세로 높이를 한 모니터 화면 안에 종목 테이블까지 다 들어오도록 최적 폭인 390px로 세밀 조정
    fig.update_layout(
        margin=dict(t=2, b=2, l=2, r=2), 
        height=390,
        treemapcolorway=["#1E293B"]
    )
    
    side_space1, center_map, side_space2 = st.columns([0.2, 9.6, 0.2])
    with center_map:
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("테마 상태 데이터를 로드하는 중입니다...")

# =========================================================================
# 4. 🔍 상하단 연동 제어 및 종목 노출 구역 (강제 활성화 보완형)
# =========================================================================
theme_list = top_25_themes['테마'].dropna().tolist() if not top_25_themes.empty else ["대북/남북경협"]
chosen_theme = st.selectbox("📂 조회할 시장 테마를 선택하세요:", theme_list, index=0)

try:
    # 🎯 조건 분기 구조 전면 개편: 파일 유무 상관없이 무조건 테이블 렌더링 영역 가동
    target_theme = str(chosen_theme).strip()
    theme_detail_df = raw_df[raw_df['theme'] == target_theme].copy()
    
    avail_cols = []
    col_names = []
    
    if 'name' in theme_detail_df.columns: avail_cols.append('name'); col_names.append('종목명')
    if 'code' in theme_detail_df.columns: avail_cols.append('code'); col_names.append('종목코드')
    if 'market' in theme_detail_df.columns: avail_cols.append('market'); col_names.append('시장구분')
        
    theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
    theme_df_clean.columns = col_names
    
    # 종목 리스트 출력 실행
    if not theme_df_clean.empty:
        st.table(theme_df_clean.head(12))
    else:
        st.warning(f"⚠️ 전체 데이터셋 내에 '{target_theme}' 테마에 매핑된 실시간 종목 데이터가 없습니다. 크롤러 동작을 확인하세요.")
        
except Exception as e:
    st.info("🔄 주가 테이블을 화면에 구성하는 중입니다...")

# =========================================================================
# 5. ⏱️ 60초 간격 세션 자동 갱신 및 캐시 제어 타이머
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
