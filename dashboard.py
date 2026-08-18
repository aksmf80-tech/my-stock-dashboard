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
    .block-container { padding-top: 3.8rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 24px !important;
        color: #F8FAFC !important;
        margin-bottom: 0.8rem !important;
    }
    
    [data-testid="stMetricLabel"] { font-size: 19px !important; font-weight: 700 !important; color: #E2E8F0 !important; }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 900 !important; color: #FFFFFF !important; }
    
    /* 🎨 우측 소속 종목 카드 콤팩트 전광판 이펙트 디자인 */
    .pinup-card {
        padding: 12px 16px;
        margin: 5px 0;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3);
    }
    .bg-up { background-color: #DC2626 !important; border-left: 6px solid #FEF08A; }   /* 강렬한 상승 레드 */
    .bg-down { background-color: #2563EB !important; border-left: 6px solid #93C5FD; } /* 시원한 하락 블루 */
    .stock-name { font-size: 16px; font-weight: 800; color: #FFFFFF; }
    .stock-rate { font-size: 16px; font-weight: 900; color: #FFFFFF; }
    
    /* 히트맵 글자 중앙 정렬 보정 */
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (최대 30개 규모 백업 데이터 풀 확장 탑재)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

BACKUP_STOCK_POOL = {
    "대북/남북경협": [
        ("코데즈컴바인", 30.00), ("좋은사람들", 30.00), ("인디에프", 29.81), ("일신석재", 22.24), 
        ("부산산업", 18.50), ("제이에스티나", 15.30), ("신원", 12.10), ("재영솔루텍", 9.80),
        ("아난티", 8.40), ("현대로템", 7.15), ("한일현대시멘트", 5.20), ("쌍용C&E", 4.10),
        ("성신양회", 3.85), ("특수건설", 2.10), ("우원개발", 1.45), ("남광토건", -0.80),
        ("삼부토건", -1.20), ("동아지질", -2.50), ("서암기계공업", -3.10), ("대호에이엘", -4.20)
    ],
    "반도체 후공정": [
        ("한미반도체", 14.20), ("리노공업", 5.12), ("하나마이크론", 4.30), ("이오테크닉스", 3.12),
        ("네패스", 2.85), ("에스에프에이", 2.10), ("엘비세미콘", 1.45), ("두산테스나", 0.90),
        ("시그네틱스", -0.40), ("윈팩", -1.15), ("에이팩트", -2.30), ("티에스이", -3.50)
    ],
    "시스템 반도체": [
        ("삼성전자", -1.20), ("SK하이닉스", -2.50), ("DB하이텍", 0.90), ("네패스아크", 1.45),
        ("가온칩스", 8.30), ("오픈엣지테크놀로지", 7.15), ("에이디테크놀로지", 5.40), ("텔레칩스", 3.10),
        ("칩스앤미디어", 2.20), ("넥스트칩", 1.10), ("코아시아", -0.80), ("알파홀딩스", -2.40)
    ],
    "수소차": [
        ("현대차", 2.10), ("일진하이솔루스", -0.50), ("동아화성", 4.15), ("두산퓨어셀", 8.90),
        ("에스퓨어셀", 6.30), ("상아프론테크", 3.10), ("유니크", 1.85), ("평화산업", -1.40)
    ],
    "전기차 부품": [
        ("에코프로비엠", 4.35), ("엘앤에프", -3.10), ("신흥에스이씨", 1.20), ("상신이디피", 5.40),
        ("삼기", 3.15), ("엠에스오토텍", 2.10), ("우수AMS", -1.10), ("명신산업", -2.85)
    ],
    "로봇": [
        ("레인보우로보틱스", 8.90), ("두산로보틱스", 11.20), ("뉴로메카", 5.40), ("로보티즈", 3.15),
        ("티보로보틱스", 2.80), ("유진로봇", 1.45), ("로보스타", -0.90), ("스맥", -2.35)
    ],
    "제약/바이오": [
        ("삼성바이오로직스", -0.80), ("셀트리온", 1.50), ("알테오젠", 12.30), ("HLB", 9.45),
        ("유한양행", 4.20), ("한미약품", 2.15), ("SK바이오팜", -1.10), ("제일약품", -3.40)
    ]
}

@st.cache_data(ttl=5)
def load_synchronized_market_data():
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={
            '테마': 'theme', 'theme': 'theme',
            '종목명': 'name', 'name': 'name',
            '시장구분': 'market', 'market': 'market',
            '종목코드': 'code', 'code': 'code',
            '등락률': 'rate', 'rate': 'rate'
        })
    else:
        sample_rows = []
        for theme, stocks in BACKUP_STOCK_POOL.items():
            for name, rate in stocks:
                sample_rows.append({'theme': theme, 'name': name, 'rate': rate})
        base_df = pd.DataFrame(sample_rows)
        
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
            custom_data=['등rak률'] if '등rak률' in top_25_themes.columns else ['등락률']
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
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                try:
                    first_point = points_list[0]
                    if "label" in first_point:
                        st.session_state.selected_theme_click = str(first_point["label"]).strip()
                    elif "point_number" in first_point:
                        clicked_index = first_point["point_number"]
                        if clicked_index < len(top_25_themes):
                            st.session_state.selected_theme_click = top_25_themes['테마'].iloc[clicked_index]
                except Exception:
                    pass
    else:
        st.info("테마 데이터를 로드하는 중입니다...")

# --- [우측 구역] 클릭한 테마의 종목 카드를 촘촘하게 2줄 배치 ---
with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    right_sub_cols = st.columns(2)
    
    final_stock_list = []
    theme_detail_df = pd.DataFrame()
    if 'theme' in raw_df.columns:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
    if not theme_detail_df.empty:
        theme_detail_df = theme_detail_df.sort_values(by='rate', ascending=False).reset_index(drop=True)
        for _, row in theme_detail_df.head(30).iterrows():
            final_stock_list.append((row['name'], row['rate']))
    else:
        # 🎯 [들여쓰기 버그 완전 박멸] 스크린샷에 나온 바깥쪽의 불필요한 설명 파편 글씨를 완전 삭제하고
