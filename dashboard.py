import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# 1. 화면 레이아웃 넓게 설정
st.set_page_config(layout="wide")
st.title("📊 실시간 주식 테마별 현황판")

DATA_FILE = "theme_data.csv"

# 🟢 [핵심] 60초마다 이 안의 모든 요소(트리맵, 목록, 뉴스)를 깜빡임 없이 새로고침
@st.fragment(run_every=60)
def render_interactive_dashboard():
    if not os.path.exists(DATA_FILE):
        st.warning("⏳ 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
        return

    # 최신 데이터 읽기
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    
    # 상단에 갱신 시각 표시 (F5 없이 1분마다 스스로 바뀜)
    st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {time.strftime('%H:%M:%S')})")

    # ---------------------------------------------------------
    # 구역 1: 등락률에 따라 크기가 스스로 바뀌는 트리맵 (Treemap)
    # ---------------------------------------------------------
    fig = px.treemap(
        df, 
        path=['테마'], 
        values='등락률_절대값', # 상승/하락 폭이 클수록 칸이 스스로 커짐
        color='등락률',
        color_continuous_scale='RdBu_r', # 상승은 빨강, 하락은 파랑
        hover_data=['종목명', '주가']
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=400)
    
    # 스트림릿에 트리맵 그리기 및 클릭 감지 설정
    selected_theme = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # 기본 선택 테마 지정 (선택 안 했을 때는 첫 번째 테마)
    current_theme = df['테마'].iloc[0]
    if selected_theme and "points" in selected_theme and len(selected_theme["points"]) > 0:
        current_theme = selected_theme["points"][0].get("label", current_theme)

    st.markdown("---")

    # ---------------------------------------------------------
    # 구역 2: 테마 클릭 시 아래에 목록이 주르륵 나오는 부분 & 뉴스 연동
    # ---------------------------------------------------------
    st.subheader(f"📂 {current_theme} 관련 정보")
    
    # 해당 테마에 속한 종목들만 필터링
    theme_df = df[df['테마'] == current_theme].copy()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"**📈 {current_theme} 종목 리스트**")
        # 데이터프레임에서 종목을 선택할 수 있도록 데이터 편집기(Data Editor) 활용
        # ⚠️ 보드 안에 종목을 마우스로 클릭하면 라디오 버튼처럼 감지합니다.
        selected_rows = st.dataframe(
            theme_df[['종목명', '주가', '등락률']], 
            use_container_width=True,
            on_select="rerun",
            selection_mode="single"
        )
        
        # 기본 선택 종목 지정 (선택 안 했을 때는 해당 테마의 첫 번째 종목)
        current_stock = theme_df['종목명'].iloc[0]
        if selected_rows and "rows" in selected_rows["selection"] and len(selected_rows["selection"]["rows"]) > 0:
            idx = selected_rows["selection"]["rows"][0]
            current_stock = theme_df['종목명'].iloc[idx]

    with col2:
        st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
        # 💡 [뉴스 연동] 선택된 테마와 종목에 맞는 뉴스 목록을 가상으로 매칭하여 보여줍니다.
        # 실제 환경에서는 fetch_data.py가 수집한 뉴스 데이터를 매칭하게 됩니다.
        st.info(f"🔍 '{current_stock}' 주가 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스 속보 리스트가 여기에 바인딩됩니다.")
        
        # 스크린샷과 유사한 뉴스 형태 출력 예시
        st.caption(f"📌 [뉴스] {current_stock} 관련주, '봄바람 살랑살랑' 거래량 급증하며 강세 (1일 전)")
        st.caption(f"📌 [뉴스] {current_theme} 시장 경쟁 심화... {current_stock} 글로벌 공급망 확대 나선다 (2일 전)")
        st.caption(f"📌 [뉴스] 외국인·기관 코스닥 순매수 상위 종목에 {current_stock} 이름 올렸다 (3일 전)")

# 대시보드 화면 실행
render_interactive_dashboard()
