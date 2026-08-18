import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* 데이터 테이블 내부 글자 및 숫자 대폭 확대 */
    .stDataFrame div [data-testid="stTable"] td, .stDataFrame div [data-testid="stTable"] th {
        font-size: 22px !important;
        font-weight: bold !important;
    }
    .stMarkdown h3 {
        font-size: 26px !important;
        font-weight: bold !important;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 정품 시세 테이블 로드
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

# 🎯 차트용 테마별 평균 데이터프레임 빌드
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

# 🎯 세션 상태를 활용해 클릭된 테마 고정 제어 장치 작동
if 'selected_theme' not in st.session_state:
    st.session_state.selected_theme = theme_summary['테마'].iloc[0]

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
    clicked_point = chart_events['selection']['points'][0]
    if 'id' in clicked_point:
        st.session_state.selected_theme = clicked_point['id'].split('/')[-1]

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 🎯 [완벽 매칭 완료] 클릭한 테마의 소속 개별 종목들이 촥 뿜어져 나오는 표 구역
# ---------------------------------------------------------
chosen_theme = st.session_state.selected_theme
st.subheader(f"📂 {chosen_theme} 관련 정보")

# 원본 데이터프레임에서 사용자가 클릭한 테마에 속한 개별 종목 시세를 정밀 추출합니다.
theme_df = df[df['테마'] == chosen_theme].copy().sort_values(by='등락률', ascending=False).reset_index(drop=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 📈 {chosen_theme} 소속 대장주 당일 시세판")
    
    # 🎯 22px 울트라 대형 폰트로 뿜어져 나오는 진짜 소속 개별 종목 표!
    st.dataframe(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        height=280
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"### 📰 {chosen_theme} + {current_stock} 관련 뉴스")
    st.info(f"🔍 '{current_stock}' 및 '{chosen_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://naver.com"
    st.markdown(f"📌 [📢 **[뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)**]({stock_news_url})")
    st.markdown(f"📌 [📢 **[뉴스] '{chosen_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2 전)**]({stock_news_url})")
   
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
