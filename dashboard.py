import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =================================================================
# 1. [인프라 공사] 스트림릿 기본 주방 환경 설정 및 철옹성 방어막
# =================================================================
st.set_page_config(
    page_title="iWin 주도주 실시간 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# HTS 규격 붉은색/푸른색 및 가두리 3분할 전용 다크 테마 커스텀 스킨 주입
st.markdown(
    """
    <style>
    /* 전체 다크룸 배경 기지 고정 */
    .stApp {
        background-color: #0F172A;
    }
    /* 🚨 [형님 특명 반영]: 최상단 패딩 여백을 제로(0)에 가깝게 압축하여 배너를 머리 끝까지 올립니다 */
    div.block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
    }
    /* 상단 3분할 광고 배너용 정품 CSS 가두리 */
    .master-banner-box {
        padding: 15px; 
        border-radius: 8px; 
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1); 
        height: 100px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center;
    }
    /* 가독성 극대화를 위한 스크롤바 디자인 세척 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #111827;
    }
    ::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =================================================================
# 2. [비밀 금고 열기] 형님 순정 가두리 방 번호 [supabase] 정밀 추적 완공
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =================================================================
# 3. [데이터 파이프라인] 15초 캐시 가드 수송관
# =================================================================
@st.cache_data(ttl=15)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").order("updated_at", desc=True).limit(100).execute()
        data = response.data
        
        if not data:
            return pd.DataFrame()
            
        rows = []
        for item in data:
            t_name = str(item.get('theme_name', '미분류')).strip()
            s_code = str(item.get('stock_code', '')).strip()
            s_name = str(item.get('stock_name', '')).strip()
            
            p_val = item.get('current_price')
            try: price = int(p_val) if p_val is not None else 0
            except: price = 0
                
            r_val = item.get('theme_flu_rt')
            try: rate = float(r_val) if r_val is not None else 0.0
            except: rate = 0.0
                
            rows.append({
                'theme': t_name, 'code': s_code, 'name': s_name, 'price': price, 'rate': rate
            })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# 💥 메인 수송관 데이터프레임 쟁반 수신
raw_df = load_market_data()
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =================================================================
# 1. [인프라 공사] 스트림릿 기본 주방 환경 설정 및 철옹성 방어막
# =================================================================
st.set_page_config(
    page_title="iWin 주도주 실시간 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# HTS 규격 붉은색/푸른색 및 가두리 3분할 전용 다크 테마 커스텀 스킨 주입
st.markdown(
    """
    <style>
    /* 전체 다크룸 배경 기지 고정 */
    .stApp {
        background-color: #0F172A;
    }
    /* 🚨 [형님 특명 반영]: 최상단 패딩 여백을 제로(0)에 가깝게 압축하여 배너를 머리 끝까지 올립니다 */
    div.block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
    }
    /* 상단 3분할 광고 배너용 정품 CSS 가두리 */
    .master-banner-box {
        padding: 15px; 
        border-radius: 8px; 
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1); 
        height: 100px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center;
    }
    /* 가독성 극대화를 위한 스크롤바 디자인 세척 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #111827;
    }
    ::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =================================================================
# 2. [비밀 금고 열기] 형님 순정 가두리 방 번호 [supabase] 정밀 추적 완공
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =================================================================
# 3. [데이터 파이프라인] 15초 캐시 가드 수송관
# =================================================================
@st.cache_data(ttl=15)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").order("updated_at", desc=True).limit(100).execute()
        data = response.data
        
        if not data:
            return pd.DataFrame()
            
        rows = []
        for item in data:
            t_name = str(item.get('theme_name', '미분류')).strip()
            s_code = str(item.get('stock_code', '')).strip()
            s_name = str(item.get('stock_name', '')).strip()
            
            p_val = item.get('current_price')
            try: price = int(p_val) if p_val is not None else 0
            except: price = 0
                
            r_val = item.get('theme_flu_rt')
            try: rate = float(r_val) if r_val is not None else 0.0
            except: rate = 0.0
                
            rows.append({
                'theme': t_name, 'code': s_code, 'name': s_name, 'price': price, 'rate': rate
            })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

# 💥 메인 수송관 데이터프레임 쟁반 수신
raw_df = load_market_data()
# =================================================================
# 5. [하단 3분할 대수술] 🚨 히트맵 1광고 폭 맞춤 축소 및 우측 익명 채팅창 완공
# =================================================================
if 'selected_theme_click' not in st.session_state:
    st.session_state.selected_theme_click = None

# 🚨 [형님 특명]: 좌측 히트맵 가로 폭을 상단 1번 광고 배너 사이즈 규격만큼 콤팩트하게 축소!
# 기존 [4.4 : 5.6] 비율에서 1번 배너 직통 라인인 [3.6 : 6.4] 황금 대칭 수로로 뼈대를 개조했습니다. [1.8]
bottom_cols = st.columns([3.6, 6.4], gap="medium")

# -----------------------------------------------------------------
# 🗺️ [좌측 칸]: 실시간 주도 테마 히트맵 (🚨 1번 배너 가로 매칭 축소 완료)
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
        
        # Plotly 트리맵 엔진 구동 [1.8]
        import plotly.express as px
        fig = px.treemap(
            theme_df,
            path=['theme_clean'],
            values='stock_count',
            color='avg_rate',
            color_continuous_scale=[[0, '#3B82F6'], [0.5, '#111827'], [1, '#EF4444']],
            color_continuous_midpoint=0.0
        )
        
        # 🚨 [주말 ValueError 완벽 소독]: 데이터가 비어있어도 엔진이 터지지 않도록 포맷 고정
        fig.update_traces(
            texttemplate="<b>{label}</b>",
            textposition="inside",
            insidetextfont=dict(size=14, color='white'),
            hovertemplate="<b>{label}</b>"
        )
        
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        from streamlit_plotly_events import plotly_events
        selected_point = plotly_events(fig, click_event=True, hover_event=False, override_height=500)
        
        if selected_point:
            try:
                clicked_idx = selected_point['point_number']
                chosen_theme = theme_df.iloc[clicked_idx]['theme_clean']
                st.session_state.selected_theme_click = chosen_theme
            except:
                pass

# -----------------------------------------------------------------
# 🗂️ [우측 칸]: 테마 포지션 정중앙 전진 밀기 + 💥 우측 날개 미니 채팅창 완공
# -----------------------------------------------------------------
with bottom_cols[1]:
    if st.session_state.selected_theme_click:
        chosen_theme = st.session_state.selected_theme_click
    else:
        chosen_theme = theme_df.iloc[0]['theme_clean'] if 'theme_df' in locals() and not theme_df.empty else "IT 서비스"
        
    st.markdown(f"### 🗂️ [{chosen_theme}] 테마 포지션 및 라이브 토크")
    
    if raw_df is not None and not raw_df.empty:
        theme_detail_df = raw_df[raw_df['theme'].str.replace('ROOM_', '') == chosen_theme].copy()
        
        if not theme_detail_df.empty:
            up_stocks = theme_detail_df[theme_detail_df['rate'] >= 0].sort_values(by='rate', ascending=False)
            down_stocks = theme_detail_df[theme_detail_df['rate'] < 0].sort_values(by='rate', ascending=True)
            
            # 히트맵이 축소된 만큼 상승·하락 종목과 우측 채팅방의 가로 상자가 웅장하고 칼정렬로 확장 정렬됩니다! [1.8]
            sub_cols = st.columns([4.2, 4.2, 3.6], gap="small")
            
            # [칸 0번]: 소속 상승 종목 정중앙 배치 [1.8]
            with sub_cols[0]:
                st.markdown("<span style='color:#EF4444; font-weight:700; font-size:14px;'>🔺 소속 상승 종목</span>", unsafe_allow_html=True)
                up_box_html = "<div style='height:440px; overflow-y:auto; border:1px solid #374151; padding:8px; border-radius:6px; background-color:#111827;'>"
                for _, row in up_stocks.iterrows():
                    s_name = row.get('name', '종목명')
                    s_code = row.get('code', '000000')
                    s_price = int(row.get('price', 0))
                    s_rate = float(row.get('rate', 0.0))
                    up_box_html += f"""
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #1F2937; padding-bottom:4px;'>
                        <span style='color:#FFF; font-weight:600; font-size:12px;'>{s_name} <small style='color:#9CA3AF;'>{s_code}</small></span>
                        <span style='color:#EF4444; font-weight:700; font-size:12px; margin-left:auto;'>{s_price:,}원 (+{s_rate:.2f}%)</span>
                    </div>
                    """
                up_box_html += "</div>"
                st.markdown(up_box_html, unsafe_allow_html=True)
                
            # [칸 1번]: 소속 하락 종목 정중앙 배치 [1.8]
            with sub_cols[1]:
                st.markdown("<span style='color:#3B82F6; font-weight:700; font-size:14px;'>🔹 소속 하락 종목</span>", unsafe_allow_html=True)
                down_box_html = "<div style='height:440px; overflow-y:auto; border:1px solid #374151; padding:8px; border-radius:6px; background-color:#111827;'>"
                if down_stocks.empty:
                    down_box_html += "<div style='color:#9CA3AF; text-align:center; margin-top:20px; font-size:12px;'>당일 해당 테마에 하락 종목이 없습니다.</div>"
                else:
                    for _, row in down_stocks.iterrows():
                        s_name = row.get('name', '종목명')
                        s_code = row.get('code', '000000')
                        s_price = int(row.get('price', 0))
                        s_rate = float(row.get('rate', 0.0))
                        down_box_html += f"""
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #1F2937; padding-bottom:4px;'>
                            <span style='color:#FFF; font-weight:600; font-size:12px;'>{s_name} <small style='color:#9CA3AF;'>{s_code}</small></span>
                            <span style='color:#3B82F6; font-weight:700; font-size:12px; margin-left:auto;'>{s_price:,}원 ({s_rate:.2f}%)</span>
                        </div>
                        """
                down_box_html += "</div>"
                st.markdown(down_box_html, unsafe_allow_html=True)

            # [칸 2번]: 하락 종목 바로 우측 날개 옆방 무료 미니 채팅창 개통! [1.8]
            with sub_cols[2]:
                st.markdown("<span style='color:#10B981; font-weight:700; font-size:14px;'>💬 실시간 라이브 토크</span>", unsafe_allow_html=True)
                chat_html = """
                <div style='border:1px solid #374151; border-radius:6px; overflow:hidden; background-color:#111827; height:440px;'>
                    <iframe src="https://cbox.ws" 
                            width="100%" 
                            height="440" 
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

# =================================================================
# 6. [오토 리프레시 엔진] 15초 단위 마켓 자동 동기화 수송 (순정 복구)
# =================================================================
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=15000, key="market_data_refresh")
