import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import time

# =========================================================================
# 0. 🛠️ 대시보드 기본 환경 및 다크 테마 디자인 설정 (기억 3 황금 간격)
# =========================================================================
st.set_page_config(
    page_title="1분 연동 핀업 스타일 주식 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* 천장 잘림 방지 안전 여백 고정 */
    .block-container { padding-top: 4.2rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.5rem 0 !important; }
    
    /* 타이틀과 하단 메트릭 카드의 세로 여백 간격을 시원하게 벌리는 기억 3 규격 */
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 26px !important;
        color: #F8FAFC !important;
        font-weight: 800 !important;
        margin-bottom: 1.8rem !important;
    }
    
    [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 700 !important; color: #94A3B8 !important; }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 900 !important; color: #FFFFFF !important; }
    
    /* 🔺 상승 종목 버튼 왼쪽 테두리 6px 강렬한 레드 매니큐어 바 주입 */
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
    
    /* 🔹 하락 종목 버튼 왼쪽 테두리 6px 시원한 블루 매니큐어 바 주입 */
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
    
    /* 히트맵 글자 중앙 정렬 보정 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    </style>
""", unsafe_allow_html=True)
# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (형님 4,115개 뼈대 + 야후 1분 직동기화 융합 엔진)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

# 🚨 [NameError 방지] 데이터 백업 풀 정의 자리를 완벽하게 수복해 두었습니다.
BACKUP_STOCK_POOL = {
    "대북/남북경협": [("코데즈컴바인", 30.0), ("좋은사람들", 30.0), ("인디에프", 29.81), ("일신석재", 22.24), ("부산산업", 18.5)],
    "반도체 후공정": [("한미반도체", 14.2), ("리노공업", 5.12), ("하나마이크론", 4.3), ("이오테크닉스", 3.12), ("네패스", 2.85)],
    "시스템 반도체": [("삼성전자", -1.2), ("SK하이닉스", -2.5), ("DB하이텍", 0.9), ("가온칩스", 8.3), ("텔레칩스", 3.1)],
    "수소차": [("현대차", 2.1), ("일진하이솔루스", -0.5), ("동아화성", 4.15), ("두산퓨어셀", 8.9), ("에스퓨어셀", 6.3)],
    "전기차 부품": [("에코프로비엠", 4.35), ("엘앤에프", -3.1), ("신흥에스이씨", 1.2), ("상신이디피", 5.4), ("삼기", 3.15)],
    "로봇": [("레인보우로보틱스", 8.9), ("두산로보틱스", 11.2), ("뉴로메카", 5.4), ("로보티즈", 3.15), ("유진로봇", 1.45)],
    "제약/바이오": [("삼성바이오로직스", -0.8), ("셀트리온", 1.5), ("알테오젠", 12.3), ("HLB", 9.45), ("유한양행", 4.2)]
}

LIVE_TICKER_MAP = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", 
    "레인보우로보틱스": "277810.KQ", "두산로보틱스": "454910.KS", "현대차": "005380.KS",
    "에코프로비엠": "247540.KQ", "엘앤에프": "066970.KQ", "알테오젠": "196170.KQ", 
    "HLB": "028300.KQ", "유한양행": "000100.KS", "코데즈컴바인": "047770.KQ",
    "두산퓨어셀": "336260.KS", "가온칩스": "399720.KQ", "리노공업": "058470.KQ"
}

@st.cache_data(ttl=5)
def load_market_data():
    base_df = pd.DataFrame()
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        try:
            base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
            rename_map = {}
            for col in base_df.columns:
                col_str = str(col).strip().lower()
                if '테마' in col_str or 'theme' in col_str: rename_map[col] = 'theme'
                elif '종목' in col_str or 'name' in col_str: rename_map[col] = 'name'
                elif '등락' in col_str or 'rate' in col_str: rename_map[col] = 'rate'
            base_df = base_df.rename(columns=rename_map)
        except Exception:
            base_df = pd.DataFrame()

    if base_df.empty or 'theme' not in base_df.columns:
        sample_rows = []
        for theme_key, stocks in BACKUP_STOCK_POOL.items():
            for name, rate in stocks:
                sample_rows.append({'theme': theme_key, 'name': name, 'rate': rate})
        base_df = pd.DataFrame(sample_rows)
        
    base_df['theme'] = base_df['theme'].fillna('미분류').astype(str).str.strip()
    base_df['name'] = base_df['name'].fillna('알수없음').astype(str).str.strip()
    base_df['rate'] = pd.to_numeric(base_df['rate'], errors='coerce').fillna(0.0).astype(float)

    # 🎯 야후 파이낸스 1분 라이브 실시간 치환 엔진
    try:
        import yfinance as yf
        tickers_to_fetch = list(LIVE_TICKER_MAP.values())
        yahoo_data = yf.download(" ".join(tickers_to_fetch), period="1d", interval="1m", progress=False)
        if not yahoo_data.empty:
            yahoo_close = yahoo_data['Close'] if isinstance(yahoo_data.columns, pd.MultiIndex) else yahoo_data
            for stock_name, ticker in LIVE_TICKER_MAP.items():
                if ticker in yahoo_close.columns:
                    close_series = yahoo_close[ticker].dropna()
                    if len(close_series) >= 2:
                        val_first = float(close_series.iloc)
                        val_last = float(close_series.iloc[-1])
                        if val_first != 0:
                            live_rate = round(((val_last - val_first) / val_first) * 100, 2)
                            base_df.loc[base_df['name'] == stock_name, 'rate'] = live_rate
    except Exception:
        pass

    if os.path.exists(STATUS_FILE) and os.path.getsize(STATUS_FILE) > 0:
        try:
            status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
            status_rename = {}
            for col in status_df.columns:
                col_str = str(col).strip()
                if '테마' in col_str or 'theme' in col_str: status_rename[col] = '테마'
                elif '등락' in col_str or 'rate' in col_str: status_rename[col] = '등락률'
                elif '가중치' in col_str or 'weight' in col_str: status_rename[col] = '화면크기_가중치'
                elif '시간' in col_str or 'time' in col_str: status_rename[col] = '업데이트시간'
            status_df = status_df.rename(columns=status_rename)
        except Exception:
            status_df = pd.DataFrame()
    else:
        status_df = pd.DataFrame()
        
    if status_df.empty or '테마' not in status_df.columns:
        agg_df = base_df.groupby('theme')['rate'].mean().reset_index()
        current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        status_df = pd.DataFrame({
            '테마': agg_df['theme'], '등락률': agg_df['rate'].round(2),
            '화면크기_가중치': np.linspace(35, 10, len(agg_df)), '업데이트시간': [current_time_str] * len(agg_df)
        })
        
    if '등락률' in status_df.columns:
        status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
        
    return base_df, status_df

raw_df, status_df = load_market_data()
update_time = status_df['업데이트시간'].iloc if not status_df.empty and '업데이트시간' in status_df.columns else time.strftime('%H:%M:%S')
# -------------------------------------------------------------------------
# 2. 📊 상단 타이틀 및 상위 5개 테마 메트릭 스코어보드 표출 영역
# -------------------------------------------------------------------------
title_col, time_col = st.columns(2)
with title_col:
    st.markdown("<h2 class='dashboard-title'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:6px; color:#38BDF8; font-size:12px; font-weight:bold;'>🔄 1분 무한 실시간 동기화: {update_time}</p>", unsafe_allow_html=True)

# 실시간 등락률이 높은 상위 5개 테마 메트릭 바 자동 표출
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
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc if not top_25_themes.empty else "대북/남북경협"

# 左右 스플릿 레이아웃 설정
left_layout, right_layout = st.columns([5.3, 4.7], gap="large")

# 🗺️ 왼쪽 영역: 실시간 테마 히트맵 배치 구역
with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty:
        if '등락률' in top_25_themes.columns:
            top_25_themes['등락률'] = top_25_themes['등락률'].fillna(0.0).astype(float)
            
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
                p_target = points_list
                if "label" in p_target and p_target["label"]:
                    st.session_state.selected_theme_click = str(p_target["label"]).strip()
                elif "customdata" in p_target and p_target["customdata"]:
                    st.session_state.selected_theme_click = str(p_target["customdata"]).strip()

# 🗂️ 오른쪽 영역: 클릭한 테마의 소속 종목 24선 고정 표출 구역
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
    
    # 등락률 실수 수치 기준으로 오리지널 내림차순/오름차순 정렬
    up_stocks = sorted(up_stocks, key=lambda x: x, reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x, reverse=False)
    
    # 🚨 [형님의 황금 비율 24선 필터] 상승 대장주 상위 12개만 정밀 컷트
    st.markdown("#### 🔺 상승 종목")
    if up_stocks:
        up_cols = st.columns(2)
        for u_idx, (s_name, s_rate) in enumerate(up_stocks[:12]):
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
    
    # 🚨 [형님의 황금 비율 24선 필터] 하락 마이너주 하위 12개만 정밀 컷트
    st.markdown("#### 🔹 하락 종목")
    if down_stocks:
        down_cols = st.columns(2)
        for d_idx, (s_name, s_rate) in enumerate(down_stocks[:12]):
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
# 🎯 [60초 자가 무한 리런 스케줄러] 1분 마다 화면을 흔들어 데이터 동기화 강제 유도
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
