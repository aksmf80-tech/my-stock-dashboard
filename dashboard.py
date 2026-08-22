import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import datetime
from supabase import create_client, Client

# 1. 페이지 레이아웃 세팅 (HTS 스타일 풀화면 기본 개방)
st.set_page_config(
    page_title="실시간 주도주 테마 전광판",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HTS 스타일 컴팩트 CSS 세팅 (🚨 [형님 특명] 좌우 끝단 공백 유격 원천 파괴)
st.markdown("""
    <style>
    /* 상단 기본 헤더 완전 제거 및 밀어올림 */
    [data-testid="stHeader"] { background: transparent !important; height: 0rem !important; display: none !important; }
    
    /* 🚨 [핵심 타격 보정]: 스트림릿 고유의 가로 제한 사슬을 완벽하게 부수고 100% 풀 개방합니다.
       max-width를 무제한(none)으로 풀고, 좌우 패딩 마진을 0.8rem으로 최소화하여 모니터 양쪽 끝 벽면까지 꽉 채웁니다. */
    .block-container { 
        max-width: none !important; 
        padding-top: 1.5rem !important; 
        padding-bottom: 0.5rem !important; 
        padding-left: 0.8rem !important; 
        padding-right: 0.8rem !important; 
    }
    
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    /* 광고 겉틀 박스 높이를 80px 순정 다크 챠콜 박스로 밀착 세팅 */
    .coupang-ad-box {
        background-color: #1E293B !important;
        border: 2px dashed #94A3B8 !important;
        border-radius: 6px !important;
        padding: 0px !important; /* 내부 여백을 0으로 깎아서 광고 알맹이 풀 밀착 */
        text-align: center !important;
        min-height: 80px !important;
        max-height: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
    }
    
    /* 가운데 2구역 종목창 방어막 고정 */
    .stock-box-up {
        border-left: 8px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stock-box-down {
        border-left: 8px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stock-name-up { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-name-down { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-rate-up { color: #F87171 !important; font-weight: 900 !important; font-size: 19px !important; }
    .stock-rate-down { color: #60A5FA !important; font-weight: 900 !important; font-size: 19px !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2-2. 쿠팡 파트너스 광고 코드 직통 삽입 구역 (가로 무제한 확장 버전)
# =================================================================
HTML_AD_1 = """
<iframe src="https://ads-partners.coupang.com/widgets.html?id=1020951&template=carousel&trackingCode=AF2178062&subId=&width=400&height=80&tsource=" width="400" height="80" frameborder="0" scrolling="no" referrerpolicy="unsafe-url"></iframe>
"""

HTML_AD_2 = """
<iframe src="https://coupang.com" width="100%" height="80" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" style="border:none;"></iframe>
"""

HTML_AD_3 = """
<iframe src="https://coupang.com" width="100%" height="80" frameborder="0" scrolling="no" referrerpolicy="unsafe-url" style="border:none;"></iframe>
"""

# 가로 3형제 풀배너 웅장하게 가동 (모니터 끝 단까지 강제 밀착)
ad_col1, ad_col2, ad_col3 = st.columns(3, gap="medium")
with ad_col1:
    st.markdown(f'<div class="coupang-ad-box">{HTML_AD_1}</div>', unsafe_allow_html=True)
with ad_col2:
    st.markdown(f'<div class="coupang-ad-box">{HTML_AD_2}</div>', unsafe_allow_html=True)
with ad_col3:
    st.markdown(f'<div class="coupang-ad-box">{HTML_AD_3}</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)


# 3. 수파베이스 직통 연결 및 데이터 파이프라인
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=15)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").execute()
        rows = []
        for item in response.data:
            r_val = item.get('theme_flu_rt')
            p_val = item.get('current_price')
            t_name = str(item.get('theme_name', '미분류')).strip()
            
            parsed_rate = 0.0
            if r_val is not None and str(r_val).strip() != '':
                try:
                    clean_rate = str(r_val).replace('%', '').replace('+', '').strip()
                    parsed_rate = float(clean_rate)
                except ValueError: parsed_rate = 0.0
            
            parsed_price = 0
            if p_val is not None and str(p_val).strip() != '':
                try:
                    clean_price = str(p_val).replace(',', '').strip()
                    parsed_price = int(float(clean_price))
                except ValueError: parsed_price = 0
            
            rows.append({'theme': t_name, 'name': str(item.get('stock_name', '알수없음')).strip(), 'code': str(item.get('stock_code', '005930')).strip(), 'rate': parsed_rate, 'price': parsed_price})
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        base_df['rate'] = base_df['rate'].fillna(0.0)
        agg_df = base_df.groupby('theme')['rate'].mean().reset_index()
        kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        current_time_str = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        
        status_df = pd.DataFrame({'테마': agg_df['theme'], '등락률': agg_df['rate'].round(2), '업데이트시간': [current_time_str] * len(agg_df)})
        status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
        status_df['화면크기_가중치'] = np.linspace(35, 10, len(status_df)) if len(status_df) > 0 else []
    else:
        status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        
    return base_df, status_df

raw_df, status_df = load_market_data()
kst_current = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
update_time = kst_current.strftime('%H:%M:%S')
# 4. 하단 레이아웃 세팅
if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = ""

if not st.session_state.selected_theme_click and not status_df.empty:
    st.session_state.selected_theme_click = str(status_df['테마'].iloc[0]).strip()

# 3분할 황금 비율 고정 세팅 (3.3 : 3.7 : 3.0)
col_heatmap, col_stock_double, col_chat_room = st.columns([3.3, 3.7, 3.0], gap="medium")

# -----------------------------------------------------------------
# [1구역] 네이버 카페 바로가기 + 실시간 테마 히트맵 (상단 머리 다운 다운)
# -----------------------------------------------------------------
with col_heatmap:
    # 🎯 가운데 종목창과 완벽한 정렬을 위해 강제 다운 상단 마진 12px 주입
    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    st.markdown(f"### 🗺️ 테마 히트맵 <small style='font-size:12px; color:#94A3B8; font-weight:normal;'>({update_time})</small>", unsafe_allow_html=True)

    # 네이버 카페 바로가기 링크 박스
    st.markdown("""
        <a href="https://cafe.naver.com/signalhub" target="_blank" style="text-decoration: none; width: 100%;">
            <div style="background-color: #1E293B; border: 2px solid #2DB400; border-radius: 6px; padding: 14px; text-align: center; color: #2DB400; font-weight: 800; font-size: 16px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer;">
                💚 공식 네이버 카페 바로가기 👉
            </div>
        </a>
    """, unsafe_allow_html=True)

    if not status_df.empty:
        try:
            hts_color_scale = [[0.0, "#0044AA"], [0.45, "#1E293B"], [0.5, "#0F172A"], [0.55, "#2D1515"], [1.0, "#CC0000"]]
            max_rate = float(status_df['등락률'].max())
            min_rate = float(status_df['등락률'].min())
            bound = max(abs(max_rate), abs(min_rate), 1.0)

            fig = px.treemap(
                status_df, path=['테마'], values='화면크기_가중치', color='등락률',             
                color_continuous_scale=hts_color_scale, range_color=[-bound, bound], custom_data=['테마']
            )
            fig.update_traces(texttemplate="<b>%{label}</b><br>%{color:.2f}%", textfont=dict(size=13, color="white", family="sans-serif"), textposition="middle center")
            
            # 🚨 높이를 600px로 조율하여 바닥 라인 정밀 정렬 마감
            fig.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=600, coloraxis_showscale=False, template="plotly_dark")
            chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            if chart_res and isinstance(chart_res, dict) and "selection" in chart_res:
                points_list = chart_res["selection"].get("points", [])
                if points_list and len(points_list) > 0:
                    first_point = points_list[0]
                    if isinstance(first_point, dict):
                        custom_data_val = first_point.get("customdata", [])
                        label_val = first_point.get("label", "")
                        chosen_lbl = custom_data_val[0] if (custom_data_val and isinstance(custom_data_val, list)) else label_val
                        if chosen_lbl and str(chosen_lbl).strip() != st.session_state.selected_theme_click:
                            st.session_state.selected_theme_click = str(chosen_lbl).strip()
                            st.rerun()
        except Exception as chart_err:
            st.error(f"📊 히트맵 컬러 엔진 연동 오류 방어: {chart_err}")
    else:
        st.info("📊 데이터 패킷 수신 대기 중.")
# 데이터 가공 및 정렬 엔진 보정
chosen_theme = str(st.session_state.selected_theme_click).strip()
up_stocks, down_stocks = [], []

if not status_df.empty and chosen_theme and not raw_df.empty:
    raw_df['theme_clean'] = raw_df['theme'].astype(str).str.strip()
    theme_detail_df = raw_df[raw_df['theme_clean'] == chosen_theme].copy()
    
    final_stock_list = []
    for _, row in theme_detail_df.iterrows():
        s_price = int(row.get('price', 0))
        s_name = str(row.get('name', '알수없음')).strip()
        s_rate = float(row.get('rate', 0.0))
        s_code = str(row.get('code', '005930')).strip()
        final_stock_list.append((s_name, s_rate, s_price, s_code))
        
    up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
    down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
    up_stocks = sorted(up_stocks, key=lambda x: x, reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x, reverse=False)

# -----------------------------------------------------------------
# [2구역] 소속 종목 복층형 기둥 (HTS 순정 콤팩트 규격)
# -----------------------------------------------------------------
with col_stock_double:
    st.markdown(f"### 🎯 [{chosen_theme}] 종목 포지션", unsafe_allow_html=True)
    st.markdown(f"<b style='color:#F87171; font-size:14px;'>🔺 소속 상승 종목 ({len(up_stocks)}개)</b>", unsafe_allow_html=True)
    
    with st.container(height=285, border=True):
        if up_stocks:
            for s_name, s_rate, s_price, s_code in up_stocks[:50]:
                st.markdown(f"<div class='stock-box-up' style='padding: 10px 14px !important; margin-bottom: 5px !important;'><span class='stock-name-up' style='font-size:16px !important;'>🔺 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span><span class='stock-rate-up' style='font-size:16px !important;'>{s_price:,}원 (+{s_rate:.2f}%)</span></div>", unsafe_allow_html=True)
        else: st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 상승 종목이 없습니다.</p>", unsafe_allow_html=True)
            
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.markdown(f"<b style='color:#60A5FA; font-size:14px;'>🔹 소속 하락 종목 ({len(down_stocks)}개)</b>", unsafe_allow_html=True)
    
    with st.container(height=285, border=True):
        if down_stocks:
            for s_name, s_rate, s_price, s_code in down_stocks[:50]:
                st.markdown(f"<div class='stock-box-down' style='padding: 10px 14px !important; margin-bottom: 5px !important;'><span class='stock-name-down' style='font-size:16px !important;'>🔹 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span><span class='stock-rate-down' style='font-size:16px !important;'>{s_price:,}원 ({s_rate:.2f}%)</span></div>", unsafe_allow_html=True)
        else: st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 하락 종목이 없습니다.</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------
# [3구역] 🚨 Cbox 순정 다이렉트 익명 소통방 (형님 방 주소 다이렉트 패킷)
# -----------------------------------------------------------------
with col_chat_room:
    # 가운데 종목 기둥과 헤드라인 수평을 맞추기 위한 12px 다운 마진
    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("### 💬 실시간 주주 대화방", unsafe_allow_html=True)
    
    # 🎯 src 주소 내부에 형님의 고유 코드(3559455 및 p6H02s)와 직통 명령어(&sec=main) 결합 완공
    st.markdown("""
        <div style="background-color: #1E293B; border: 2px solid #10B981; border-radius: 8px; padding: 8px; height: 626px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);">
            <iframe 
                src="https://www3.cbox.ws/box/?boxid=3559455&boxtag=p6H02s" 
                marginwidth="0" 
                marginheight="0" 
                frameborder="0" 
                width="100%" 
                height="100%" 
                scrolling="auto"
                allowtransparency="yes"
                allow="autoplay"
                style="border: none; border-radius: 6px; background-color: #0F172A;"
            ></iframe>
        </div>
    """, unsafe_allow_html=True)

# 5. 오토 리프레시 엔진 구동 (15초 자동 브라우저 동기화)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass

