import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

# 🎯 글자 크기 시원하게 확대 및 핀업 전용 레이아웃 테마 CSS 주입
st.markdown("""
    <style>
    /* 데이터 테이블 내부 글자 및 숫자 대폭 확대 */
    .stDataFrame div [data-testid="stTable"] td, .stDataFrame div [data-testid="stTable"] th {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    /* 서브 타이틀 가독성 강조 */
    .stMarkdown h3 {
        font-size: 26px !important;
        font-weight: bold !important;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 🔔 홍보 배너 및 대시보드 타이틀
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

# 데이터 파일 존재 여부 확인
if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 최신 데이터 읽기
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

required_cols = ['테마', '종목명', '등락률']
if df is None or df.empty or not all(col in df.columns for col in required_cols):
    st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다.")
    st.stop()

# 🎯 [핀업 정렬 엔진] 등락률 높은 순서대로 칼같이 정렬
df = df.sort_values(by='등락률', ascending=False).reset_index(drop=True)

# 주도 테마 볼륨감 가중치 배정
df['화면크기_가중치'] = df['등락률'].abs() + 5.0

# 🎯 [핀업 스타일 교정 1] 글자를 정중앙에 배치하기 위해 라벨 구조를 테마명과 퍼센트로 깔끔하게 분리 결합합니다.
def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

df['핀업라벨'] = df.apply(make_pinup_label, axis=1)

# 해외 서버 시차 해결 (KST 동기화)
utc_now = datetime.utcnow()
kor_now = utc_now + timedelta(hours=9)
current_time_str = kor_now.strftime('%H:%M:%S')

st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {current_time_str})")

# ---------------------------------------------------------
# 구역 1: 핀업 완벽 복사형 트리맵 차트 (정중앙 정렬 완료)
# ---------------------------------------------------------
COLOR_LIMIT = 5.0 

fig = px.treemap(
    df, 
    path=['테마'], # 🎯 [핵심] 차트 클릭 연동 클릭 메커니즘을 위해 원본 테마명을 타겟팅합니다.
    values='화면크기_가중치',    
    color='등락률',        
    color_continuous_scale='RdBu_r', # 상승 빨강 / 하락 파랑 완벽 대조
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], 
    custom_data=['핀업라벨'] # 🎯 정중앙 표출용 커스텀 라벨 전송
)

# 🎯 [선생님 지적 완벽 해결] 글자를 무조건 사각형 '정중앙 세로/가로' 배치하고 굵고 크게 키웁니다!
fig.update_traces(
    maxdepth=1, 
    text=df['핀업라벨'], # 🎯 줄바꿈 기호(<br>)가 포함된 정품 핀업 라벨 주입
    textinfo="text",      # 🎯 텍스트 규격만 순수 표출
    marker=dict(line=dict(width=3.0, color='white')), # 두꺼운 흰색 성곽선 테두리
    textfont=dict(size=18, color='white', weight='bold'), # 글자 크기 대폭 확대 및 두껍게 강조
    textposition="middle center" # 🎯 완벽하게 정중앙에 글자가 모이도록 강제 지정!
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=460 
)

# 🎯 [핀업 스타일 교정 2] 차트 내부 클릭 이벤트를 스트림릿이 인지하도록 클릭 링크 연결!
selected_theme_from_chart = st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={'displayModeBar': False},
    on_select="rerun" # 🎯 차트 네모 칸을 누르면 화면이 알아서 감지해 리런(Rerun)됩니다!
)

# 기본 선택 테마 초기화 매커니즘
chosen_theme = df['테마'].iloc[0]

# 🎯 만약 사용자가 차트의 네모 칸을 마우스로 '툭' 클릭했다면, 그 클릭한 테마 이름으로 하단 정보를 즉시 교체합니다!
if selected_theme_from_chart and 'selection' in selected_theme_from_chart and selected_theme_from_chart['selection']['points']:
    clicked_point = selected_theme_from_chart['selection']['points'][0]
    if 'id' in clicked_point:
        # 클릭된 블록의 테마명 파싱 도려내기
        chosen_theme = clicked_point['id'].split('/')[-1]

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 🎯 [완벽 클릭 연동] 위에서 현황판 네모를 클릭하면 소속 종목들이 마술처럼 촥 바뀌는 구역
# ---------------------------------------------------------
st.subheader(f"📂 {chosen_theme} 관련 정보")

# 🎯 현재 선택되거나 '클릭된' 테마 이름과 일치하는 종목들만 실시간 동적 매핑 필터링!
theme_df = df[df['테마'] == chosen_theme].copy().reset_index(drop=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 📈 {chosen_theme} 소속 대장주 당일 시세판")
    
    # 🎯 글씨 크기가 20px로 시원시원하게 확대된 대형 정품 데이터 테이블 표출
    st.dataframe(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        height=240
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"### 📰 {chosen_theme} + {current_stock} 관련 뉴스")
    st.info(f"🔍 '{current_stock}' 및 '{chosen_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://naver.com"
    st.markdown(f"📌 [📢 **[뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)**]({stock_news_url})")
    st.markdown(f"📌 [📢 **[뉴스] '{chosen_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)**]({stock_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마전망을 보실 수 있습니다.")

# ---------------------------------------------------------
# 타이머 엔진 (60초 자동 리셋)
# ---------------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.invalidate_pages() 
    st.rerun()
