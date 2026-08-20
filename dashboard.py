import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from supabase import create_client, Client

# =================================================================
# 1. 스트림릿 페이지 레이아웃 및 컴팩트 뼈대 세팅
# =================================================================
st.set_page_config(
    page_title="실시간 주식 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =================================================================
# 2. HTS 스타일 컴팩트 CSS 세팅
# =================================================================
st.markdown("""
    <style>
    .block-container { padding-top: 4.2rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.5rem 0 !important; }
    
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 26px !important;
        color: #F8FAFC !important;
        font-weight: 800 !important;
        margin-bottom: 1.8rem !important;
    }
    
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
    
    .master-box-up {
        border-left: 6px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 8px 14px !important;
        margin-bottom: 4px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    .master-box-down {
        border-left: 6px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 8px 14px !important;
        margin-bottom: 4px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    .master-name { color: #FFFFFF !important; font-weight: 800 !important; font-size: 14px !important; }
    .master-rate-up { color: #F87171 !important; font-weight: 900 !important; font-size: 14px !important; }
    .master-rate-down { color: #60A5FA !important; font-weight: 900 !important; font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)
# =================================================================
# 3. 수파베이스 클라우드 데이터 연동
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=5)
def load_market_data():
    try:
        response = supabase.table("stock_skeleton").select("*").execute()
        rows = []
        for item in response.data:
            rows.append({
                'theme': str(item.get('theme_name', '미분류')).strip(),
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                'rate': float(item.get('fluctuation', 0.0)),
                'price': int(item.get('current_price', 0))
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        agg_df = base_df.groupby('theme')['rate'].mean().reset_index()
        current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        status_df = pd.DataFrame({
            '테마': agg_df['theme'],
            '등락률': agg_df['rate'].round(2),
            '화면크기_가중치': np.linspace(35, 10, len(agg_df)),
            '업데이트시간': [current_time_str] * len(agg_df)
        })
        status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
    else:
        status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        
    return base_df, status_df

raw_df, status_df = load_market_data()
update_time = status_df['업데이트시간'].iloc if not status_df.empty and '업데이트시간' in status_df.columns else time.strftime('%H:%M:%S')
# =================================================================
# 4. 최상단 가로 1줄 4열 마스터 보드 배치
# =================================================================
title_col, time_col = st.columns(2)
with title_col:
    st.markdown("<h2 class='dashboard-title'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:14px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 실시간 동기화: {update_time}</p>", unsafe_allow_html=True)

master_4_cols = st.columns(4)

for idx, idx_name in enumerate(["코스피", "코스닥"]):
    idx_rate = 0.0
    idx_price = 0
    if not raw_df.empty and 'name' in raw_df.columns:
        target_idx_row = raw_df[raw_df['name'] == idx_name]
        if not target_idx_row.empty:
            idx_rate = float(target_idx_row['rate'].iloc[0])
            idx_price = float(target_idx_row['price'].iloc[0])
            
    with master_4_cols[idx]:
        price_str = f"{idx_price:,.2f}" if idx_name == "코스닥" else f"{int(idx_price):,}"
        if idx_rate >= 0:
            st.markdown(f"<div class='master-box-up'><span class='master-name'>📈 {idx_name}</span><span class='master-rate-up'>{price_str}pt (+{idx_rate}%)</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='master-box-down'><span class='master-name'>📉 {idx_name}</span><span class='master-rate-down'>{price_str}pt ({idx_rate}%)</span></div>", unsafe_allow_html=True)

for idx, m_name in enumerate(["삼성전자", "SK하이닉스"]):
    m_rate = 0.0
    m_price = 0
    if not raw_df.empty and 'name' in raw_df.columns:
        target_row = raw_df[raw_df['name'] == m_name]
        if not target_row.empty:
            m_rate = float(target_row['rate'].iloc[0])
            m_price = int(target_row['price'].iloc[0])
            
    with master_4_cols[idx + 2]:
        if m_rate >= 0:
            st.markdown(f"<div class='master-box-up'><span class='master-name'>🏛️ {m_name}</span><span class='master-rate-up'>{m_price:,}원 (+{m_rate}%)</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='master-box-down'><span class='master-name'>🏛️ {m_name}</span><span class='master-rate-down'>{m_price:,}원 ({m_rate}%)</span></div>", unsafe_allow_html=True)

st.markdown("---")
# =================================================================
# 5. 하단 레이아웃: 왼쪽 실시간 트리맵 히트맵 / 오른쪽 선택 테마 상세 소속 종목 분할 배치
# =================================================================
top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc if not top_25_themes.empty else "미분류"

left_layout, right_layout = st.columns([5.3, 4.7], gap="large")

with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty:
        top_25_themes['등락률'] = top_25_themes['등락률'].fillna(0.0).astype(float)
        
        # 💡 [순정 복구 완료] ValueError 충돌을 일으키던 모든 찌꺼기 옵션을 제거한 안전 규격입니다.
        fig = px.treemap(
            top_25_themes, path=['테마'], values='화면크기_가중치', color='등락률',             
            color_continuous_scale='RdBu_r', color_continuous_midpoint=0, custom_data=['테마']
        )
        fig.update_traces(texttemplate="<b>%{label}</b>", textfont=dict(size=16, color="white"), textposition="middle center")
        fig.update_layout(margin=dict(t=2, b=2, l=2, r=2), height=520)
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            p_list = chart_res["selection"]["points"]
            if p_list and len(p_list) > 0:
                p_target = p_list
                chosen_lbl = p_target.get("label", p_target.get("customdata", ""))
                if isinstance(chosen_lbl, list) and len(chosen_lbl) > 0: chosen_lbl = chosen_lbl
                if chosen_lbl: st.session_state.selected_theme_click = str(chosen_lbl).strip()
with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    final_stock_list = []
    if not raw_df.empty:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        for _, row in theme_detail_df.iterrows():
            final_stock_list.append((row['name'], float(row['rate']), int(row['price']), str(row['code'])))
            
    up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
    down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
    
    up_stocks = sorted(up_stocks, key=lambda x: x, reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x, reverse=False)
    
    st.markdown("#### 🔺 상승 종목", unsafe_allow_html=True)
    if up_stocks:
        up_cols = st.columns(2)
        for u_idx, (s_name, s_rate, s_price, s_code) in enumerate(up_stocks[:12]):
            with up_cols[u_idx % 2]:
                st.markdown(f"<div class='stock-box-up'><span class='stock-name-up'>🔺 {s_name} ({s_code})</span><span class='stock-rate-up'>{s_price:,}원 (+{s_rate}%)</span></div>", unsafe_allow_html=True)
    else:
        st.text("상승 종목이 없습니다.")

    st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔹 하락 종목", unsafe_allow_html=True)
    if down_stocks:
        down_cols = st.columns(2)
        for d_idx, (s_name, s_rate, s_price, s_code) in enumerate(down_stocks[:12]):
            with down_cols[d_idx % 2]:
                st.markdown(f"<div class='stock-box-down'><span class='stock-name-down'>🔹 {s_name} ({s_code})</span><span class='stock-rate-down'>{s_price:,}원 ({s_rate}%)</span></div>", unsafe_allow_html=True)
    else:
        st.text("하락 종목이 없습니다.")

# =================================================================
# 6. 60초 주기 자동 리프레시 타이머 (들여쓰기 0칸 완전 차단 독립형)
# =================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
else:
    time.sleep(1)
    st.rerun()
