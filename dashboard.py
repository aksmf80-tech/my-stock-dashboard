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
# 3. 수파베이스 클라우드 직통 연결 인증 및 데이터 파이프라인 (🚨 실종된 가스관 복구 완공 버전)
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🎯 [형님 특명 트래픽 방어막]: 30만 명 디도스 폭탄을 완벽하게 분쇄하는 15초 캐시 락 기지 구축!
@st.cache_data(ttl=15)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").execute()
        rows = []
        for item in response.data:
            s_code = str(item.get('stock_code', '')).strip()
            s_name = str(item.get('stock_name', '')).strip()
            
            # 🔥 [가짜 데이터 암살 가드]: SKELETON_BASE 뼈대는 국물도 없이 쳐내서 화면 정화 완공!
            if "SKELETON" in s_name.upper() or "SKELETON" in s_code.upper():
                continue
                
            r_val = item.get('theme_flu_rt')
            p_val = item.get('current_price')
            t_name = str(item.get('theme_name', '미분류')).strip()
            
            rows.append({
                'theme': t_name,
                'name': s_name,
                'code': s_code,
                'rate': float(r_val) if r_val is not None else 0.0,
                'price': int(p_val) if p_val is not None else 0  # 싱싱한 리얼 단가 안착
            })
        raw_df = pd.DataFrame(rows)
    except Exception as e:
        raw_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not raw_df.empty:
        agg_df = raw_df.groupby('theme')['rate'].mean().reset_index()
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
        
    return raw_df, status_df

# 💥 [실종 수로 긴급 복구]: 잘려 나갔던 정품 데이터 쟁반 출격 명령 수로를 다시 강제로 안착시킵니다!
raw_df, status_df = load_market_data()

# 시계 연산 영점 동기화
kst_current = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
update_time = kst_current.strftime('%H:%M:%S')

