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
    page_title="핀업 스타일 주식 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 여백을 조절하고 하단 종목 카드를 예쁘게 꾸미는 다크 모드 전용 CSS
st.markdown("""
    <style>
    /* 상단 타이틀 짤림 방지를 위해 padding-top 안전 마진(1.2rem) 확보 */
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    hr { margin: 0.5rem 0 !important; }
    
    /* 🎨 핀업 스타일의 콤팩트한 종목 카드 디자인 (좌우 늘어짐 전면 차단) */
    .stock-card {
        background-color: #1E293B;
        border-left: 5px solid #EF4444;
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        max-width: 400px;
    }
    .stock-name { font-size: 16px; font-weight: bold; color: #F8FAFC; }
    .stock-rate { font-size: 16px; font-weight: bold; }
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
# 1. 📂 데이터 로드 및 정제 구역 (KeyError 버그 완전 제거)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5)
def load_market_data():
    # 1. 종목 및 등락률 데이터 결합 및 가공
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code', '등락률': 'rate'})
    else:
        # 💡 [KeyError 해결] 샘플 데이터의 열 이름을 정확히 'theme' 소문자로 설정
        sample_rows = []
        mock_stocks = {
            '대북/남북경협': [('코데즈컴바인', 30.00), ('좋은사람들', 30.00), ('인디에프', 29.81)],
            '반도체 후공정': [('한미반도체', 14.20), ('리노공업', 5.12)],
            '시스템 반도체': [('삼성전자', -1.20), ('SK하이닉스', -2.50)],
            '수소차': [('현대차', 2.10), ('일진하이솔루스', -0.50)],
            '전기차 부품': [('에코프로비엠', 4.35), ('엘앤에프', -3.10)],
            '로봇': [('레인보우로보틱스', 8.90), ('두산로보틱스', 11.20)],
            '제약/바이오': [('삼성바이오로직스', -0.80), ('셀트리온', 1.50)]
        }
        for theme, stocks in mock_stocks.items():
            for name, rate in stocks:
                sample_rows.append({'theme': theme, 'name': name, 'rate': rate})
        base_df = pd.DataFrame(sample_rows)
        
    # 만약 원본 데이터에 등락률(rate)이 없다면 가상으로 안전 패치
    if 'rate' not in base_df.columns:
        base_df['rate'] = np.random.uniform(-15, 30, size=len(base_df)).round(2)
        
    # 공백 제거 안전 조치 실행
    if 'theme' in base_df.columns:
        base_df['theme'] = base_df['theme'].astype(str).str.strip()

    # 2. 실시간 테마 상태 데이터 로드
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
# 2. 🗺️ 상단 구역: 타이틀 및 실시간 주도 테마 TOP 5
# =========================================================================
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

title_col, time_col = st.columns()
with title_col:
    st.markdown("<h2 style='margin:0; padding:0; font-size:24px; color:#F8FAFC;'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:8px; color:#94A3B8; font-size:13px; font-weight:bold;'>⏱️ 동기화 완료: {update_time}</p>", unsafe_allow_html=True)

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
# 3. 🗺️ 중간 구역: 순정 st.plotly_chart 내부 클릭 연동형 히트맵
# =========================================================================
top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc[0] if not top_25_themes.empty else "대북/남북경협"

if not top_25_themes.empty and '테마' in top_25_themes.columns:
    fig = px.treemap(
        top_25_themes,
        path=['테마'],
        values='화면크기_가중치',    
        color='등락률',             
        color_continuous_scale='RdBu_r',  
        color_continuous_midpoint=0      
    )
    
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{color:.2f}%",
        textfont=dict(size=18, color="white"),
        textposition="middle center"
    )
    
    fig.update_layout(
        margin=dict(t=2, b=2, l=2, r=2), 
        height=380,
        treemapcolorway=["#1E293B"]
    )
    
    side_space1, center_map, side_space2 = st.columns([0.2, 9.6, 0.2])
    with center_map:
        # 🎯 최신 Streamlit 순정 인터랙션 연동 모드 실행
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        # 클릭 이벤트 감지 루프
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list:
                try:
                    clicked_point = points_list[0]
                    # 트리맵 계층 구조 내에서 선택된 포인트 넘버 매핑 보정
                    if "point_number" in clicked_point:
                        clicked_index = clicked_point["point_number"]
                        # 최상위 루트 노드 인덱스 필터 처리 예외 방어
                        if clicked_index < len(top_25_themes):
                            clicked_theme = top_25_themes['테마'].iloc[clicked_index]
                            st.session_state.selected_theme_click = clicked_theme
                except Exception:
                    pass
else:
    st.info("테마 상태 데이터를 로드하는 중입니다...")

# =========================================================================
# 4. 🎯 하단 구역: 콤팩트 카드 표출 구역 (셀렉트박스 삭제 및 레이아웃 밀집)
# =========================================================================
chosen_theme = st.session_state.selected_theme_click

st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 테마 소속 종목", unsafe_allow_html=True)

card_cols = st.columns(3)

try:
    theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
    
    if not theme_detail_df.empty:
        theme_detail_df = theme_detail_df.sort_values(by='rate', ascending=False).reset_index(drop=True)
        
        for idx, row in theme_detail_df.head(12).iterrows():
            s_name = row['name']
            s_rate = row['rate']
            
            rate_class = "rate-up" if s_rate >= 0 else "rate-down"
            rate_sign = "+" if s_rate >= 0 else ""
            
            with card_cols[idx % 3]:
                st.markdown(f"""
                    <div class="stock-card">
                        <span class="stock-name">▪️ {s_name}</span>
                        <span class="stock-rate {rate_class}">{rate_sign}{s_rate}%</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ 현재 '{chosen_theme}' 테마에 매핑된 종목 데이터셋이 존재하지 않습니다.")
except Exception as e:
    st.info("🔄 실시간 주가 리스트를 로드하는 중입니다...")

# =========================================================================
# 5. ⏱️ 세션 타이머 제어
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
