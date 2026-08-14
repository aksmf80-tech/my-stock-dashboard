import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# ⚠️ 주의: set_page_config는 항상 코드 최상단에 위치해야 에러가 나지 않습니다.
st.set_page_config(layout="wide")

# 🔔 홍보 배너
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://naver.com)에서 매일 확인하세요!**")

st.title("📊 테마별 현황판")

DATA_FILE = "theme_data.csv"

# 🟢 [핵심] 60초마다 이 안의 모든 요소(트리맵, 목록, 뉴스)를 깜빡임 없이 새로고침
@st.fragment(run_every=60)
def render_interactive_dashboard():
    if not os.path.exists(DATA_FILE):
        st.warning("⌛ 데이터 파일(theme_data.csv)을 기다리는 중입니다. 수집 앱을 확인해 주세요.")
        return

    # 최신 데이터 읽기
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

    required_cols = ['테마', '종목명', '등락률']
    if df is None or df.empty or not all(col in df.columns for col in required_cols):
        st.warning("📊 현재 표시할 주식 데이터 형식이 올바르지 않거나 데이터가 없습니다. 장이 열리면 자동으로 갱신됩니다.")
        return

    # 상단에 갱신 시각 표시 (F5 없이 1분마다 스스로 바뀜)
    st.success(f"🔄 실시간 데이터 동기화 완료! (최근 갱신 시각: {time.strftime('%H:%M:%S')})")

    # ---------------------------------------------------------
    # 구역 1: 핀업(FINUP) 스타일 ➡️ 클릭 시 화면이 꽉 차며 종목이 쪼개지는 트리맵
    # ---------------------------------------------------------
    # 💡 [핀업 완벽 재현 핵심] 
    # 첫 화면에서 대분류 테마만 깔끔하게 보이고 클릭 시 꽉 차게 확대되도록 px.Constant와 계층을 연결합니다.
    fig = px.treemap(
        df, 
        path=[px.Constant("시장 전체"), '테마', '종목명'], 
        values='등락률', 
        color='등락률',
        color_continuous_scale='RdBu_r', 
        hover_data=['업데이트시간']
    )
    
    # maxdepth=2를 설정하여 처음에는 '시장 전체 ➡️ 테마'까지만 보여주고 화면을 깔끔하게 유지합니다.
    fig.update_traces(maxdepth=2, textinfo="label+value")
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=500)
    
    # 스트림릿에 트리맵 그리기 및 클릭 감지 설정
    selected_theme = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # 🛠️ [iloc 오타 완벽 해결] 행 번호 [0]을 정확히 붙여서 인덱서 에러를 완전히 차단합니다.
    current_theme = df['테마'].iloc[0] if not df.empty else "선택된 테마 없음"
    
    # 트리맵 클릭 시 유저가 탐색하는 화면의 단계를 추적하여 하단 정보와 실시간으로 동기화합니다.
    if selected_theme and "points" in selected_theme and len(selected_theme["points"]) > 0:
        point_data = selected_theme["points"][0]
        clicked_label = point_data.get("label", current_theme)
        
        # 클릭한 구역이 실제 테마명이면 하단 정보를 변경
        if clicked_label in df['테마'].values:
            current_theme = clicked_label
        # 더 안쪽의 개별 종목 구역까지 클릭해 들어간 상태라면 부모(parent)인 테마명을 추적하여 유지
        elif "parent" in point_data and point_data["parent"] in df['테마'].values:
            current_theme = point_data["parent"]

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
        
        # 신버전 구버전 모두 에러 없는 안전한 드롭다운 선택 방식으로 변경
        current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

    with col2:
        st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
        st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
        
        # 주소 뒤에 직접 문자열을 결합하여 공백과 깨짐 현상을 완벽하게 제거
        stock_news_url = "https://naver.com" + str(current_stock)
        theme_news_url = "https://naver.com" + str(current_theme).replace(" ", "")
        
        st.markdown(f"📌 [📢 [뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)]({stock_news_url})")
        st.markdown(f"📌 [📢 [뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)]({theme_news_url})")
       
        # 🔗 뉴스 구역 맨 아래에도 블로그 이동 텍스트 링크 삽입
        st.markdown("---")
        st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://naver.com)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# 대시보드 화면 실행
render_interactive_dashboard()
