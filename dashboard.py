import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import time

# =========================================================================
# 0. 🛠️ 대시보드 기본 환경 및 다크 테마 디자인 설정
# =========================================================================
st.set_page_config(
    page_title="핀업 스타일 테마 맵 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎯 상단 글자 크기 밸런싱 및 가독성 증폭 디자인 CSS 튜닝
st.markdown("""
    <style>
    /* 상단 요소를 완전히 내려서 가독성 확보 */
    .block-container { padding-top: 3.5rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    /* 🎯 상단 5대 테마 글자 크기 및 수치(%) 비율 레이아웃 커스텀 */
    [data-testid="stMetricLabel"] { font-size: 15px !important; font-weight: bold !important; color: #CBD5E1 !important; }
    [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 800 !important; color: #F8FAFC !important; }
    
    /* 🎨 우측 종목 카드 콤팩트 격자 디자인 */
    .stock-card {
        background-color: #1E293B;
        border-left: 5px solid #EF4444;
        padding: 12px 14px;
        margin: 5px 0;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    .stock-name { font-size: 15px; font-weight: bold; color: #F8FAFC; }
    .stock-rate { font-size: 15px; font-weight: bold; }
    .rate-up { color: #F87171; }
    .rate-down { color: #60A5FA; }
    
    /* 히트맵 글자 중앙 정렬 보정 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (컬럼 동기화 정상화)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5)
def load_market_data():
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code', '등락률': 'rate'})
    else:
        sample_rows = []
        mock_stocks = {
            '대북/남북경협': [('코데즈컴바인', 30.00), ('좋은사람들', 30.00), ('인디에프', 29.81), ('일신석재', 22.24)],
            '반도체 후공정': [('한미반도체', 14.20), ('리노공업', 5.12), ('이오테크닉스', 3.45)],
            '시스템 반도체': [('삼성전자', -1.20), ('SK하이닉스', -2.50), ('DB하이텍', 0.85)],
            '수소차': [('현대차', 2.10), ('일진하이솔루스', -0.50)],
            '전기차 부품': [('에코프로비엠', 4.35), ('엘앤에프', -3.10)],
            '로봇': [('레인보우로보틱스', 8.90), ('두산로보틱스', 11.20)],
            '제약/바이오': [('삼성바이오로직스', -0.80), ('셀트리온', 1.50)]
        }
        for theme, stocks in mock_stocks.items():
            for name, rate in stocks:
                sample_rows.append({'theme': theme, 'name': name, 'rate': rate})
        base_df = pd.DataFrame(sample_rows)
        
    if 'rate' not in base_df.columns:
        base_df['rate'] = np.random.uniform(-15, 30, size=len(base_df)).round(2)
    base_df['theme'] = base_df['theme'].astype(str).str.strip()

    if os.path.exists(STATUS_FILE) and os.path.getsize(STATUS_FILE) > 0:
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
        if '테마' in status_df.columns:
            status_df['테마'] = status_df['테마'].astype(str).str.strip()
    else:
        current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        status_df = pd.DataFrame({
            '테마': ['대북/남북경협', '반도체 후공정', '시스템 반도체', '수소차', '전기차 부품', '로봇', '제약/바이오'],
            '등락률': [24.75, 16.37, -11.09, -13.62, -13.36, -14.47, -14.78],
            '화면크기_가중치': [35.0, 28.0, 20.0, 18.0, 15.0, 12.0, 10.0],
            '업데이트시간': [current_time_str] * 7
        })
        
    return base_df, status_df

raw_df, status_df = load_market_data()

# =========================================================================
# 2. 🗺️ 상단 구역: 타이틀 및 실시간 주도 테마 TOP 5 (글자 크기 밸런스 패치)
# =========================================================================
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

title_col, time_col = st.columns([6, 4])
with title_col:
    st.markdown("<h2 style='margin:0; padding:0; font-size:22px; color:#F8FAFC;'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:6px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 동기화 완료: {update_time}</p>", unsafe_allow_html=True)

# 🎯 상단 5대 테마 지표 가로 비율 정렬 완료
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

# =========================================================================
# 3. 🗺️ 획기적 공간 설계: [좌 히트맵 5.5 : 우 종목 카드 4.5] 사이드바이사이드 구조
# =========================================================================
top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc[0] if not top_25_themes.empty else "대북/남북경협"

left_layout, right_layout = st.columns([5.5, 4.5], gap="large")

# --- [좌측 구역] 테마 히트맵 배치 ---
with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty and '테마' in top_25_themes.columns:
        
        # 🎯 [NaN% 완벽 해결 조치] 음수 연산 버그를 우회하기 위해 한글명과 퍼센트 수치를 미리 합친 정적 텍스트 필드 생성
        display_texts = []
        for _, row in top_25_themes.iterrows():
            sign = "+" if row['등락률'] >= 0 else ""
            display_texts.append(f"<b>{row['테마']}</b><br>{sign}{row['등락률']:.2f}%")
        top_25_themes['display_text'] = display_texts
        
        fig = px.treemap(
            top_25_themes,
            path=['display_text'], # 📌 테마명 대신 치환이 완료된 정적 텍스트 경로를 태워 NaN% 원천 차단
            values='화면크기_가중치',    
            color='등락률',             
            color_continuous_scale='RdBu_r',  
            color_continuous_midpoint=0      
        )
        
        fig.update_traces(
            textfont=dict(size=18, color="white"),
            textposition="middle center"
        )
        
        fig.update_layout(
            margin=dict(t=2, b=2, l=2, r=2), 
            height=520,
            treemapcolorway=["#1E293B"]
        )
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        # 클릭 데이터 센서 바인딩 및 파싱 매핑
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                try:
                    first_point = points_list[0]
                    if "id" in first_point:
                        # 정적 텍스트 경로 구조에서 HTML 태그를 분리하여 순수 테마 한글명만 추출해냄
                        raw_id = first_point["id"]
                        parsed_theme = raw_id.split("<b>")[1].split("</b>")[0].strip()
                        st.session_state.selected_theme_click = parsed_theme
                except Exception:
                    pass
    else:
        st.info("테마 데이터를 로드하는 중입니다...")

# --- [우측 구역] 클릭한 테마의 종목 카드를 촘촘하게 2줄 배치 ---
with right_layout:
    chosen_theme = st.session_state.selected_theme_click
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    right_sub_cols = st.columns(2)
    
    try:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
        if not theme_detail_df.empty:
            theme_detail_df = theme_detail_df.sort_values(by='rate', ascending=False).reset_index(drop=True)
            
            for idx, row in theme_detail_df.head(14).iterrows():
                s_name = row['name']
                s_rate = row['rate']
                
                rate_class = "rate-up" if s_rate >= 0 else "rate-down"
                rate_sign = "+" if s_rate >= 0 else ""
                
                with right_sub_cols[idx % 2]:
                    st.markdown(f"""
                        <div class="stock-card">
                            <span class="stock-name">▪️ {s_name}</span>
                            <span class="stock-rate {rate_class}">{rate_sign}{s_rate}%</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ '{chosen_theme}' 테마에 매핑된 실시간 종목이 없습니다.")
    except Exception as e:
        st.info("🔄 실시간 주가 리스트를 우측 레이아웃에 정렬하는 중입니다...")

# =========================================================================
# 5. ⏱️ 세션 타이머 제어
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
