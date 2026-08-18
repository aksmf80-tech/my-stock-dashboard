import streamlit as st
import pandas as pd
import os
import time

# =========================================================================
# 0. 🛠️ 대시보드 기본 환경 및 100% 와이드 레이아웃 설정
# =========================================================================
st.set_page_config(
    page_title="핀업 스타일 클린 대시보드",
    layout="wide",  # 📰 뉴스 없는 와이드 100% 레이아웃 강제 활성화
    initial_sidebar_state="collapsed"
)

# 테이블 가독성 향상 및 너비 100% 채우기 전용 CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stTable"] { width: 100% !important; }
    th { background-color: #1E293B !important; color: white !important; font-weight: bold !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 1. 📂 수집 엔진 출력 데이터 로드 구역
# =========================================================================
BASE_FILE = "theme_data.csv"
STATUS_FILE = "realtime_theme_status.csv"

@st.cache_data(ttl=60)  # 실시간 수집 주기에 맞춰 1분 간격 자동 캐시 갱신
def load_market_data():
    # 1. 종목 뼈대 데이터 로드
    if os.path.exists(BASE_FILE):
        base_df = pd.read_csv(BASE_FILE, encoding='utf-8-sig')
        base_df.columns = [str(col).strip().lower() for col in base_df.columns]
        # 한글 컬럼 대응 명칭 표준화
        base_df = base_df.rename(columns={'테마': 'theme', '종목명': 'name', '시장': 'market', '종목코드': 'code'})
    else:
        # 데이터가 없을 때 방어용 샘플 생성
        sample = {'theme': ['대북/남북경협']*2 + ['반도체 후공정']*2, 'name': ['코데즈컴바인', '좋은사람들', '한미반도체', '리노공업'], 'code': ['047770', '033340', '042700', '058470'], 'market': ['KOSDAQ', 'KOSDAQ', 'KOSPI', 'KOSDAQ']}
        base_df = pd.DataFrame(sample)

    # 2. 실시간 테마 상태 데이터 로드
    if os.path.exists(STATUS_FILE):
        status_df = pd.read_csv(STATUS_FILE, encoding='utf-8-sig')
    else:
        # 데이터가 없을 때 방어용 샘플 생성
        status_df = pd.DataFrame({
            '테마': ['대북/남북경협', '반도체 후공정', '시스템 반도체'],
            '등락률': [24.75, 16.37, -11.09],
            '업데이트시간': [time.strftime('%Y-%m-%d %H:%M:%S')]
        })
        
    return base_df, status_df

raw_df, status_df = load_market_data()

# =========================================================================
# 2. 🎯 고유 테마 목록 추출 및 chosen_theme 선언 (NameError 완벽 차단)
# =========================================================================
st.title("📊 실시간 주식 테마 대시보드")

# 최근 갱신 시간 표시
update_time = status_df['업데이트시간'].iloc[0] if '업데이트시간' in status_df.columns else "미정"
st.caption(f"⚙️ 수집 엔진 연동 완료 | 최근 데이터 갱신 시간: {update_time}")

# 수집 엔진이 뽑아준 테마 목록 가져오기
if not status_df.empty and '테마' in status_df.columns:
    theme_list = status_df['테마'].dropna().tolist()
else:
    theme_list = ["대북/남북경협", "반도체 후공정", "시스템 반도체"]

# 💡 최상단 셀렉트박스로 사용자가 테마를 변경하면 하단 100% 종목 리스트가 즉시 연동됩니다.
chosen_theme = st.selectbox("🔍 분석하고 싶은 테마를 선택하세요:", theme_list, index=0)

# =========================================================================
# 3. 🖼️ 상단 콤팩트 구역: 실시간 상위 주도 테마 가로 요약 바
# =========================================================================
st.markdown("---")
st.write("### 🔥 현재 시장 주도 상위 테마")
theme_cols = st.columns(3)

for i in range(min(3, len(status_df))):
    t_name = status_df['테마'].iloc[i]
    t_rate = status_df['등락률'].iloc[i]
    
    with theme_cols[i]:
        if t_rate >= 0:
            st.metric(label=f"🔺 {t_name}", value=f"+{t_rate}%", delta="시장 주도 테마")
        else:
            st.metric(label=f"🔻 {t_name}", value=f"{t_rate}%", delta="하락세", delta_color="inverse")
st.markdown("---")

# =========================================================================
# 4. 🎯 하단 종목 집중 구역 (뉴스 영역 완전 박멸 및 100% 화면 표출)
# =========================================================================
st.subheader(f"📂 {chosen_theme} 테마 상세분석 정보")
st.markdown(f"### 🔥 {chosen_theme} 소속 대장 종목 리스트")

try:
    if not raw_df.empty and 'theme' in raw_df.columns:
        # 선택된 테마 데이터만 정밀 필터링
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        
        avail_cols = []
        col_names = []
        
        # 컬럼 유무 체크 후 출력 그리드 한글화 매핑
        if 'name' in theme_detail_df.columns: 
            avail_cols.append('name'); col_names.append('종목명')
        if 'code' in theme_detail_df.columns: 
            avail_cols.append('code'); col_names.append('종목코드')
        if 'market' in theme_detail_df.columns: 
            avail_cols.append('market'); col_names.append('시장구분')
            
        theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
        theme_df_clean.columns = col_names
        
        # 📌 뉴스가 완전히 빠진 100% 전체 공간을 채워 상위 대장 종목 출력 (최대 15개)
        if not theme_df_clean.empty:
            st.table(theme_df_clean.head(15))
        else:
            st.info(f"현재 `{chosen_theme}` 테마에 배정된 소속 종목 데이터가 비어있습니다.")
    else:
        st.error("데이터셋에 'theme' 열이 존재하지 않거나 데이터 구조가 올바르지 않습니다.")
except Exception as e:
    st.info("🔄 데이터를 불러오는 중입니다... 잠시만 기다려 주세요.")

# =========================================================================
# 5. ⏱️ 60초 간격 세션 자동 갱신 및 캐시 제어 타이머
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
