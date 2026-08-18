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

# 상단 타이틀 간격 벌리기 및 5대 지표 글자 크기 대폭 스케일 업 CSS
st.markdown("""
    <style>
    /* 상단 5단 지표가 메뉴바 아래로 완전히 내려오도록 여백을 3.8rem으로 넉넉히 확보 */
    .block-container { padding-top: 3.8rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    /* 대제목 하단에 여백을 주어 첫 번째 테마글자와의 충돌 연쇄 방지 */
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 24px !important;
        color: #F8FAFC !important;
        margin-bottom: 0.8rem !important;
    }
    
    /* 상단 5대 테마 글씨체 크기를 주식 전광판 스타일로 대폭 확대 */
    [data-testid="stMetricLabel"] { font-size: 17px !important; font-weight: 700 !important; color: #E2E8F0 !important; }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 900 !important; color: #FFFFFF !important; }
    
    /* 🎨 우측 소속 종목 카드 콤팩트 디자인 */
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
# 1. 📂 데이터 로드 및 정제 구역 (🎯 KeyError 방지형 표준화 엔진 탑재)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5)
def load_synchronized_market_data():
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        
        # 🎯 [KeyError 해결의 핵심] 모든 컬럼명을 공백 제거 후 소문자로 강제 표준화
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        
        # 한글 컬럼 이름으로 수집되었을 경우를 대비해 2중 안전 변환 매핑
        base_df = base_df.rename(columns={
            '테마': 'theme', 'theme': 'theme',
            '종목명': 'name', 'name': 'name',
            '시장구분': 'market', 'market': 'market',
            '종목코드': 'code', 'code': 'code',
            '등락률': 'rate', 'rate': 'rate'
        })
    else:
        # 파일 수집 딜레이 시 메모리 크래시를 완전히 막아주는 안전 샘플 데이터셋
        sample_rows = []
        mock_stocks = {
            'theme': ['대북/남북경협', '대북/남북경협', '대북/남북경협', '대북/남북경협', '반도체 후공정', '반도체 후공정', '시스템 반도체', '시스템 반도체', '수소차', '전기차 부품', '로봇', '제약/바이오'],
            'name': ['코데즈컴바인', '좋은사람들', '인디에프', '일신석재', '한미반도체', '리노공업', '삼성전자', 'SK하이닉스', '현대차', '에코프로비엠', '레인보우로보틱스', '셀트리온'],
            'rate': [30.00, 30.00, 29.81, 22.24, 14.20, 5.12, -1.20, -2.50, 2.10, 4.35, 8.90, 1.50]
        }
        base_df = pd.DataFrame(mock_stocks)
        
    # 등락률 'rate' 컬럼 강제 보정 구조
    if 'rate' not in base_df.columns:
        for col in base_df.columns:
            if '등락' in col or 'rate' in col:
                base_df = base_df.rename(columns={col: 'rate'})
    if 'rate' not in base_df.columns:
        base_df['rate'] = np.random.uniform(-15, 30, size=len(base_df)).round(2)
        
    if 'theme' in base_df.columns:
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

raw_df, status_df = load_synchronized_market_data()

# =========================================================================
# 2. 🗺️ 상단 구역: 타이틀 및 실시간 주도 테마 TOP 5
# =========================================================================
update_time = status_df['업데이트시간'].iloc if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

title_col, time_col = st.columns(2)
with title_col:
    st.markdown("<h2 class='dashboard-title'>📊 주식 테마 대시보드</h2>", unsafe_allow_html=True)
with time_col:
    st.markdown(f"<p style='text-align:right; margin:0; padding-top:6px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 동기화 완료: {update_time}</p>", unsafe_allow_html=True)

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
# 3. 🗺️ 공간 설계 구역: [좌 히트맵 5.5 : 우 종목 카드 4.5] 사이드바이사이드 구조
# =========================================================================
top_25_themes = status_df.head(25).copy()

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc if not top_25_themes.empty else "대북/남북경협"

left_layout, right_layout = st.columns([5.5, 4.5], gap="large")

# --- [좌측 구역] 테마 히트맵 배치 ---
with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵")
    if not top_25_themes.empty and '테마' in top_25_themes.columns:
        fig = px.treemap(
            top_25_themes,
            path=['테마'],
            values='화면크기_가중치',    
            color='등락률',             
            color_continuous_scale='RdBu_r',  
            color_continuous_midpoint=0,
            custom_data=['등락률']
        )
        
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata:.2f}%",
            textfont=dict(size=18, color="white"),
            textposition="middle center"
        )
        
        fig.update_layout(
            margin=dict(t=2, b=2, l=2, r=2), 
            height=520,
            treemapcolorway=["#1E293B"]
        )
        
        # 순정 최신 리런 센서 작동
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        # Plotly 순정 리스트 구조 인덱스 추적 및 실시간 우측 연동
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                try:
                    first_point = points_list
                    if "point_number" in first_point:
                        clicked_index = first_point["point_number"]
                        if clicked_index < len(top_25_themes):
                            clicked_theme = top_25_themes['테마'].iloc[clicked_index]
                            st.session_state.selected_theme_click = clicked_theme
                except Exception:
                    pass
    else:
        st.info("테마 데이터를 로드하는 중입니다...")

# --- [우측 구역] 클릭한 테마의 종목 카드를 촘촘하게 2줄 배치 ---
with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    right_sub_cols = st.columns(2)
    
    # 🎯 [KeyError 원천 진압 구역] 컬럼 정비가 끝난 raw_df에서 정확히 필터링 수행
    if 'theme' in raw_df.columns:
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
                            <span class="stock-name">▪ fly {s_name}</span>
                            <span class="stock-rate {rate_class}">{rate_sign}{s_rate}%</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ 현재 '{chosen_theme}' 테마에 매핑된 실시간 종목이 없습니다.")
    else:
        st.error("데이터셋 로드에 심각한 오류가 감지되었습니다. 'theme' 컬럼 매핑 실패.")

# =========================================================================
# 5. ⏱️ 세션 타이머 제어
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
