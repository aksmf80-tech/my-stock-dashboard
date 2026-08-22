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
    
    /* 전체 화면 가두리 패딩을 재조정하여 광고판과 히트맵이 밀착되도록 배치합니다. */
    .block-container { padding-top: 2.0rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    /* 쿠팡 광고 배너 스타일 정의 */
    .coupang-ad-box {
        background-color: #1E293B !important;
        border: 2px dashed #94A3B8 !important;
        border-radius: 6px !important;
        padding: 15px !important;
        text-align: center !important;
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        min-height: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
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
# 2-2. 최상단 쿠팡 광고 3자리 가로 배치 레이아웃
# =================================================================
ad_col1, ad_col2, ad_col3 = st.columns(3, gap="medium")
with ad_col1:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (1번 영역)</div>', unsafe_allow_html=True)
with ad_col2:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (2번 영역)</div>', unsafe_allow_html=True)
with ad_col3:
    st.markdown('<div class="coupang-ad-box">📢 쿠팡 광고 자리 (3번 영역)</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
# =================================================================
# 3. 수파베이스 클라우드 직통 연결 인증 및 데이터 파이프라인 (정밀 보정 버전)
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
            
            # 🚨 [수치 변환 보안 방어막]: 특수기호 완벽 차단 및 float 정제
            parsed_rate = 0.0
            if r_val is not None:
                try:
                    clean_rate = str(r_val).replace('%', '').replace('+', '').strip()
                    parsed_rate = float(clean_rate) if clean_rate else 0.0
                except ValueError:
                    parsed_rate = 0.0
            
            # 현재가 정수 안전 변환
            parsed_price = 0
            if p_val is not None:
                try:
                    clean_price = str(p_val).replace(',', '').strip()
                    parsed_price = int(float(clean_price)) if clean_price else 0
                except ValueError:
                    parsed_price = 0
            
            rows.append({
                'theme': t_name,
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                'rate': parsed_rate,
                'price': parsed_price
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        # 결측값 무조건 영점 보정
        base_df['rate'] = base_df['rate'].fillna(0.0)
        
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
# 4. 하단 레이아웃 (형님 특명: 히트맵 3.3 고정 + 종목 상하 복층 + 채팅방 날개)
# =================================================================

# 세션 상태 사전 완전 초기화
if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = ""

# 초기 화면 공백 파괴: 장 시작 시 등락률 대장 1위 테마 자동 프리로딩
if not st.session_state.selected_theme_click and not status_df.empty:
    st.session_state.selected_theme_click = str(status_df['테마'].iloc[0]).strip()

# 🎯 [형님 맞춤형 삼분할 설계 마감]
col_heatmap, col_stock_double, col_chat_room = st.columns([3.3, 3.7, 3.0], gap="medium")

# -----------------------------------------------------------------
# [1구역] 실시간 테마 히트맵 (가로폭 3.3 규격 축소 장착)
# -----------------------------------------------------------------
with col_heatmap:
    st.markdown(f"### 🗺️ 테마 히트맵 <small style='font-size:12px; color:#94A3B8; font-weight:normal;'>({update_time})</small>", unsafe_allow_html=True)

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
                textfont=dict(size=13, color="white", family="sans-serif"),
                textposition="middle center"
            )
            
            fig.update_layout(
                margin=dict(t=5, b=5, l=5, r=5), 
                height=720, 
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
        st.info("📊 데이터 패킷 수신 대기 중.")

# 2구역 연동 데이터 사전 정제 엔진
chosen_theme = str(st.session_state.selected_theme_click).strip()
up_stocks = []
down_stocks = []

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
    
    # 🔺 등락률 기준 내부 튜플 인덱스 정렬 보정
    up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
    down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)

# -----------------------------------------------------------------
# [2구역] 소속 종목 복층형 정렬 기둥 (상승 위 / 하락 아래)
# -----------------------------------------------------------------
with col_stock_double:
    st.markdown(f"### 🎯 [{chosen_theme}] 종목 포지션", unsafe_allow_html=True)
    
    # 상단 복층: 상승 종목 휠 스크롤 박스 (높이 335px 배치)
    st.markdown(f"<b style='color:#F87171; font-size:14px;'>🔺 소속 상승 종목 ({len(up_stocks)}개)</b>", unsafe_allow_html=True)
    with st.container(height=335, border=True):
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
            
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    # 하단 복층: 하락 종목 휠 스크롤 박스 (높이 335px 배치)
    st.markdown(f"<b style='color:#60A5FA; font-size:14px;'>🔹 소속 하락 종목 ({len(down_stocks)}개)</b>", unsafe_allow_html=True)
    with st.container(height=335, border=True):
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

# -----------------------------------------------------------------
# [3구역] 무료 채팅방 날개 자리 홍보 배너 보드
# -----------------------------------------------------------------
with col_chat_room:
    st.markdown("### 💬 VIP 실시간 소통망", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="
            background-color: #1E293B;
            border: 2px solid #10B981;
            border-radius: 8px;
            padding: 25px 20px;
            text-align: center;
            height: 720px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        ">
            <div style="font-size: 45px; margin-bottom: 20px;">🔓</div>
            <h3 style="color: #10B981; font-weight: 900; margin-bottom: 5px; font-size: 24px;">평생 무료 정보 리딩방</h3>
            <p style="color: #94A3B8; font-size: 14px; margin-bottom: 30px; line-height: 1.5;">
                당일 실시간 주도주 테마 정보와<br>
                수파베이스 패킷 급등 시그널을<br>
                조건 없이 가장 빠르게 공유합니다.
            </p>
            <div style="
                background-color: #0F172A;
                border: 1px dashed #34D399;
                padding: 15px;
                border-radius: 6px;
                width: 100%;
                color: #34D399;
                font-weight: 700;
                font-size: 15px;
                margin-bottom: 35px;
            ">
                🔥 [참여 코드: 고정 대기 중]
            </div>
            <a href="https://kakao.com" target="_blank" style="text-decoration: none; width: 100%;">
                <div style="
                    background-color: #10B981;
                    color: white;
                    font-weight: 800;
                    padding: 16px;
                    border-radius: 6px;
                    font-size: 18px;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                    cursor: pointer;
                ">
                    👉 무료 카카오톡방 입장하기
                </div>
            </a>
            <div style="margin-top: 20px; font-size: 12px; color: #64748B;">
                * 본 방은 일체의 유료 결제를 유도하지 않습니다.
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 5. 오토 리프레시 엔진 구동
# =================================================================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass
