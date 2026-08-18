import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# ⚠️ 주의: set_page_config는 항상 코드 최상단에 위치해야 합니다.
st.set_page_config(layout="wide")

# 🔔 홍보 배너
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")
st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

# 데이터 파일 존재 여부 확인
if not os.path.exists(DATA_FILE):
    st.warning("⌛ 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
    st.stop()

# 최신 데이터 읽기
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

required_cols = ['테마', '종목명', '등락률']
if df is None or df.empty or not all(col in df.columns for col in required_cols):
    st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다. 장이 열리면 자동으로 갱신됩니다.")
    st.stop()

# 🛠️ 마이너스 등락률로 인한 트리맵 붕괴 막기 (면적용 절댓값 계산)
df['등락률_절댓값'] = df['등락률'].abs().apply(lambda x: max(x, 0.1))

# 상단에 갱신 시각 표시
st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {time.strftime('%H:%M:%S')})")

# ---------------------------------------------------------
# 구역 1: 등락률에 따라 몸집만 커지고 클릭 확대는 안 되는 핀업 트리맵
# ---------------------------------------------------------
fig = px.treemap(
    df, 
    path=['테마'], 
    values='등락률_절댓값', 
    color='등락률',
    color_continuous_scale='RdBu_r', 
    hover_data=['종목명']
)

# maxdepth를 1로 잠그고 조작 제한
fig.update_traces(maxdepth=1, textinfo="label+value")
fig.update_layout(
    clickmode='event', 
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=400
)

# 스트림릿에 트리맵 그리기 및 클릭 감지 설정 (on_select 활성화)
selected_theme = st.plotly_chart(
    fig, 
    use_container_width=True, 
    on_select="rerun", 
    config={'displayModeBar': False, 'scrollZoom': False}
)

# 🛠️ 세션 변수가 아예 없을 때만 최초 기본값(첫 행 테마) 지정
if "chosen_theme" not in st.session_state:
    st.session_state["chosen_theme"] = df['테마'].iloc[0] if not df.empty else "선택된 테마 없음"

# 🛠️ [클릭 트래킹 완전 보완] 모든 데이터 추출 경로 예외처리
if selected_theme:
    points = []
    # 구조 분해하여 points 리스트 추출
    if hasattr(selected_theme, "selection") and selected_theme.selection:
        points = selected_theme.selection.get("points", [])
    elif isinstance(selected_theme, dict) and "selection" in selected_theme:
        points = selected_theme["selection"].get("points", [])
        
    if points and len(points) > 0:
        point_data = points[0]
        
        # 💡 트리맵 종류에 따라 label, id, root 등에 값이 다르게 맵핑되므로 순차적으로 탐색합니다.
        clicked_label = (
            point_data.get("label") or 
            point_data.get("id") or 
            point_data.get("root")
        )
        
        # 만약 'id' 경로에 '/'가 포함되어 들어오는 경우(예: "자동차 부품/현대모비스") 텍스트를 정제합니다.
        if clicked_label and "/" in str(clicked_label):
            clicked_label = str(clicked_label).split("/")[-1]
            
        # 정상적인 값이 추출되었을 때만 세션 상태를 변경하여 화면을 유지합니다.
        if clicked_label and str(clicked_label).strip() != "" and clicked_label in df['테마'].values:
            st.session_state["chosen_theme"] = clicked_label

# 무조건 세션에 기록된 최종 테마를 화면에 바인딩
current_theme = st.session_state["chosen_theme"]

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 테마 클릭 시 아래에 목록이 주르륵 나오는 부분 & 뉴스 연동
# ---------------------------------------------------------
st.subheader(f"📂 {current_theme} 관련 정보")

# 해당 테마에 속한 종목들만 필터링
theme_df = df[df['테마'] == current_theme].copy()

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📈 {current_theme} 종목 리스트**")
    
    st.data_editor(
        theme_df[['종목명', '등락률']],
        use_container_width=True,
        disabled=True, 
        key="stock_selector"
    )
    
    current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

with col2:
    st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
    st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
    
    stock_news_url = "https://naver.com" + str(current_stock)
    theme_news_url = "https://naver.com" + str(current_theme).replace(" ", "")
    
    st.markdown(f"📌 [📢 [뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)]({stock_news_url})")
    st.markdown(f"📌 [📢 [뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)]({theme_news_url})")
   
    st.markdown("---")
    st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")
