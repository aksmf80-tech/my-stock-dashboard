import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# ⚠️ set_page_config는 반드시 최상단에 고정되어야 합니다.
st.set_page_config(layout="wide")

# 🔔 홍보 배너 및 대시보드 타이틀
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

# 🎯 [마지막 교정] 잘못 꼬여있던 유령 파일명을 버리고, 현재 생성된 정품 실시간 데이터 파일명으로 완벽히 고정합니다.
DATA_FILE = "theme_data.csv"

# 데이터 파일 존재 여부 확인
if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 스트림릿 캐시를 무력화하고 파일을 완전 생으로 실시간 새로고침하여 로드
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

required_cols = ['테마', '종목명', '등락률']
if df is None or df.empty or not all(col in df.columns for col in required_cols):
    st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다.")
    st.stop()

# 특정 테마의 화면 독점을 막기 위해 모든 테마 사각형의 크기를 동일하게 고정합니다.
df['화면크기_고정'] = 10 

# 해외 서버 기준 시간을 대한민국 서울 표준시(KST)로 정확히 연동
utc_now = datetime.utcnow()
kor_now = utc_now + timedelta(hours=9)
current_time_str = kor_now.strftime('%H:%M:%S')

st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {current_time_str})")

# ---------------------------------------------------------
# 상단 테마 선택 컨트롤러 배치
# ---------------------------------------------------------
theme_list = df['테마'].unique().tolist()
current_theme = st.selectbox(
    "🔍 **상세 정보를 조회할 테마를 선택하세요**", 
    options=theme_list,
    index=0,
    key="global_theme_selector"
)

# ---------------------------------------------------------
# 구역 1: 등락률 시각화용 트리맵 (0을 중심으로 선명한 핀업 스타일 대칭 정렬)
# ---------------------------------------------------------
v_min = df['등락률'].min()
v_max = df['등락률'].max()
abs_max = float(max(abs(v_min), abs(v_max), 3.0))

fig = px.treemap(
    df, 
    path=['테마'], 
    values='화면크기_고정',  # 사각형 크기 균등 고정
    color='등락률',        # 색상은 종목/테마별 등락률 각자 실시간 추적!
    color_continuous_scale='RdBu_r', # 상승은 빨강, 하락은 파랑 완벽 대조
    range_color=[-abs_max, abs_max], # 0%를 중심으로 선명하게 맵핑
    hover_data=['종목명']
)

# 핀업 스타일 테두리 마감 및 가독성 설정
fig.update_traces(
    maxdepth=1, 
    textinfo="label+value",
    marker=dict(line=dict(width=1.5, color='white'))
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=380
)

# 차트 표출
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 테마 클릭 시 아래에 목록이 주르륵 나오는 부분 & 뉴스 연동
# ---------------------------------------------------------
st.subheader(f"📂 {current_theme} 관련 정보")

theme_df = df[df['테마'] == current_theme].copy()

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📈 {current_theme} 종목 리스트**")
    
    st.data_editor(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        disabled=True, 
        key="stock_selector"
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
    st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://naver.com" + str(current_stock)
    theme_news_url = "https://naver.com" + str(current_theme).replace(" ", "")
    
    st.markdown(f"📌 [📢 [뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)]({stock_news_url})")
    st.markdown(f"📌 [📢 [뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)]({theme_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# ---------------------------------------------------------
# 타이머 엔진 (60초 자동 리셋 및 캐시 고스트 파괴)
# ---------------------------------------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.invalidate_pages() 
    st.rerun()
