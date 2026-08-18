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
    page_title="구글 파이낸스 스타일 테마 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 상단 타이틀 간격 및 5대 지표 글자 크기 대폭 스케일 업 CSS
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
    
    g.treemaptext text {
        text-anchor: middle !important;
        dominant-baseline: central !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역 (🎯 구글 파이낸스 매핑 대치 풀)
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

# 구글 파이낸스 수집 엔진 스펙과 대칭을 이루는 국내 핵심 14대 대장주 뼈대 풀
BACKUP_STOCK_POOL = {
    "대북/남북경협": [
        ("코데즈컴바인", 30.00), ("좋은사람들", 30.00), ("인디에프", 29.81), ("일신석재", 22.24),
        ("부산산업", 18.50), ("제이에스티나", 15.30), ("신원", 12.10), ("재영솔루텍", 9.80),
        ("아난티", 8.40), ("현대로템", 7.15), ("한일현대시멘트", 5.20), ("쌍용C&E", 4.10),
        ("성신양회", 3.85), ("특수건설", 2.10)
    ],
    "반도체 후공정": [
        ("한미반도체", 14.20), ("리노공업", 5.12), ("하나마이크론", 4.30), ("이오테크닉스", 3.12),
        ("네패스", 2.85), ("에스에프에이", 2.10), ("엘비세미콘", 1.45), ("두산테스나", 0.90),
        ("시그네틱스", -0.40), ("윈팩", -1.15), ("에이팩트", -2.30), ("티에스이", -3.50),
        ("고영", 3.20), ("피에스케이", 1.15)
    ],
    "시스템 반도체": [
        ("삼성전자", -1.20), ("SK하이닉스", -2.50), ("DB하이텍", 0.90), ("네패스아크", 1.45),
        ("가온칩스", 8.30), ("오픈엣지테크놀로지", 7.15), ("에이디테크놀로지", 5.40), ("텔레칩스", 3.10),
        ("칩스앤미디어", 2.20), ("넥스트칩", 1.10), ("코아시아", -0.80), ("알파홀딩스", -2.40),
        ("SFA반도체", 4.20), ("어보브반도체", 1.85)
    ],
    "수소차": [
        ("현대차", 2.10), ("일진하이솔루스", -0.50), ("동아화성", 4.15), ("대우부품", 1.30),
        ("두산퓨어셀", 8.90), ("에스퓨어셀", 6.30), ("상아프론테크", 3.10), ("유니크", 1.85),
        ("평화산업", -1.40), ("평화홀딩스", 2.20), ("엔케이", 0.95), ("지엠비코리아", -0.80),
        ("일진다이아", 2.45), ("코오롱플라스틱", -1.15)
    ],
    "전기차 부품": [
        ("에코프로비엠", 4.35), ("엘앤에프", -3.10), ("신흥에스이씨", 1.20), ("상신이디피", 5.40),
        ("삼기", 3.15), ("엠에스오토텍", 2.10), ("우수AMS", -1.10), ("명신산업", -2.85),
        ("아진산업", 3.40), ("구영테크", 0.95), ("대유에이텍", -1.20), ("영화테크", 2.15),
        ("계양전기", 1.40), ("화신", -0.55)
    ],
    "로봇": [
        ("레인보우로보틱스", 8.90), ("두산로보틱스", 11.20), ("뉴로메카", 5.40), ("로보티즈", 3.15),
        ("티보로보틱스", 2.80), ("유진로봇", 1.45), ("로보스타", -0.90), ("스맥", -2.35),
        ("휴림로봇", 4.10), ("에브리봇", -1.50), ("로보로보", 0.85), ("디엔에이치", 2.30),
        ("푸른기술", 1.70), ("싸이맥스", -0.45)
    ],
    "제약/바이오": [
        ("삼성바이오로직스", -0.80), ("셀트리온", 1.50), ("알테오젠", 12.30), ("HLB", 9.45),
        ("유한양행", 4.20), ("한미약품", 2.15), ("SK바이오팜", -1.10), ("제일약품", -3.40),
        ("대웅제약", 1.85), ("종근당", 0.95), ("녹십자", -1.40), ("동국제약", 2.10),
        ("한올바이오", 5.30), ("신풍제약", -2.15)
    ]
}

@st.cache_data(ttl=5)
def load_market_data():
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        # 구글 파이낸스 수집 필드명에 완벽 동기화 매핑
        base_df = base_df.rename(columns={
            '테마': 'theme', 'theme': 'theme',
            '종목명': 'name', 'name': 'name',
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

raw_df, status_df = load_market_data()

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
        
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                try:
                    first_point = points_list
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

# --- [우측 구역] 클릭한 테마의 종목 버튼형 카드 나열 (최대 14개 완결) ---
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
        for _, row in theme_detail_df.head(14).iterrows():
            final_stock_list.append((row['name'], row['rate']))
    else:
        final_stock_list = BACKUP_STOCK_POOL.get(chosen_theme, [("샘플대장주A", 4.25), ("샘플대장주B", -1.80)])
        
    # 들여쓰기 공백을 완벽 정렬하여 버튼 컴포넌트 14개 안정적 출력
    for idx, (s_name, s_rate) in enumerate(final_stock_list[:14]):
        rate_sign = "+" if s_rate >= 0 else ""
        with right_sub_cols[idx % 2]:
            st.button(f"▪️ {s_name} ({rate_sign}{s_rate}%)", key=f"stock_btn_google_14_{idx}_{s_name}", use_container_width=True)

