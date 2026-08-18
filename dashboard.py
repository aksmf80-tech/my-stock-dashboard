import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import time
import yfinance as yf

# =========================================================================
# 0. 🛠️ 대시보드 기본 환경 및 다크 테마 디자인 설정 (6px 매니큐어 바 고정)
# =========================================================================
st.set_page_config(
    page_title="1분 라이브 야후 연동 주식 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .block-container { padding-top: 2.5rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.5rem 0 !important; }
    
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 26px !important;
        color: #F8FAFC !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 700 !important; color: #94A3B8 !important; }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 900 !important; color: #FFFFFF !important; }
    
    /* 🔺 상승 종목 전용 매니큐어 바 스타일 컴포넌트 */
    .stock-box-up {
        border-left: 6px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        margin-bottom: 6px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stock-name-up { color: #FFF !important; font-weight: 700 !important; font-size: 14px !important; }
    .stock-rate-up { color: #F87171 !important; font-weight: 800 !important; font-size: 14px !important; }
    
    /* 🔹 하락 종목 전용 매니큐어 바 스타일 컴포넌트 */
    .stock-box-down {
        border-left: 6px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        margin-bottom: 6px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stock-name-down { color: #FFF !important; font-weight: 700 !important; font-size: 14px !important; }
    .stock-rate-down { color: #60A5FA !important; font-weight: 800 !important; font-size: 14px !important; }
    
    /* 트리맵 내부 텍스트 중앙 홀딩 보정 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    </style>
""", unsafe_allow_html=True)
# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (4,115개 뼈대 완벽 연동 + 야후 1분 주가 쪼기)
# =========================================================================
# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (4,115개 뼈대 완벽 연동 + 야후 1분 주가 쪼기)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

# 🎯 장중에 실시간으로 주가를 쪼아와 뼈대에 주입할 핵심 주도주 매핑 리스트입니다.
LIVE_TICKER_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", 
    "레인보우로보틱스": "277810.KQ", "두산로보틱스": "454910.KS", "현대차": "005380.KS",
    "에코프로비엠": "247540.KQ", "엘앤에프": "066970.KQ", "알테오젠": "196170.KQ", 
    "HLB": "028300.KQ", "유한양행": "000100.KS", "코데즈컴바인": "047770.KQ",
    "두산퓨어셀": "336260.KS", "가온칩스": "399720.KQ", "리노공업": "058470.KQ"
}

@st.cache_data(ttl=5)
def load_and_sync_live_data():
    # [뼈대 확보] 깃허브 레포지토리에 심겨있는 4,115개 마스터 데이터 로드
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        try:
            base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        except Exception:
            base_df = pd.DataFrame()
            
        # [컬럼명 유연화 패치] 한글, 영어, 대소문자, 공백 등 어떤 형식이 와도 추적 매핑
        rename_map = {}
        for col in base_df.columns:
            col_str = str(col).strip().lower()
            if '테마' in col_str or 'theme' in col_str:
                rename_map[col] = 'theme'
            elif '종목' in col_str or 'name' in col_str:
                rename_map[col] = 'name'
            elif '등락' in col_str or 'rate' in col_str:
                rename_map[col] = 'rate'
                
        base_df = base_df.rename(columns=rename_map)
    else:
        base_df = pd.DataFrame()

    # 안전하게 컬럼 기본 자리를 채워 안정적인 데이터 테이블 빌드
    if 'theme' not in base_df.columns or base_df.empty: base_df['theme'] = '미분류'
    if 'name' not in base_df.columns or base_df.empty: base_df['name'] = '알수없음'
    if 'rate' not in base_df.columns or base_df.empty: base_df['rate'] = 0.0

    # 🚨 [AttributeError 전면 방어 패치] 판다스 내장 함수 안전 강제 캐스팅
    base_df['theme'] = base_df['theme'].fillna('미분류').astype(str)
    base_df['theme'] = base_df['theme'].apply(lambda x: x.strip())
    
    base_df['name'] = base_df['name'].fillna('알수없음').astype(str)
    base_df['name'] = base_df['name'].apply(lambda x: x.strip())
    
    base_df['rate'] = pd.to_numeric(base_df['rate'], errors='coerce').fillna(0.0).astype(float)

    # 🎯 [형님 전략 장착] 지정한 주도 대장주 리스트만 야후 파이낸스에서 스캔
    try:
        tickers_to_fetch = list(LIVE_TICKER_MAP.values())
        yahoo_data = yf.download(" ".join(tickers_to_fetch), period="1d", interval="1m", progress=False)
        
        # 야후 데이터의 컬럼이 꼬이거나 멀티인덱스로 넘어올 때를 대비해 칼라 정제 처리
        if isinstance(yahoo_data.columns, pd.MultiIndex):
            # Close 레벨의 딕셔너리 정보만 다이렉트로 정렬
            yahoo_close = yahoo_data['Close']
        else:
            yahoo_close = yahoo_data
        
        # 1분 마다 받아온 야후 라이브 등락률을 4,115개 마스터 뼈대 데이터에 실시간 오버라이드
        for stock_name, ticker in LIVE_TICKER_MAP.items():
            if ticker in yahoo_close.columns:
                close_series = yahoo_close[ticker].dropna()
                if len(close_series) >= 2:
                    val_first = float(close_series.iloc)
                    val_last = float(close_series.iloc[-1])
                    if val_first != 0:
                        c_rate = round(((val_last - val_first) / val_first) * 100, 2)
                        # 뼈대 데이터 내의 일치하는 종목 등락률을 진짜 실시간 1분 주가로 치환!
                        base_df.loc[base_df['name'] == stock_name, 'rate'] = c_rate
    except Exception:
        pass # 장외 시간이거나 가벼운 통신 지연 시 기존 깃허브 마스터 정산 파일 수치 유지

    # [테마 스코어 자동 연산] 종목들의 변동을 즉각 반영해 실시간 테마 평균 지수 연산
    agg_df = base_df.groupby('theme')['rate'].mean().reset_index()
    status_df = pd.DataFrame({
        '테마': agg_df['theme'],
        '등락률': agg_df['rate'].round(2),
        '화면크기_가중치': np.linspace(35, 10, len(agg_df)),
        '업데이트시간': [time.strftime('%Y-%m-%d %H:%M:%S')] * len(agg_df)
    })
    
    # 등락률이 높은 주도 테마 순서대로 칼정렬 셰이핑
    status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
    
    return base_df, status_df

raw_df, status_df = load_and_sync_live_data()
update_time = status_df['업데이트시간'].iloc if not status_df.empty else time.strftime('%H:%M:%S')

# -------------------------------------------------------------------------
# 2. 📊 상단 타이틀 및 상위 5개 테마 스코어보드 표출 영역
# -------------------------------------------------------------------------
title_col, time_col = st.columns(2)
with title_col:
    st.markdown("<h2 class='dashboard-title'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:6px; color:#38BDF8; font-size:12px; font-weight:bold;'>🔄 뼈대 연동 + 1분 야후 맥박 동기화: {update_time}</p>", unsafe_allow_html=True)

# 실시간 등락률이 높은 상위 5개 테마 메트릭 전광판 자동 표출
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

top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc[0] if not top_25_themes.empty else "대북/남북경협"

# 左右 스플릿 레이아웃 설정
left_layout, right_layout = st.columns([5.3, 4.7], gap="large")

# 🗺️ 왼쪽 영역: 실시간 테마 히트맵 배치 구역
with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty:
        fig = px.treemap(
            top_25_themes,
            path=['테마'],
            values='화면크기_가중치',    
            color='등락률',             
            color_continuous_scale='RdBu_r',  
            color_continuous_midpoint=0,
            custom_data=['테마']
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b>",
            textfont=dict(size=16, color="white"),
            textposition="middle center"
        )
        fig.update_layout(margin=dict(t=2, b=2, l=2, r=2), height=520)
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                p_target = points_list[0]
                if "label" in p_target and p_target["label"]:
                    st.session_state.selected_theme_click = str(p_target["label"]).strip()

# 🗂️ 오른쪽 영역: 클릭한 테마의 실시간 소속 종목 표출 구역
with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    final_stock_list = []
    theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
    
    if not theme_detail_df.empty:
        for _, row in theme_detail_df.iterrows():
            final_stock_list.append((row['name'], float(row['rate'])))
            
    up_stocks = [(n, r) for n, r in final_stock_list if r >= 0]
    down_stocks = [(n, r) for n, r in final_stock_list if r < 0]
    
    # 🎯 형님이 지적하신 튜플 정렬 로직 완벽 고정 (등락률 실수 값 기준 칼정렬)
    up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
    
    st.markdown("#### 🔺 상승 종목")
    if up_stocks:
        up_cols = st.columns(2)
        for u_idx, (s_name, s_rate) in enumerate(up_stocks[:14]):
            with up_cols[u_idx % 2]:
                st.markdown(f"""
                    <div class='stock-box-up'>
                        <span class='stock-name-up'>🔺 {s_name}</span>
                        <span class='stock-rate-up'>+{s_rate}%</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.text("상승 종목이 없습니다.")
        
    st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔹 하락 종목")
    if down_stocks:
        down_cols = st.columns(2)
        for d_idx, (s_name, s_rate) in enumerate(down_stocks[:14]):
            with down_cols[d_idx % 2]:
                st.markdown(f"""
                    <div class='stock-box-down'>
                        <span class='stock-name-down'>🔹 {s_name}</span>
                        <span class='stock-rate-down'>{s_rate}%</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.text("하락 종목이 없습니다.")

# =========================================================================
# 🎯 [60초 자가 재부팅 엔진] 사용자가 손대지 않아도 1분 마다 화면을 갱신해 야후 라이브 맥박을 유도합니다.
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