# =================================================================
# 4. 🏛️ 시그널공장 네이버 카페 대문 부활 표출 (정품 주소 사수)
# =================================================================
st.markdown(
    "<div class='cafe-banner-container'>\n"
    "  <a href='https://cafe.naver.com/signalhub' target='_blank' style='text-decoration:none;'>\n"
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
# 5. [HTS 규격 대왕 글씨] 삼성전자 & SK하이닉스 상시 배치 ➡️ 향후 광고 배너 입점 구역
# =================================================================
st.empty()

# =================================================================
# 6. 하단 레이아웃 (🚨 주말 NaN% 에러 완치 및 미니 채팅창 개통 최종본)
# =================================================================
# 🎯 [세션 및 레이아웃 초기화] 다른 소스코드 충돌을 원천 방어합니다.
if 'selected_theme_click' not in st.session_state:
    st.session_state.selected_theme_click = None

# 좌측 히트맵과 우측 대형 리더보드의 순정 황금 비율(4.4 : 5.6)을 완벽하게 사수합니다.
bottom_cols = st.columns([4.4, 5.6], gap="medium")

# -----------------------------------------------------------------
# 🗺️ [좌측 칸]: 실시간 주도 테마 히트맵 (🚨 주말 에러 원천 봉쇄)
# -----------------------------------------------------------------
with bottom_cols[0]:
    st.markdown("### 🗺️ 실시간 주도 테마 히트맵")
    
    if raw_df is not None and not raw_df.empty:
        # 테마별 평균 등락률 산출 연산 수송
        theme_df = raw_df.groupby('theme').agg({
            'rate': 'mean',
            'code': 'count'
        }).reset_index()
        theme_df.columns = ['theme', 'avg_rate', 'stock_count']
        theme_df['theme_clean'] = theme_df['theme'].str.replace('ROOM_', '')
        
        # Plotly 트리맵 엔진 구동 (순정 세팅 유지)
        import plotly.express as px
        fig = px.treemap(
            theme_df,
            path=['theme_clean'],
            values='stock_count',
            color='avg_rate',
            color_continuous_scale=[[0, '#3B82F6'], [0.5, '#111827'], [1, '#EF4444']],
            color_continuous_midpoint=0.0
        )
        
        # 🚨 [치명적 버그 수정]: 주말에 데이터가 없어도 에러 안 나게 서식을 날것 그대로 매핑
        fig.update_traces(
            texttemplate="<b>{label}</b><br>{color}%",
            textposition="inside",
            insidetextfont=dict(size=14, color='white'),
            hovertemplate="<b>{label}</b><br>평균 등락률: {color}%"
        )
        
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=520,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        # 클릭 이벤트 스트림릿 연동 가드
        from streamlit_plotly_events import plotly_events
        selected_point = plotly_events(fig, click_event=True, hover_event=False, override_height=520)
        
        if selected_point:
            try:
                clicked_idx = selected_point[0]['point_number']
                chosen_theme = theme_df.iloc[clicked_idx]['theme_clean']
                st.session_state.selected_theme_click = chosen_theme
            except:
                pass

# -----------------------------------------------------------------
# 🗂️ [우측 칸]: 테마 포지션 + 💥 우측 날개 미니 라이브 채팅창 완공
# -----------------------------------------------------------------
with bottom_cols[1]:
    # 선택된 테마 대화방 가동 (기본값은 첫 번째 테마 강제 맵핑)
    if st.session_state.selected_theme_click:
        chosen_theme = st.session_state.selected_theme_click
    else:
        chosen_theme = theme_df.iloc[0]['theme_clean'] if 'theme_df' in locals() and not theme_df.empty else "IT 서비스"
        
    st.markdown(f"### 🗂️ [{chosen_theme}] 테마 포지션 및 소통방")
    
    # 테마에 소속된 정품 종목 데이터 가로채기
    if raw_df is not None and not raw_df.empty:
        theme_detail_df = raw_df[raw_df['theme'].str.replace('ROOM_', '') == chosen_theme].copy()
        
        if not theme_detail_df.empty:
            # 상승/하락 종목 분류 분기 가동
            up_stocks = theme_detail_df[theme_detail_df['rate'] >= 0].sort_values(by='rate', ascending=False)
            down_stocks = theme_detail_df[theme_detail_df['rate'] < 0].sort_values(by='rate', ascending=True)
            
            # 🚨 가로 칸을 3개로 분할하여 상승, 하락, 채팅방을 칼대칭 배치합니다!
            sub_cols = st.columns([4.2, 4.2, 3.6], gap="small")
            
            # 칸 1. 소속 상승 종목 렌더링
            with sub_cols[0]:
                st.markdown("<span style='color:#EF4444; font-weight:700; font-size:15px;'>🔺 소속 상승 종목</span>", unsafe_allow_html=True)
                up_box_html = "<div style='height:460px; overflow-y:auto; border:1px solid #374151; padding:8px; border-radius:6px; background-color:#111827;'>"
                for _, row in up_stocks.iterrows():
                    s_name = row.get('name', '종목명')
                    s_code = row.get('code', '000000')
                    s_price = int(row.get('price', 0))
                    s_rate = float(row.get('rate', 0.0))
                    up_box_html += f"""
                    <div style='display:flex; justify-content:content; align-items:center; margin-bottom:8px; border-bottom:1px solid #1F2937; padding-bottom:4px;'>
                        <span style='color:#FFF; font-weight:600; font-size:13px;'>{s_name} <small style='color:#9CA3AF;'>{s_code}</small></span>
                        <span style='color:#EF4444; font-weight:700; font-size:13px; margin-left:auto;'>{s_price:,}원 (+{s_rate:.2f}%)</span>
                    </div>
                    """
                up_box_html += "</div>"
                st.markdown(up_box_html, unsafe_allow_html=True)
                
            # 칸 2. 소속 하락 종목 렌더링
            with sub_cols[1]:
                st.markdown("<span style='color:#3B82F6; font-weight:700; font-size:15px;'>🔹 소속 하락 종목</span>", unsafe_allow_html=True)
                down_box_html = "<div style='height:460px; overflow-y:auto; border:1px solid #374151; padding:8px; border-radius:6px; background-color:#111827;'>"
                if down_stocks.empty:
                    down_box_html += "<div style='color:#9CA3AF; text-align:center; margin-top:20px; font-size:12px;'>당일 해당 테마에 하락 종목이 없습니다.</div>"
                else:
                    for _, row in down_stocks.iterrows():
                        s_name = row.get('name', '종목명')
                        s_code = row.get('code', '000000')
                        s_price = int(row.get('price', 0))
                        s_rate = float(row.get('rate', 0.0))
                        down_box_html += f"""
                        <div style='display:flex; justify-content:content; align-items:center; margin-bottom:8px; border-bottom:1px solid #1F2937; padding-bottom:4px;'>
                            <span style='color:#FFF; font-weight:600; font-size:13px;'>{s_name} <small style='color:#9CA3AF;'>{s_code}</small></span>
                            <span style='color:#3B82F6; font-weight:700; font-size:13px; margin-left:auto;'>{s_price:,}원 ({s_rate:.2f}%)</span>
                        </div>
                        """
                down_box_html += "</div>"
                st.markdown(down_box_html, unsafe_allow_html=True)

            # 칸 3. 💥 [우측 날개 미니 라이브 채팅창] 관통 완공!
            with sub_cols[2]:
                st.markdown("<span style='color:#10B981; font-weight:700; font-size:15px;'>💬 실시간 라이브 토크</span>", unsafe_allow_html=True)
                chat_html = """
                <div style='border:1px solid #374151; border-radius:6px; overflow:hidden; background-color:#111827; height:460px;'>
                    <iframe src="https://cbox.ws" 
                            width="100%" 
                            height="460" 
                            allowtransparency="yes" 
                            allow="autoplay" 
                            frameborder="0" 
                            marginwidth="0" 
                            marginheight="0" 
                            scrolling="auto">
                    </iframe>
                </div>
                """
                st.markdown(chat_html, unsafe_allow_html=True)

# -----------------------------------------------------------------
# 🔄 [15초 캐시 가드 오토 리프레시 엔진] (순정 상태 유지)
# -----------------------------------------------------------------
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=15000, key="market_data_refresh")

