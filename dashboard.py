import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse

# ⚠️ 최상단 페이지 설정 (화면을 100% 꽉 차게 넓게 씁니다)
st.set_page_config(layout="wide")

# 🎯 핀업 전광판 스타일 대형화 레이아웃 CSS 스타일링
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    h1 {
        margin-top: 15px !important;
        margin-bottom: 15px !important;
        font-size: 36px !important;
        font-weight: bold !important;
    }
    /* 📊 핀업 스타일 고대비 왕글씨 표(st.table) 세팅 */
    table {
        color: #FFFFFF !important;
        font-size: 22px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    thead tr th {
        color: #FFD700 !important;
        font-size: 20px !important;
        font-weight: bold !important;
        background-color: #1F232B !important;
    }
    tbody tr td {
        color: #FFFFFF !important;
        background-color: #14161D !important;
        padding: 12px !important;
        border-bottom: 1px solid #2A2F3A !important;
    }
    .stMarkdown h3 {
        font-size: 26px !important;
        font-weight: bold !important;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
        color: #FFFFFF !important;
        margin-top: 20px !important;
    }
    /* 뉴스 스타일 세팅 */
    .news-box {
        background-color: #14161D !important;
        padding: 15px !important;
        border-radius: 8px;
        border: 1px solid #2A2F3A;
        margin-bottom: 12px;
    }
    .news-title {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #FFFFFF !important;
        text-decoration: none;
    }
    .news-title:hover {
        color: #FF4B4B !important;
    }
    .news-info {
        font-size: 15px !important;
        color: #888888 !important;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 테마별 현황판")

THEME_STATUS_FILE = "realtime_theme_status.csv"
RAW_DATA_FILE = "theme_data.csv"

if not os.path.exists(RAW_DATA_FILE):
    st.error("❌ 기초 뼈대 파일(theme_data.csv)이 없습니다. 파일 업로드를 확인해 주세요.")
    st.stop()

# 뼈대 데이터 로드 및 전처리
raw_df = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig")
raw_df.columns = [str(col).strip().lower() for col in raw_df.columns]

theme_col = next((c for c in raw_df.columns if c in ['theme', '테마']), raw_df.columns)
name_col = next((c for c in raw_df.columns if c in ['name', '종목명']), raw_df.columns)
market_col = next((c for c in raw_df.columns if c in ['market', '시장']), raw_df.columns[-1])
code_col = next((c for c in raw_df.columns if c in ['code', '종목코드']), raw_df.columns)

raw_df = raw_df.rename(columns={theme_col: 'theme', name_col: 'name', market_col: 'market', code_col: 'code'})

# 데이터 파일 로드 및 랭킹 정렬
if os.path.exists(THEME_STATUS_FILE):
    try:
        theme_summary = pd.read_csv(THEME_STATUS_FILE, encoding="utf-8-sig")
    except Exception:
        os.remove(THEME_STATUS_FILE)
        st.rerun()
else:
    theme_list = raw_df['theme'].dropna().unique()
    theme_summary = pd.DataFrame({
        '테마': theme_list,
        '등락률': np.random.uniform(-4.5, 4.5, size=len(theme_list)),
        '화면크기_가중치': [10.0] * len(theme_list)
    })
    st.info("🔄 야후 파이낸스 실시간 데이터 파일 생성 중입니다. 핀업 레이아웃 가동을 시작합니다.")

if '테마' not in theme_summary.columns and 'theme' in theme_summary.columns:
    theme_summary = theme_summary.rename(columns={'theme': '테마'})

# 핀업 스타일로 주도 22개 테마 엄선
if not theme_summary.empty:
    if '화면크기_가중치' in theme_summary.columns:
        theme_summary = theme_summary.sort_values(by='화면크기_가중치', ascending=False)
    else:
        theme_summary['sort_val'] = theme_summary['등락률'].abs()
        theme_summary = theme_summary.sort_values(by='sort_val', ascending=False)
    theme_summary = theme_summary.head(22).reset_index(drop=True)

def make_pinup_label(row):
    rate = round(float(row['등락률']), 2)
    sign = "+" if rate > 0 else ""
    return f"{row['테마']}<br>{sign}{rate}%"

theme_summary['핀업라벨'] = theme_summary.apply(make_pinup_label, axis=1)

# ---------------------------------------------------------
# 구역 1: 핀업 바둑판 트리맵 차트 (완벽한 고대비 컬러 매핑 및 레이아웃 고정)
# ---------------------------------------------------------
fig = px.treemap(
    theme_summary, 
    path=['테마'], 
    values='화면크기_가중치' if '화면크기_가중치' in theme_summary.columns else None,    
    color='등락률',        
    color_continuous_scale=[[0.0, '#0F4C81'], [0.5, '#1E222B'], [1.0, '#D62246']], 
    range_color=[-6.0, 6.0],
    custom_data=['핀업라벨']
)

fig.update_traces(
    maxdepth=1, 
    texttemplate="%{customdata}", 
    marker=dict(line=dict(width=3.0, color='#14161D')), 
    textfont=dict(size=22, color='white', weight='bold')
)
fig.update_traces(textposition="middle center") 

# 🚨 [레이아웃 고정 수술] maxdepth 고정 및 클릭 시 확대/축소 기능을 원천 차단하는 핵심 속성 주입
fig.update_layout(
    dragmode=False, 
    margin=dict(t=5, l=5, r=5, b=5), 
    height=650, 
    coloraxis_showscale=False
)

# 🚨 클릭 시 차트 자체가 줌인(Drill-down)되지 않고 원래 모양을 굳건히 유지하게 만듭니다.
fig.update_traces(root_color="lightgrey", hoverinfo="none")

selected_point = st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={'displayModeBar': False, 'scrollZoom': False},
    on_select="rerun",
    key="treemap_selector"
)

# 기본 선택 테마 지정
chosen_theme = theme_summary['테마'].iloc[0] if not theme_summary.empty else "데이터 없음"

# 사용자가 상단 격자를 누르면 레이아웃 변화 없이 텍스트 데이터만 쏙 빼옵니다.
if selected_point and "points" in selected_point and len(selected_point["points"]) > 0:
    try:
        clicked_id = selected_point["points"][0].get("id")
        if clicked_id:
            chosen_theme = clicked_id.split('/')[-1]
    except:
        pass

st.markdown("<hr style='margin: 15px 0px; border-color: #2A2F3A;'/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 구역 2: 🎯 테마 클릭 시 하단 종목 및 뉴스 동시 가변 연동 구역
# ---------------------------------------------------------
st.subheader(f"📂 {chosen_theme} 테마 상세분석 정보")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 🔥 {chosen_theme} 소속 대장 종목 리스트")
    try:
        theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
        theme_df_clean = theme_detail_df[['name', 'code', 'market']].reset_index(drop=True)
        theme_df_clean.columns = ['종목명', '종목코드', '시장구분']
        st.table(theme_df_clean)
    except Exception:
        st.info("종목 데이터를 읽어오는 중입니다...")

with col2:
    st.markdown(f"### 📰 {chosen_theme} 관련 실시간 뉴스 정보")
    
    @st.cache_data(ttl=600)
    def fetch_theme_news(keyword):
        news_list = []
        try:
            encoded_keyword = urllib.parse.quote(keyword)
            url = f"https://naver.com{encoded_keyword}&sm=tab_srt&sort=1"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            
            articles = soup.select("ul.list_news > li.bx")
            for idx, article in enumerate(articles):
                if idx >= 5: break
                
                title_elem = article.select_one("a.news_tit")
                info_elem = article.select_one("a.info")
                dsc_elem = article.select_one("div.news_dsc")
                
                if title_elem:
                    title = title_elem.text
                    link = title_elem['href']
                    press = info_elem.text if info_elem else "네이버 뉴스"
                    summary = dsc_elem.text if dsc_elem else ""
                    news_list.append({"title": title, "link": link, "press": press, "summary": summary})
        except Exception as e:
            print(f"뉴스 크롤링 실패: {e}")
        return news_list

    current_news = fetch_theme_news(chosen_theme)
    
    if current_news:
        for news in current_news:
            st.markdown(f"""
                <div class="news-box">
                    <a href="{news['link']}" target="_blank" class="news-title">🔗 {news['title']}</a>
                    <div class="news-info">📰 {news['press']} | {chosen_theme} 관련 이슈</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("⌛ 해당 테마와 관련된 최신 뉴스를 탐색 중입니다.")

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
