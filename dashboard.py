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
        # 💡 [형님 폴더 기법 정밀 싱크]: 3,000방에 주식 코드별로 1대1 분산 저장된 1,500마리 고기 원본들을 
        # 화면 출력 바로 전단계에서 가상 테마 폴더명('theme') 기준으로 자석처럼 한 그릇에 대합체 병합 연산 처리합니다!
        filtered_df = base_df[~base_df['theme'].isin(['대형주마스터', '미분류', '빈방_대기', '준비중_테마', 'SKELETON_BASE', ''])]
        if not filtered_df.empty:
            agg_df = filtered_df.groupby('theme')['rate'].mean().reset_index()
            
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
    else:
        status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        
    return base_df, status_df

raw_df, status_df = load_market_data()

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
# 5. [HTS 규격 대왕 글씨] 삼성전자 & SK하이닉스 상시 배치 (100% 순정 투과형)
# =================================================================
master_2_cols = st.columns(2)
m_targets = [("삼성전자", "005930"), ("SK하이닉스", "000660")]

for idx, (m_name, m_code) in enumerate(m_targets):
    m_price = 0  
    m_rate = 0.0
    is_data_loaded = False

    try:
        if not raw_df.empty:
            # 💡 [뻗음 원천 차단]: filtered_df가 아닌 원본 raw_df에서 가져오므로 테마 분류와 상관없이 무조건 뚫고 나옵니다.
            target_rows = raw_df[raw_df['code'] == m_code]
            if not target_rows.empty:
                latest_row = target_rows.iloc[-1] # .iloc 뒤에 대괄호 인덱싱을 적용하여 문법 에러 차단
                
                p_live = int(latest_row['price'])
                r_live = float(latest_row['rate'])
                
                if p_live > 0:
                    m_price = p_live
                    m_rate = r_live
                    is_data_loaded = True
    except:
        pass

    with master_2_cols[idx]:
        if is_data_loaded:
            price_display = f"{m_price:,}원"
            if m_rate >= 0:
                st.markdown(f"""
                    <div class='master-box-custom-up'>
                        <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                        <span style='color:#EF4444; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} (+{m_rate:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='master-box-custom-down'>
                        <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                        <span style='color:#3B82F6; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} ({m_rate:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='master-box-custom-up' style='border-left:8px solid #64748B !important;'>
                    <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                    <span style='color:#94A3B8; font-weight:900; font-size:24px; margin-left:auto;'>대기중 (0원)</span>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =================================================================
# 6. 하단 레이아웃 (당일 1등 테마 자동 선점형 호가 슬라이스)
# =================================================================

# 세션 상태 선제 초기화
if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = ""

# 💡 [공백 방어막]: 마우스로 클릭하기 전이라도, 당일 전광판 1등 테마를 세션에 강제 주입해 리더보드를 먼저 깨웁니다.
if not st.session_state.selected_theme_click and not status_df.empty:
    st.session_state.selected_theme_click = str(status_df['테마'].iloc[0]).strip()

left_layout, right_layout = st.columns([4.4, 5.6], gap="large")

with left_layout:
    st.markdown("### 🗺️ 실시간 주도 테마 히트맵 (좌상단 상승 저격형)")

    if not status_df.empty:
        try:
            fig = px.treemap(
                status_df, 
                path=['테마'], 
                values='화면크기_가중치', 
                color='등락률',             
                color_continuous_scale='RdBu_r', 
                color_continuous_midpoint=0,
                custom_data=['테마']
            )
            
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{color:.2f}%", 
                textfont=dict(size=15, color="white"), 
                textposition="middle center"
            )
            
            fig.update_layout(
                margin=dict(t=5, b=5, l=5, r=5), 
                height=620,
                coloraxis_showscale=True,
                template="plotly_dark"
            )
            
            chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # 🚨 [신형 클릭 파싱 저격]: points 목록의 0번 딕셔너리를 대괄호으로 정확히 파싱해 먹통을 차단합니다.
            if chart_res and isinstance(chart_res, dict) and "selection" in chart_res:
                selection_data = chart_res["selection"]
                if "points" in selection_data and len(selection_data["points"]) > 0:
                    first_point = selection_data["points"][0] # 대괄호 번호 기입 완료
                    
                    if isinstance(first_point, dict):
                        chosen_lbl = first_point.get("label", first_point.get("customdata", [""]))
                        if isinstance(chosen_lbl, list) and len(chosen_lbl) > 0:
                            chosen_lbl = chosen_lbl[0]
                        
                        if chosen_lbl:
                            st.session_state.selected_theme_click = str(chosen_lbl).strip()
        except Exception as chart_err:
            st.error(f"📊 히트맵 연동 중 일시적 지연이 발생했습니다. (원인: {chart_err})")
    else:
        st.info("📊 수파베이스 양식장 통덤프 패킷을 수신 대기 중입니다. 터미널에서 주입 사격을 실행해 주세요!")

with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    
    if not status_df.empty and chosen_theme:
        st.markdown(f"### 🗂️ <span style='font-size:24px;'><b>[{chosen_theme}]</b> 소속 종목 리더보드</span>", unsafe_allow_html=True)
        
        final_stock_list = []
        if not raw_df.empty:
            # 보이지 않는 뒤쪽 공백 오차까지 트림 처리하여 병합 연산 구동
            raw_df['theme_clean'] = raw_df['theme'].astype(str).str.strip()
            theme_detail_df = raw_df[raw_df['theme_clean'] == chosen_theme].copy()
            
            for _, row in theme_detail_df.iterrows():
                s_price = int(row.get('price', 0)) if pd.notna(row.get('price')) else 0
                s_name = str(row.get('name', '알수없음')).strip()
                s_rate = float(row.get('rate', 0.0)) if pd.notna(row.get('rate')) else 0.0
                s_code = str(row.get('code', '005930')).strip()
                final_stock_list.append((s_name, s_rate, s_price, s_code))
                
        # 🔺 등락률(인덱스 1번) 기준 내림차순 정렬 / 🔹 등락률 기준 오름차순 정렬 교정 완료
        up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
        down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
        
        up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True) # 1번 인덱스로 정렬축 고정
        down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
        
        # 상승 종목 리스트 표출
        st.markdown("#### 🔺 상승 종목", unsafe_allow_html=True)
        with st.container(height=260, border=False):
            if up_stocks:
                up_cols = st.columns(2)
                for u_idx, (s_name, s_rate, s_price, s_code) in enumerate(up_stocks[:50]):
                    with up_cols[u_idx % 2]:
                        st.markdown(
                            f"<div class='stock-box-up'>"
                            f"  <span class='stock-name-up'>🔺 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-up'>{s_price:,}원 (+{s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
            else:
                st.text("상승 종목이 없습니다.")

        st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
        
        # 하락 종목 리스트 표출
        st.markdown("#### 🔹 하락 종목", unsafe_allow_html=True)
        with st.container(height=260, border=False):
            if down_stocks:
                down_cols = st.columns(2)
                for d_idx, (s_name, s_rate, s_price, s_code) in enumerate(down_stocks[:50]):
                    with down_cols[d_idx % 2]:
                        st.markdown(
                            f"<div class='stock-box-down'>"
                            f"  <span class='stock-name-down'>🔹 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-down'>{s_price:,}원 ({s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
            else:
                st.text("하락 종목이 없습니다.")
    else:
        st.markdown("### 🗂️ 소속 종목 리더보드")
        st.info("🔄 데이터 수신 즉시 실시간 호가 슬라이스 정렬창이 표출됩니다.")

# =================================================================
# 7. 오토 리프레시 엔진 구동 (15초 단위)
# =================================================================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass
