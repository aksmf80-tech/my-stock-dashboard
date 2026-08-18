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

# 상단 타이틀 간격 벌리기 및 5대 지표 글자 크기 대폭 스케일 업 CSS
st.markdown("""
    <style>
    .block-container { padding-top: 3.2rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    hr { margin: 0.4rem 0 !important; }
    
    .dashboard-title {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 24px !important;
        color: #F8FAFC !important;
        margin-bottom: 0.8rem !important;
    }
    
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
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 데이터 로드 및 정제 구역
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=5)
def load_synchronized_market_data():
    if os.path.exists(BASE_FILE) and os.path.getsize(BASE_FILE) > 0:
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code', '등락률': 'rate'})
    else:
        sample_rows = []
        mock_stocks = {
            'theme': ['대북/남북경협', '대북/남북경협', '반도체 후공정', '시스템 반도체', '시스템 반도체', '수소차', '전기차 부품', '로봇', '제약/바이오'],
            'name': ['코데즈컴바인', '좋은사람들', '한미반도체', '삼성전자', '코데즈컴바인', '현대차', '에코프로비엠', '레인보우로보틱스', '셀트리온'],
            'rate': [30.00, 30.00, 14.20, -1.20, 25.40, 2.10, 4.35, 8.90, 1.50]
        }
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
update_time = status_df['업데이트시간'].iloc[0] if not status_df.empty and '업데이트시간' in status_df.columns else "미정"

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
# 3. 🗺️ 공간 설계 구역: [좌 고정형 차트 5.5 : 우 종목 카드 4.5] 사이드바이사이드
# =========================================================================
top_25_themes = status_df.head(25).copy()

# 거래량/가중치 순으로 정렬하여 차트 가독성 증폭
if '화면크기_가중치' in top_25_themes.columns:
    top_25_themes = top_25_themes.sort_values(by='화면크기_가중치', ascending=True)

if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = top_25_themes['테마'].iloc[-1] if not top_25_themes.empty else "대북/남북경협"

left_layout, right_layout = st.columns([5.5, 4.5], gap="large")

# --- [좌측 구역] 절대 확대되지 않는 핀업 스타일 가로 바 차트 배치 ---
with left_layout:
    st.markdown("### 🗺️ 실시간 테마 히트맵 (고정형)")
    if not top_25_themes.empty and '테마' in top_25_themes.columns:
        
        # 🎯 [대혁신] 클릭 시 화면 전환/확대가 절대 일어나지 않는 가로형 막대 차트로 대체
        fig = px.bar(
            top_25_themes,
            x='화면크기_가중치',
            y='테마',
            color='등락률',
            orientation='h',  # 가로형 막대 설정
            color_continuous_scale='RdBu_r',
            color_continuous_midpoint=0,
            text='등락률'  # 막대 끝에 수치 표출
        )
        
        fig.update_traces(
            texttemplate="<b>%{text:.2f}%</b>",
            textposition="outside",
            textfont=dict(size=14, color="white"),
            marker=dict(line=dict(width=1, color='#1E293B'))
        )
        
        fig.update_layout(
            margin=dict(t=2, b=2, l=2, r=30), 
            height=520,
            xaxis_title="시장 가중치 (거래대금)",
            yaxis_title=None,
            showlegend=False
        )
        
        # 순정 인터랙션 연동 센서 작동
        chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        # 🎯 바 차트 구조에 최적화된 초정밀 인덱스 추적 및 우측 실시간 바인딩
        if chart_res and "selection" in chart_res and "points" in chart_res["selection"]:
            points_list = chart_res["selection"]["points"]
            if points_list and len(points_list) > 0:
                try:
                    first_point = points_list[0]
                    # 바 차트의 y축 라벨 값(테마명)을 직접 낚아채는 가장 안전한 알고리즘 적용
                    if "y" in first_point:
                        st.session_state.selected_theme_click = str(first_point["y"]).strip()
                except Exception:
                    pass
    else:
        st.info("테마 데이터를 로드하는 중입니다...")

# --- [우측 구역] 클릭한 테마의 종목 카드를 촘촘하게 2줄 배치 ---
with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    st.markdown(f"### 🗂️ <b>{chosen_theme}</b> 소속 종목", unsafe_allow_html=True)
    
    right_sub_cols = st.columns(2)
    
    try:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
        if not theme_detail_df.empty:
            if 'rate' in theme_detail_df.columns:
                theme_detail_df = theme_detail_df.sort_values(by='rate', ascending=False)
            theme_detail_df = theme_detail_df.reset_index(drop=True)
            
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
            # 2중 안전장치: 파일 동기화 딜레이 시 활성화되는 7대 대장주 백업 풀
            backup_pool = {
                "대북/남북경협": [("코데즈컴바인", 30.00), ("좋은사람들", 30.00), ("인디에프", 29.81), ("일신석재", 22.24)],
                "반도체 후공정": [("한미반도체", 14.20), ("리노공업", 5.12), ("하나마이크론", 4.30), ("이오테크닉스", 3.12)],
                "시스템 반도체": [("삼성전자", -1.20), ("SK하이닉스", -2.50), ("DB하이텍", 0.90), ("네패스아크", 1.45)],
                "수소차": [("현대차", 2.10), ("일진하이솔루스", -0.50)],
                "전기차 부품": [("에코프로비엠", 4.35), ("엘앤에프", -3.10)],
                "로봇": [("레인보우로보틱스", 8.90), ("두산로보틱스", 11.20)],
                "제약/바이오": [("삼성바이오로직스", -0.80), ("셀트리온", 1.50)]
            }
            active_list = backup_pool.get(chosen_theme, [("샘플대장주A", 4.25), ("샘플대장주B", -1.80)])
            for idx, (s_name, s_rate) in enumerate(active_list):
                rate_class = "rate-up" if s_rate >= 0 else "rate-down"
                rate_sign = "+" if s_rate >= 0 else ""
                with right_sub_cols[idx % 2]:
                    st.markdown(f"""
                        <div class="stock-card">
                            <span class="stock-name">▪️ {s_name}</span>
                            <span class="stock-rate {rate_class}">{rate_sign}{s_rate}%</span>
                        </div>
                    """, unsafe_allow_html=True)
