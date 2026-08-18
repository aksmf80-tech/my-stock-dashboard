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
    # 1. 종목 뼈대 데이터 로드 (한 종목이 여러 테마에 속할 수 있는 원본 DB)
    if os.path.exists(BASE_FILE):
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code'})
    else:
        # 가상 방어용 종목 데이터 (한 종목이 여러 테마에 중복 매핑된 예시)
        sample = {
            'theme': ['대북/남북경협', '대북/남북경협', '반도체 후공정', '시스템 반도체', '시스템 반도체'], 
            'name': ['코데즈컴바인', '좋은사람들', '한미반도체', '삼성전자', '코데즈컴바인'], # 코데즈컴바인 중복 속성 예시
            'code': ['047770', '033340', '042700', '005930', '047770'], 
            'market': ['KOSDAQ', 'KOSDAQ', 'KOSPI', 'KOSPI', 'KOSDAQ']
        }
        base_df = pd.DataFrame(sample)

    # 2. 실시간 테마 상태 데이터 로드 (수집 엔진 아웃풋)
    if os.path.exists(STATUS_FILE):
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
    else:
        # 가상 방어용 상위 테마 상태 데이터 (크기 가중치 및 등락률 포함)
        current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        status_df = pd.DataFrame({
            '테마': ['대북/남북경협', '반도체 후공정', '시스템 반도체', '수소차', '전기차 부품', '로봇', '제약/바이오'],
            '등락률': [24.75, 16.37, -11.09, -13.62, -13.36, -14.47, -14.78],
            '화면크기_가중치':, # 거래량 반영 가중치
            '업데이트시간': [current_time_str] * 7
        })
        
    return base_df, status_df

raw_df, status_df = load_market_data()

# =========================================================================
# 2. 🗺️ 상단 구역: 핀업 스타일 실시간 가변 테마 맵 (박스 25개 스케일 제한)
# =========================================================================
st.title("📊 핀업 스타일 주식 테마 대시보드")
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"
st.caption(f"⚙️ 4,115개 전수 수집 연동 엔진 작동 중 | 최근 갱신: {update_time}")

st.markdown("### 🗺️ 실시간 테마 히트맵 (상위 25개 중심)")
st.write("💡 거래량이 많을수록 박스가 커지고, 상승 종목이 많으면 빨간색 / 낙폭이 크면 파란색으로 표현됩니다.")

# 수집된 테마 중 상위 25개만 커팅하여 레이아웃 밀도 최적화
top_25_themes = status_df.head(25).copy()

if not top_25_themes.empty:
    # 핀업 특유의 빨강/파랑 히트맵을 생성하는 Plotly 트리맵 컴포넌트
    fig = px.treemap(
        top_25_themes,
        path=['테마'],
        values='화면크기_가중치',    # 📦 거래량/대금이 많을수록 박스가 커짐
        color='등락률',             # 🎨 상승률이 높으면 빨강(Red), 낙폭이 크면 파랑(Blue)
        color_continuous_scale='RdBu_r',  # 주식 직관 컬러 스케일 (Red-Blue 반전)
        color_continuous_midpoint=0      # 0%를 기준으로 색상 분기
    )
    
    # 맵 내부 텍스트 템플릿 세팅 (테마명과 등락률 동시 표출)
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{color:.2f}%",
        textfont=dict(size=14, color="white")
    )
    fig.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=350)
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
        # 사용자가 위에서 지정한 테마에 소속된 종목만 필터링 (중복 속성 자동 해결)
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
        avail_cols = []
        col_names = []
        
        if 'name' in theme_detail_df.columns: avail_cols.append('name'); col_names.append('종목명')
        if 'code' in theme_detail_df.columns: avail_cols.append('code'); col_names.append('종목코드')
        if 'market' in theme_detail_df.columns: avail_cols.append('market'); col_names.append('시장구분')
            
        theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
        theme_df_clean.columns = col_names
        
        # 뉴스를 걷어낸 자리에 시원하게 100% 너비로 테이블 배치 (상위 15개 노출)
        if not theme_df_clean.empty:
            st.table(theme_df_clean.head(15))
        else:
            st.info(f"현재 `{chosen_theme}` 테마에 매핑된 실시간 종목 정보가 존재하지 않습니다.")
    else:
        st.error("종목 데이터베이스의 테마 식별 열 구조를 다시 점검해 주세요.")
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
