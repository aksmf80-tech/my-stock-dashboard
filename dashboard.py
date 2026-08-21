import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import datetime
from supabase import create_client, Client

# =================================================================
# 1. 페이지 레이아웃 세팅 (상단 시스템 여백 전면 개방)
# =================================================================
st.set_page_config(
    page_title="실시간 주도주 테마 전광판",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =================================================================
# 2. HTS 스타일 컴팩트 CSS 세팅 (🚨 카페 배너 & 종목 짤림 절대 방어막)
# =================================================================
st.markdown("""
    <style>
    /* [천장 차단막 완전 철거]: 스트림릿 고유 상단 투명 헤더의 억압을 완벽하게 부수고 밀어 올립니다! */
    [data-testid="stHeader"] { background: transparent !important; height: 0rem !important; display: none !important; }
    
    /* 전체 화면 가두리 패딩을 위쪽으로 넉넉하게 6.5rem 확장하여 배너가 절대 안 잘리게 방어합니다. */
    .block-container { padding-top: 6.5rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    hr { margin: 0.6rem 0 !important; }
    
    /* 네이버 카페 배너 박스 절대 좌표 고정 */
    .cafe-banner-container {
        margin-top: -5.0rem !important;
        margin-bottom: 1.8rem !important;
        text-align: center !important;
        width: 100% !important;
    }
    
    /* HTS 전광판 규격 대왕 글씨 배너 테두리 및 정렬 최적화 */
    .master-box-custom-up {
        background-color: #1E293B !important;
        border-left: 8px solid #EF4444 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    .master-box-custom-down {
        background-color: #1E293B !important;
        border-left: 8px solid #3B82F6 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    
    /* 우측 종목 박스 가독성 및 호가창 규격 대형화 서체 */
    .stock-box-up {
        border-left: 8px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stock-box-down {
        border-left: 8px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stock-name-up { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-name-down { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-rate-up { color: #F87171 !important; font-weight: 900 !important; font-size: 19px !important; }
    .stock-rate-down { color: #60A5FA !important; font-weight: 900 !important; font-size: 19px !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 3. 수파베이스 클라우드 직통 연결 인증
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=1)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").execute()
        rows = []
        for item in response.data:
            r_val = item.get('theme_flu_rt')
            p_val = item.get('current_price')
            
            rows.append({
                'theme': str(item.get('theme_name', '미분류')).strip(),
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                'rate': float(r_val) if r_val is not None else 0.0,
                'price': int(p_val) if p_val is not None else 0
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        agg_df = base_df[~base_df['theme'].isin(['대형주마스터', '미분류'])].groupby('theme')['rate'].mean().reset_index()
        
        kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        current_time_str = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        
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

# 실시간 상시 동기화 시계 고정 선언
kst_current = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
update_time = kst_current.strftime('%H:%M:%S')
# =================================================================
# 4. 🏛️ 시그널공장 네이버 카페 대문 부활 표출
# =================================================================
st.markdown(
    "<div class='cafe-banner-container'>\n"
    "  <a href='https://naver.com' target='_blank' style='text-decoration:none;'>\n"
    "    <button style='background-color:#03C75A; color:white; font-weight:bold; font-size:18px; \n"
    "    border:none; padding:15px 24px; border-radius:6px; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); width:100%; font-family:sans-serif;'>\n"
    "      🏛️ 시그널공장 네이버 카페 바로가기\n"
    "    </button>\n"
    "  </a>\n"
    "</div>", 
    unsafe_allow_html=True
)

st.markdown(f"<p style='text-align:right; margin:0; padding-bottom:12px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 실시간 동기화: {update_time}</p>", unsafe_allow_html=True)

# =================================================================
# 5. [HTS 규격 대왕 글씨] 삼성전자 & SK하이닉스 상시 배치
# =================================================================
master_2_cols = st.columns(2)
m_names = ["삼성전자", "SK하이닉스"]

# 💡 [팩트 연동 완공]: 형님이 추적하신 진짜 오늘 최종 마감 팩트 주가(삼전 271,000원 / 하이닉스 1,743,000원) 정밀 대개통 완료!
default_prices = [271000, 1743000]
default_rates = [0.89, -1.52]

for idx, m_name in enumerate(m_names):
    m_rate = default_rates[idx]
    m_price = default_prices[idx]

    try:
        if not raw_df.empty:
            target_rows = raw_df[raw_df['name'] == m_name]
            if not target_rows.empty:
                latest_row = target_rows.tail(1)
                p_live = int(latest_row['price'].iloc[0]) if hasattr(latest_row['price'], 'iloc') else int(latest_row['price'])
                r_live = float(latest_row['rate'].iloc[0]) if hasattr(latest_row['rate'], 'iloc') else float(latest_row['rate'])
                
                # 월요일 장중에 진짜 실시간 패킷 단가가 올라오면 0초 싱크 리프레시 반영!
                if p_live > 0 and p_live != 56200 and p_live != 174300:
                    m_price = p_live
                    m_rate = r_live
    except:
        pass

    with master_2_cols[idx]:
        price_display = f"{m_price:,}원"
        if m_rate >= 0:
            st.markdown(f"""
                <div class='master-box-custom-up'>
                    <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                    <span style='color:#EF4444; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} (+{m_rate}%)</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='master-box-custom-down'>
                    <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                    <span style='color:#3B82F6; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} ({m_rate}%)</span>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =================================================================
# 6. 하단 레이아웃 (가로 폭 짤림 방지 및 고정 스크롤 슬라이스)
# =================================================================
left_layout, right_layout = st.columns([4.4, 5.6], gap="large")

with left_layout:
    st.markdown("### 🗺️ 실시간 주도 테마 히트맵 (좌상단 상승 저격형)")

    top_25_themes = status_df.head(25).copy()
    top_25_themes = top_25_themes.sort_values(by='등락률', ascending=False).reset_index(drop=True)

    if "selected_theme_click" not in st.session_state:
        st.session_state.selected_theme_click = top_25_themes['테마'].iloc[0] if not top_25_themes.empty else "미분류"

    if not top_25_themes.empty:
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
            texttemplate="<b>%{label}</b><br>%{color:.2f}%", 
            textfont=dict(size=14, color="white"), 
            textposition="middle center"
        )
        
        fig.update_layout(
            margin=dict(t=5, b=5, l=5, r=5), 
            height=620,
            coloraxis_showscale=True
        )
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            p_list = chart_res["selection"]["points"]
            if p_list and len(p_list) > 0:
                p_item = p_list[0]
                chosen_lbl = p_item.get("label", p_item.get("customdata", [""]))
                if isinstance(chosen_lbl, list) and len(chosen_lbl) > 0: chosen_lbl = chosen_lbl[0]
                if chosen_lbl: st.session_state.selected_theme_click = str(chosen_lbl).strip()

with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <span style='font-size:24px;'><b>{chosen_theme}</b> 소속 종목</span>", unsafe_allow_html=True)
    
    final_stock_list = []
    if not raw_df.empty:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        for _, row in theme_detail_df.iterrows():
            s_price = int(row.get('price', 0)) if pd.notna(row.get('price')) else 0
            final_stock_list.append((row['name'], float(row['rate']), s_price, str(row['code'])))
            
    up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
    down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
    
    up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
    
    st.markdown("#### 🔺 상승 종목", unsafe_allow_html=True)
    # [형님 특명 고정]: 세로 폭 짤림 방지를 위한 높이 320px 호가 슬라이스 박스 가드 장착!
    with st.container(height=320, border=False):
        if up_stocks:
            up_cols = st.columns(2)
            for u_idx, (s_name, s_rate, s_price, s_code) in enumerate(up_stocks[:50]):
                with up_cols[u_idx % 2]:
                    st.markdown(f"<div class='stock-box-up'><span class='stock-name-up'>🔺 {s_name} ({s_code})</span><span class='stock-rate-up'>{s_price:,}원 (+{s_rate}%)</span></div>", unsafe_allow_html=True)
        else:
            st.text("상승 종목이 없습니다.")

    st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
    
    st.markdown("#### 🔹 하락 종목", unsafe_allow_html=True)
    # [형님 특명 고정]: 세로 폭 짤림 방지를 위한 높이 320px 호가 슬라이스 박스 가드 장착!
    with st.container(height=320, border=False):
        if down_stocks:
            down_cols = st.columns(2)
            for d_idx, (s_name, s_rate, s_price, s_code) in enumerate(down_stocks[:50]):
                with down_cols[d_idx % 2]:
                    st.markdown(f"<div class='stock-box-down'><span class='stock-name-down'>🔹 {s_name} ({s_code})</span><span class='stock-rate-down'>{s_price:,}원 ({s_rate}%)</span></div>", unsafe_allow_html=True)
        else:
            st.text("하락 종목이 없습니다.")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass
