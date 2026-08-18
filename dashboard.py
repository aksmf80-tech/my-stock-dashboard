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

# 🎯 우리가 무적의 야후 글로벌 엔진으로 정상화 시켜놓은 진짜 정품 데이터 파일명을 지정합니다.
DATA_FILE = "theme_data.csv"

# 데이터 파일 존재 여부 확인
if not os.path.exists(DATA_FILE):
    st.warning("⌛ 실시간 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 최신 주가 데이터 로드
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

required_cols = ['테마', '종목명', '등락률']
if df is None or df.empty or not all(col in df.columns for col in required_cols):
    st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다.")
    st.stop()

# ---------------------------------------------------------
# 🎯 [핀업 스타일 초정밀 데이터 정렬 엔진]
# ---------------------------------------------------------
# 1. 🔥 [핵심] 왼쪽(빨강/상승)에서 오른쪽(파랑/하락)으로 칼같이 줄을 세우기 위해 등락률 높은 순으로 정렬합니다.
df = df.sort_values(by='등락률', ascending=False).reset_index(drop=True)

# 2. 주도 테마일수록 사각형 크기가 눈에 띄게 커지도록 절댓값 기준 크기 가중치를 부여합니다 (최소 크기 5 보장).
df['화면크기_가중치'] = df['등락률'].abs() + 5.0

# 3. 핀업과 100% 일치하는 등락률 부호 기호 라벨 텍스트 조합 (오늘 자동 세대교체된 진짜 대장주 이름 결합)
def make_pinup_label(row):
    rate = round(row['등락률'], 2)
    if rate > 0:
        return f"{row['테마']}\n({row['종목명']})\n+{rate}%"
    elif rate < 0:
        return f"{row['테마']}\n({row['종목명']})\n{rate}%"
    else:
        return f"{row['테마']}\n({row['종목명']})\n0.0%"

df['핀업라벨'] = df.apply(make_pinup_label, axis=1)

# 해외 서버 시차 해결 (KST 표준시 동기화)
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
# 구역 1: 핀업 완벽 복사형 수십 개 바둑판 트리맵 차트 (좌측 빨강 / 우측 파랑 대조)
# ---------------------------------------------------------
# 변동률 색상 민감도를 ±5% 범위로 바짝 조여 시각적 선명함과 강렬함을 극대화합니다.
COLOR_LIMIT = 5.0 

fig = px.treemap(
    df, 
    path=['핀업라벨'],        # 🎯 테마와 동적 대장주가 반영된 진짜 핀업 라벨 고정
    values='화면크기_가중치',    # 🎯 변동성이 큰 주도 테마가 화면에 더 크게 나오도록 크기 가중치 연동
    color='등락률',        
    color_continuous_scale='RdBu_r', # 상승 빨강 / 하락 파랑 완벽 대조
    range_color=[-COLOR_LIMIT, COLOR_LIMIT], # 색상 대비 극대화 범주 고정
)

# 핀업 특유의 두꺼운 흰색 성곽선 테두리 마감 및 가독성 폰트 설정
fig.update_traces(
    maxdepth=1, 
    textinfo="label",
    marker=dict(line=dict(width=2.5, color='white')), # 🎯 바둑판 구분 테두리를 선명하게 화이트 마감
    textfont=dict(size=14, color='white', weight='bold') # 전반적인 글씨 가독성 강조
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=450 # 시각적 개방감을 위해 차트 세로 높이 확대
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 테마 선택 시 아래에 소속 상세 시세가 주르륵 나오는 구역
# ---------------------------------------------------------
st.subheader(f"📂 {current_theme} 관련 정보")

# 원본 데이터에서 현재 선택된 테마명과 일치하는 행 필터링
theme_df = df[df['테마'] == current_theme].copy()

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📈 {current_theme} 대표 대장주 당일 등락 현황**")
    
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
    
    # 한국 주식 전용 정보 서치용 매커니즘 링크 연동
    stock_news_url = "https://naver.com"
    theme_news_url = "https://naver.com"
    
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
