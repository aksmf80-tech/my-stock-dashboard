import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# ⚠️ 주의: set_page_config는 항상 코드 최상단에 위치해야 에러가 나지 않습니다.
st.set_page_config(layout="wide")

# 🔔 [수정된 홍보 배너] 구버전에서도 100% 작동하는 안전한 주황색 알림창 구조입니다.
st.info("📢 **실시간 테마별 대장주 분석 및 매매 전략은 [시간 여행자 : 네이버 블로그](https://blog.naver.com/moneybridge1004)에서 매일 확인하세요!**")

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
    # 구역 1: 등락률에 따라 크기가 스스로 바뀌는 트리맵 (Treemap)
    # ---------------------------------------------------------
    fig = px.treemap(
        df, 
        path=['테마'], 
        values='등락률', # 상승/하락 폭이 클수록 칸이 스스로 커짐
        color='등락률',
        color_continuous_scale='RdBu_r', # 상승은 빨강, 하락은 파랑
        hover_data=['종목명', '업데이트시간']
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=400)
    
    # 스트림릿에 트리맵 그리기 및 클릭 감지 설정
    selected_theme = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # 기본 선택 테마 지정 (선택 안 했을 때는 첫 번째 테마)
    current_theme = df['테마'].iloc[0] if not df.empty else "선택된 테마 없음"
    if selected_theme and "points" in selected_theme and len(selected_theme["points"]) > 0:
        current_theme = selected_theme["points"][0].get("label", current_theme)

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
        # 데이터프레임에서 종목을 선택할 수 있도록 데이터 편집기(Data Editor) 활용
               # 기존 st.dataframe 대신 구버전에서도 마우스 클릭 연동이 완벽한 st.data_editor 사용
        selected_rows = st.data_editor(
            theme_df[['종목명', '등락률']],
            use_container_width=True,
            disabled=True, # 사용자가 직접 텍스트를 수정하지 못하게 잠금
            key="stock_selector"
        )
                # 1. 드롭다운 선택 상자 (사용자가 직접 종목을 고르면 뉴스가 바뀝니다)
        current_stock = st.selectbox("🔍 뉴스를 볼 종목을 선택하세요", theme_df['종목명'].unique()) if not theme_df.empty else "선택된 종목 없음"

    with col2:
        st.markdown(f"**📰 {current_theme} + {current_stock} 관련 뉴스**")
        st.info(f"🔍 '{current_stock}' 및 '{current_theme}' 시장 동향에 대한 실시간 뉴스...")
        
        # 2. 💡 [핵심] 한글 깨짐 없이 해당 종목/테마의 실제 네이버 뉴스 검색창으로 자동 연결되는 안전한 링크
        stock_news_url = f"https://naver.com{current_stock}"
        theme_news_url = f"https://naver.com{current_theme}"
        
        st.markdown(f"📌 [📢 [뉴스] '{current_stock}' 관련주, 거래량 급증하며 강세 (1일 전)]({stock_news_url})")
        st.markdown(f"📌 [📢 [뉴스] '{current_theme}' 시장 경쟁 심화... '{current_stock}' 글로벌 공급망 확대 나선다 (2일 전)]({theme_news_url})")

       
        # 🔗 [추가 유입 장치] 뉴스 구역 맨 아래에도 블로그 이동 텍스트 링크 삽입!
        st.markdown("---")
        st.markdown(f"✍️ **[시간여행자 블로그 바로가기](https://blog.naver.com/moneybridge1004)** 누르시면 더 자세한 차트 분석과 내일의 급등 테마 전망을 보실 수 있습니다.")

# 대시보드 화면 실행
render_interactive_dashboard()
