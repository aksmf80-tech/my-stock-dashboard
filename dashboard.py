import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

# 🎯 [투명인간 버그 완전 파괴] st.table 전용 글자 강제 백색 코팅 CSS 주입
st.markdown("""
    <style>
    /* 순수 데이터 표(st.table) 내부의 모든 종목명과 숫자를 무조건 찬란한 흰색 왕글씨로 고정 */
    table {
        color: #FFFFFF !important;
        font-size: 24px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    thead tr th {
        color: #FFD700 !important; /* 표 헤더 제목 컬럼은 황금색 강조 */
        font-size: 22px !important;
        font-weight: bold !important;
    }
    tbody tr td {
        color: #FFFFFF !important;
        background-color: #1A1D24 !important; /* 가독성을 위한 최적의 핀업 배경색 매칭 */
    }
    /* 서브 타이틀 글자 크기 확대 */
    .stMarkdown h3 {
        font-size: 26px !important;
        font-weight: bold !important;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🔔 홍보 배너 및 대시보드 타이틀
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 정품 시세 테이블 로드
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

# 차트용 테마별 평균 데이터프레임 빌드
theme_summary = df.groupby('테마')['등락률'].mean().reset_index()
theme_summary = theme_summary.sort_values(by='등락률', ascending=False).reset_index(drop=True)
theme_summary['화면크기_가중치'] = theme_summary['등락률'].abs() + 5.0

def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

theme_summary['핀업라벨'] = theme_summary.apply(make_pinup_label, axis=1)

# 해외 서버 시차 해결 (KST 동기화)
utc_now = datetime.utcnow()
kor_now = utc_now + timedelta(hours=9)
current_time_str = kor_now.strftime('%H:%M:%S')

st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {current_time_str})")

# 이름 불일치 버그 완전 해결 초기값 연동
if 'selected_theme' not in st.session_state or st.session_state.selected_theme not in theme_summary['테마'].values:
    st.session_state.selected_theme = theme_summary['테마'].iloc

# ---------------------------------------------------------
# 구역 1: 핀업 완벽 복사형 트리맵 차트 (클릭 이벤트 완전 활성화)
# ---------------------------------------------------------
COLOR_LIMIT = 5.0 

fig = px.treemap(
    theme_summary, 
    path=['테마'], 
    values='화면크기_가중치',    
    color='등락률',        
    color_continuous_scale='RdBu_r', 
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], 
)

fig.update_traces(
    maxdepth=1, 
    text=theme_summary['핀업라벨'], 
    textinfo="text",      
    marker=dict(line=dict(width=3.0, color='white')), 
    textfont=dict(size=18, color='white', weight='bold'), 
    textposition="middle center" 
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=450 
)

# 차트 표출 및 클릭 감지 센서 연결
chart_events = st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={'displayModeBar': False},
    on_select="rerun"
)

# 사용자가 마우스로 네모 칸을 클릭했을 때 세션 기억 소자에 즉시 저장!
if chart_events and 'selection' in chart_events and chart_events['selection']['points']:
    clicked_point = chart_events['selection']['points']
    if 'id' in clicked_point:
        st.session_state.selected_theme = clicked_point['id'].split('/')[-1]

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 🎯 [순백색 점등 완료] 클릭한 테마의 소속 종목들이 하얗고 선명하게 터져 나오는 구역
# ---------------------------------------------------------
chosen_theme = st.session_state.selected_theme
st.subheader(f"📂 {chosen_theme} 관련 정보")

# 원본 데이터프레임에서 사용자가 클릭한 테마에 속한 개별 종목 시세를 정밀 추출합니다.
theme_df = df[df['테마'] == chosen_theme].copy().sort_values(by='등락률', ascending=False).reset_index(drop=True)

# 🎯 대시보드 표 가독성을 직관적으로 가꿔줄 한글 컬럼명 변환
theme_df_clean = theme_df[['종목명', '등락률']].copy()
theme_df_clean.columns = ['🔥 소속 대장 종목명', '📈 실시간 등락률 (%)']

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 📊 {chosen_theme} 소속 대장주 당일 시세판")
    
    # 🎯 [핵심 교정] 스타일 무력화 버그를 깨부수는 st.table로 전면 격상 교체!
    # 어둠 속에 묻혀있던 글자들이 24px 대형 흰색 글씨로 시원하게 뿜어져 나옵니다!
    st.table(theme_df_clean)
    
with col2:
    st.markdown(f"### 📰 {chosen_theme} 뉴스 브리핑")
    st.info(f"🔍 '{chosen_theme}' 시장 동향 및 주도주 흐름에 대한 실시간 뉴스 요약...")
    
    stock_news_url = "https://naver.com"
    st.markdown(f"📌 [📢 **[실시간 뉴스] '{chosen_theme}' 주도 테마, 대량 거래대금 몰리며 시장 강력 견인 (방금 전)**]({stock_news_url})")
    st.markdown(f"📌 [📢 **[시황 분석] 글로벌 공급망 재편 수혜주 부각... 블로그 본문에서 대장주 매매 타점 공개**]({stock_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# 60초 자동 리셋
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.invalidate_pages() 
    st.rerun()
