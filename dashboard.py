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
    page_title="실시간 핀업 스타일 주식 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =================================================================
# 2. 형님의 초경량 컴팩트 그리드 + 대장주 대형 가로형 1줄 전광판 통합 CSS
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
    
    [data-testid="stMetricLabel"] { font-size: 16px !important; font-weight: 700 !important; color: #94A3B8 !important; }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 900 !important; color: #FFFFFF !important; }
    
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
    
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }

    /* 시장 주도 마스터 보드 가로형 정렬 및 대형 스케일업 */
    .master-box-up {
        border-left: 8px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 24px 28px !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    .master-box-down {
        border-left: 8px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 24px 28px !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    .master-name { color: #FFFFFF !important; font-weight: 800 !important; font-size: 24px !important; }
    .master-rate-up { color: #F87171 !important; font-weight: 900 !important; font-size: 26px !important; }
    .master-rate-down { color: #60A5FA !important; font-weight: 900 !important; font-size: 26px !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 3. 수파베이스 클라우드 직통 연동 세팅
# =================================================================
# 💡 [필수 변경] 형님의 실제 수파베이스 주소와 아논 키값을 정확히 적어주세요!
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 5초 초단기 버퍼 캐시 데이터 로더
@st.cache_data(ttl=5)
# =================================================================
# 3. 수파베이스 클라우드 직통 연동 세팅 (108번 라인 부근 교체)
# =================================================================
# 5초 초단기 버퍼 캐시 데이터 로더
@st.cache_data(ttl=5)
def load_market_data():
    try:
        # 💡 [교체 핵심] 존재하지 않는 stock_prices 조인을 빼고 stock_skeleton 테이블만 단일 조회합니다.
        response = supabase.table("stock_skeleton").select("*").execute()
        
        rows = []
        for item in response.data:
            # 원장 테이블의 실제 컬럼명 구조와 1:1 완벽 맵핑
            rows.append({
                'theme': str(item.get('theme_name', '미분류')).strip(),
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                # ⚠️ 한투 컬럼명이 flct_rate가 아니라 수파베이스 원장의 fluctuation 입니다!
                'rate': float(item.get('fluctuation', 0.0)),
                'price': int(item.get('current_price', 0))
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ 데이터 파싱 중 에러 발생: {e}")
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    # 테마별 평균 등락률 산출 및 정렬 구조화 (기존 로직 유지)
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

    # 테마별 평균 등락률 산출 및 정렬 구조화
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

# 데이터 동기화 가동
raw_df, status_df = load_market_data()
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else time.strftime('%H:%M:%S')
# =================================================================
# 4. 상단 헤더 및 5대 대장 주도 테마 스코어보드 출력
# =================================================================
title_col, time_col = st.columns(2)
with title_col:
    st.markdown("<h2 class='dashboard-title'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:6px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 실시간 동기화: {update_time}</p>", unsafe_allow_html=True)

theme_cols = st.columns(5)
for i in range(min(5, len(status_df))):
    t_name = status_df['테마'].iloc[i]
    t_rate = status_df['등락률'].iloc[i]
    with theme_cols[i]:
        if t_rate >= 0: st.metric(label=f"🔺 {t_name}", value=f"+{t_rate}%")
        else: st.metric(label=f"🔻 {t_name}", value=f"{t_rate}%")

st.markdown("---")

# =================================================================
# 4. 시장 주도 마스터 보드 (초슬림 가로 1줄 4열 전광판 통합 배치)
# =================================================================
st.markdown("### 🏛️ 시장 주도 마스터 보드", unsafe_allow_html=True)

# 💡 st.columns(4)를 사용해 가로로 딱 4개의 칸을 생성하여 한 줄로 나란히 배치합니다.
master_4_cols = st.columns(4)

# [1~2번째 칸] 코스피 & 코스닥 지수 매핑
for idx, idx_name in enumerate(["코스피", "코스닥"]):
    idx_rate = 0.0
    idx_price = 0
    if not raw_df.empty and 'name' in raw_df.columns:
        target_idx_row = raw_df[raw_df['name'] == idx_name]
        if not target_idx_row.empty:
            idx_rate = float(target_idx_row['rate'].iloc[0])
            idx_price = int(target_idx_row['price'].iloc[0]) if idx_name == "코스피" else float(target_idx_row['price'].iloc[0])
            
    with master_4_cols[idx]: # 0번 칸(코스피), 1번 칸(코스닥) 진입
        price_str = f"{idx_price:,.2f}" if idx_name == "코스닥" and isinstance(idx_price, float) else f"{int(idx_price):,}"
        if idx_rate >= 0:
            st.markdown(
                f"  <div class='master-box-up'>\n"
                f"    <span class='master-name'>📈 {idx_name}</span>\n"
                f"    <span class='master-rate-up'>{price_str}pt (+{idx_rate}%)</span>\n"
                f"  </div>\n", 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"  <div class='master-box-down'>\n"
                f"    <span class='master-name'>📉 {idx_name}</span>\n"
                f"    <span class='master-rate-down'>{price_str}pt ({idx_rate}%)</span>\n"
                f"  </div>\n", 
                unsafe_allow_html=True
            )

# [3~4번째 칸] 삼성전자 & SK하이닉스 대장주 매핑
for idx, m_name in enumerate(["삼성전자", "SK하이닉스"]):
    m_rate = 0.0
    m_price = 0
    if not raw_df.empty and 'name' in raw_df.columns:
        target_row = raw_df[raw_df['name'] == m_name]
        if not target_row.empty:
            m_rate = float(target_row['rate'].iloc[0])
            m_price = int(target_row['price'].iloc[0])
            
    with master_4_cols[idx + 2]: # 2번 칸(삼성전자), 3번 칸(SK하이닉스) 진입
        if m_rate >= 0:
            st.markdown(
                f"  <div class='master-box-up'>\n"
                f"    <span class='master-name'>🏛️ {m_name}</span>\n"
                f"    <span class='master-rate-up'>{m_price:,}원 (+{m_rate}%)</span>\n"
                f"  </div>\n", 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"  <div class='master-box-down'>\n"
                f"    <span class='master-name'>🏛️ {m_name}</span>\n"
                f"    <span class='master-rate-down'>{m_price:,}원 ({m_rate}%)</span>\n"
                f"  </div>\n", 
                unsafe_allow_html=True
            )

st.markdown("---")



# =================================================================
# 5. 하단 레이아웃: 왼쪽 실시간 트리맵 히트맵 / 오른쪽 선택 테마 상세 소속 종목 분할 배치
# =================================================================
top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc[0] if not top_25_themes.empty else "미분류"

left_layout, right_layout = st.columns([5.3, 4.7], gap="large")

with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty:
        top_25_themes['등락률'] = top_25_themes['등락률'].fillna(0.0).astype(float)
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
                p_target = p_list[0]
                chosen_lbl = p_target.get("label", p_target.get("customdata", ""))
                if isinstance(chosen_lbl, list) and len(chosen_lbl) > 0: chosen_lbl = chosen_lbl[0]
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
    
    up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
    
    st.markdown("#### 🔺 상승 종목", unsafe_allow_html=True)
    if up_stocks:
        up_cols = st.columns(2)
        for u_idx, (s_name, s_rate, s_price, s_code) in enumerate(up_stocks[:12]):
            with up_cols[u_idx % 2]:
                st.markdown(
                    f"  <div class='stock-box-up'>\n"
                    f"    <span class='stock-name-up'>🔺 {s_name} ({s_code})</span>\n"
                    f"    <span class='stock-rate-up'>{s_price:,}원 (+{s_rate}%)</span>\n"
                    f"  </div>\n", 
                    unsafe_allow_html=True
                )
    else: st.text("상승 종목이 없습니다.")
        
    st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔹 하락 종목", unsafe_allow_html=True)
    if down_stocks:
        down_cols = st.columns(2)
        for d_idx, (s_name, s_rate, s_price, s_code) in enumerate(down_stocks[:12]):
            with down_cols[d_idx % 2]:
                st.markdown(
                    f"  <div class='stock-box-down'>\n"
                    f"    <span class='stock-name-down'>🔹 {s_name} ({s_code})</span>\n"
                    f"    <span class='stock-rate-down'>{s_price:,}원 ({s_rate}%)</span>\n"
                    f"  </div>\n", 
                    unsafe_allow_html=True
                )
    else: st.text("하락 종목이 없습니다.")

# =================================================================
# 6. 대시보드 60초 주기 무한 롤링 백그라운드 새로고침 루틴 가동
# =================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
 # 60초가 되기 전까지 1초씩 쉬면서 백그라운드 타이머가 쉬지 않고 돌게 만듭니다.
    time.sleep(1)
    st.rerun()
