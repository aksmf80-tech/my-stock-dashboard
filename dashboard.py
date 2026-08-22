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
# 2. HTS 스타일 컴팩트 CSS 세팅 (🚨 광고 배너 & 종목 짤림 절대 방어막)
# =================================================================
st.markdown("""
    <style>
    /* [천장 차단막 완전 철거]: 스트림릿 고유 상단 투명 헤더의 억압을 완벽하게 부수고 밀어 올립니다! */
    [data-testid="stHeader"] { background: transparent !important; height: 0rem !important; display: none !important; }
    
    /* 전체 화면 가두리 패딩을 위쪽으로 넉넉하게 6.5rem 확장하여 배너가 절대 안 잘리게 방어합니다. */
    .block-container { padding-top: 6.5rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    hr { margin: 0.6rem 0 !important; }
    
    /* 쿠팡 광고 배너 스타일 정의 */
    .coupang-ad-box {
        background-color: #1E293B !important;
        border: 2px dashed #94A3B8 !important;
        border-radius: 6px !important;
        padding: 20px !important;
        text-align: center !important;
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        min-height: 90px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* HTS 전광판 규격 대왕 글씨 배너 테두리 및 정렬 최적화 */
    .master-box-custom-up {
        background-color: #1E293B !important;
        border-left: 8px solid #EF4444 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    .master-box-custom-down {
        background-color: #1E293B !important;
        border-left: 8px solid #3B82F6 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    
    /* 우측 종목 박스 가독성 및 HTS 호가창 규격 대형화 서체 */
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
# 2-2. [형님 특명] 최상단 쿠팡 광고 3자리 가로 배치 레이아웃
# =================================================================
ad_col1, ad_col2, ad_col3 = st.columns(3, gap="medium")
with ad_col1:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (1번 영역)</div>', unsafe_allow_html=True)
with ad_col2:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (2번 영역)</div>', unsafe_allow_html=True)
with ad_col3:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (3번 영역)</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
# =================================================================
# 3. 수파베이스 클라우드 직통 연결 인증 및 데이터 파이프라인 (무필터 순정 버전)
# =================================================================
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
            
            rows.append({
                'theme': t_name,
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                'rate': float(r_val) if r_val is not None else 0.0,
                'price': int(p_val) if p_val is not None else 0
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        agg_df = base_df.groupby('theme')['rate'].mean().reset_index()
        kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        current_time_str = kst_now.strftime('%Y-%m-%d %H:%M:%S')
        
        status_df = pd.DataFrame({
            '테마': agg_df['theme'],
            '등락률': agg_df['rate'].round(2),
            '업데이트시간': [current_time_str] * len(agg_df)
        })
        status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
        status_df['화면크기_가중치'] = np.linspace(35, 10, len(status_df)) if len(status_df) > 0 else []
    else:
        status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        
    return base_df, status_df

# 변수 매핑 무결점 싱크 연결 완료
raw_df, status_df = load_market_data()

kst_current = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
update_time = kst_current.strftime('%H:%M:%S')

# =================================================================
# 5. [HTS 규격 대왕 글씨] 삼성전자 & SK하이닉스 상시 배치
# =================================================================
samsung = raw_df[raw_df['name'] == '삼성전자']
hynix = raw_df[raw_df['name'] == 'SK하이닉스']

top_col1, top_col2 = st.columns(2, gap="medium")
with top_col1:
    if not samsung.empty:
        s_rate = float(samsung.iloc[0]['rate'])
        s_price = int(samsung.iloc[0]['price'])
        box_style = "master-box-custom-up" if s_rate >= 0 else "master-box-custom-down"
        rate_color = "stock-rate-up" if s_rate >= 0 else "stock-rate-down"
        st.markdown(f"""
            <div class="{box_style}">
                <span style='font-size:22px; font-weight:800; color:white;'>삼성전자 (005930)</span>
                <span style='font-size:24px; font-weight:900;' class="{rate_color}">{s_price:,.0f}원 ({s_rate:+.2f}%)</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='master-box-custom-up'><span style='color:white;'>삼성전자 데이터 대기 중</span></div>", unsafe_allow_html=True)

with top_col2:
    if not hynix.empty:
        h_rate = float(hynix.iloc[0]['rate'])
        h_price = int(hynix.iloc[0]['price'])
        box_style = "master-box-custom-up" if h_rate >= 0 else "master-box-custom-down"
        rate_color = "stock-rate-up" if h_rate >= 0 else "stock-rate-down"
        st.markdown(f"""
            <div class="{box_style}">
                <span style='font-size:22px; font-weight:800; color:white;'>SK하이닉스 (000660)</span>
                <span style='font-size:24px; font-weight:900;' class="{rate_color}">{h_price:,.0f}원 ({h_rate:+.2f}%)</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='master-box-custom-up'><span style='color:white;'>SK하이닉스 데이터 대기 중</span></div>", unsafe_allow_html=True)

st.markdown("---")
# =================================================================
# 6. 하단 레이아웃 (핀업 스타일 컬러링 + [좌:상승 / 우:하락] 완공 버전)
# =================================================================

# 세션 상태 사전 완전 초기화
if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = ""

# 초기 화면 공백 파괴: 장 시작 시 등락률 대장 1위 테마 자동 프리로딩
if not st.session_state.selected_theme_click and not status_df.empty:
    st.session_state.selected_theme_click = str(status_df['테마'].iloc[0]).strip()

left_layout, right_layout = st.columns([4.4, 5.6], gap="large")

with left_layout:
    st.markdown(f"### 🗺️ 실시간 주도 테마 히트맵 <small style='font-size:12px; color:#94A3B8; font-weight:normal;'>({update_time} 갱신)</small>", unsafe_allow_html=True)

    if not status_df.empty:
        try:
            # 🎨 [HTS 신호등 5단 그라데이션 엔진]
            hts_color_scale = [
                [0.0, "#0044AA"],   # 하락 극대값
                [0.45, "#1E293B"],  # 미세 하락
                [0.5, "#0F172A"],   # 🎯 정확한 0.00% 보합 영점
                [0.55, "#2D1515"],  # 미세 상승
                [1.0, "#CC0000"]    # 당일 주도 테마 강렬한 레드
            ]
            
            max_rate = float(status_df['등락률'].max())
            min_rate = float(status_df['등락률'].min())
            bound = max(abs(max_rate), abs(min_rate), 1.0)

            fig = px.treemap(
                status_df, 
                path=['테마'], 
                values='화면크기_가중치', 
                color='등락률',             
                color_continuous_scale=hts_color_scale, 
                range_color=[-bound, bound], 
                custom_data=['테마']
            )
            
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{color:.2f}%", 
                textfont=dict(size=15, color="white", family="sans-serif"), 
                textposition="middle center"
            )
            
            fig.update_layout(
                margin=dict(t=5, b=5, l=5, r=5), 
                height=620,
                coloraxis_showscale=False, 
                template="plotly_dark"
            )
            
            chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # 🎯 [트리맵 클릭 0초 반응 매핑]
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
        st.info("📊 수파베이스 양식장 통덤프 패킷을 수신 대기 중입니다.")

with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    
    if not status_df.empty and chosen_theme:
        st.markdown(f"### 🗂️ <span style='font-size:24px;'><b>[{chosen_theme}]</b> 테마 포지션 </span>", unsafe_allow_html=True)
        
        final_stock_list = []
        if not raw_df.empty:
            raw_df['theme_clean'] = raw_df['theme'].astype(str).str.strip()
            theme_detail_df = raw_df[raw_df['theme_clean'] == chosen_theme].copy()
            
            for _, row in theme_detail_df.iterrows():
                s_price = int(row.get('price', 0))
                s_name = str(row.get('name', '알수없음')).strip()
                s_rate = float(row.get('rate', 0.0))
                s_code = str(row.get('code', '005930')).strip()
                final_stock_list.append((s_name, s_rate, s_price, s_code))
                
        # 등락률 포지션별 안전 해체
        up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
        down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
        
        up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
        down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
        
        sub_col1, sub_col2 = st.columns([5.0, 5.0], gap="medium")
        
        with sub_col1:
            st.markdown(f"#### 🔺 소속 상승 종목 ({len(up_stocks)}개)", unsafe_allow_html=True)
            with st.container(height=520, border=True):
                if up_stocks:
                    for s_name, s_rate, s_price, s_code in up_stocks[:50]:
                        st.markdown(
                            f"<div class='stock-box-up' style='padding: 10px 14px !important; margin-bottom: 5px !important;'>"
                            f"  <span class='stock-name-up' style='font-size:16px !important;'>🔺 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-up' style='font-size:16px !important;'>{s_price:,}원 (+{s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                else:
                    st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 상승 종목이 없습니다.</p>", unsafe_allow_html=True)
                    
        with sub_col2:
            st.markdown(f"#### 🔹 소속 하락 종목 ({len(down_stocks)}개)", unsafe_allow_html=True)
            with st.container(height=520, border=True):
                if down_stocks:
                    for s_name, s_rate, s_price, s_code in down_stocks[:50]:
                        st.markdown(
                            f"<div class='stock-box-down' style='padding: 10px 14px !important; margin-bottom: 5px !important;'>"
                            f"  <span class='stock-name-down' style='font-size:16px !important;'>🔹 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-down' style='font-size:16px !important;'>{s_price:,}원 ({s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                else:
                    st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 하락 종목이 없습니다.</p>", unsafe_allow_html=True)
    else:
        st.markdown("### 🗂️ 소속 종목 리더보드")
        st.info("🔄 데이터 패킷 수신 대기 중...")

# =================================================================
# 7. 오토 리프레시 엔진 구동
# =================================================================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass
