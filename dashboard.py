import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import urllib.request
import re
from bs4 import BeautifulSoup

# 1. 반응형 전체화면 및 웹 브라우저 탭 제목 설정
st.set_page_config(page_title="실시간 주식 테마 대시보드", layout="wide")

# ⭐ 요청하신 부제목 설명 글자들을 모두 깔끔하게 지우고 메인 제목만 남겼습니다!
st.title("📊 실시간 주식 테마 대시보드")

# 2. 네이버 증권 전체 테마 및 종목 크롤링 함수 (장마감 및 주말 방어 적용)
@st.cache_data(ttl=60)
def fetch_naver_theme_data():
    try:
        url = "https://naver.com"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        theme_table = soup.find('table', {'class': 'type_5'})
        if not theme_table:
            return pd.DataFrame()
            
        rows = theme_table.find_all('tr')
        theme_list = []
        
        count = 0
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                theme_name_tag = cols.find('a')
                if theme_name_tag:
                    theme_name = theme_name_tag.text.strip()
                    theme_link = "https://naver.com" + theme_name_tag['href']
                    
                    change_tag = cols.find('span')
                    if change_tag:
                        change_text = change_tag.text.strip().replace('%','').replace('+','').replace(' ','')
                        try:
                            theme_change = float(change_text)
                            if 'nv01' in change_tag.get('class', []):
                                theme_change = -theme_change
                        except ValueError:
                            theme_change = 0.0
                    else:
                        try:
                            theme_change = float(cols.text.strip().replace('%','').replace('+','').replace(' ',''))
                        except:
                            theme_change = 0.0
                        
                    theme_list.append({
                        "테마": theme_name,
                        "테마등락률": theme_change,
                        "링크": theme_link
                    })
                    count += 1
                    if count >= 20: # 가독성을 위해 상위 20개 핵심 테마 수집
                        break
                        
        all_stocks = []
        for t_info in theme_list:
            try:
                t_req = urllib.request.Request(t_info["링크"], headers={'User-Agent': 'Mozilla/5.0'})
                t_html = urllib.request.urlopen(t_req).read()
                t_soup = BeautifulSoup(t_html, 'html.parser')
                
                stock_table = t_soup.find('table', {'class': 'type_5'})
                if stock_table:
                    s_rows = stock_table.find_all('tr')
                    s_count = 0
                    for s_row in s_rows:
                        s_cols = s_row.find_all('td')
                        if len(s_cols) >= 3:
                            s_name_tag = s_cols.find('a')
                            if s_name_tag:
                                s_name = s_name_tag.text.strip()
                                
                                try:
                                    s_price = int(s_cols.text.strip().replace(',', ''))
                                except:
                                    s_price = 0
                                    
                                s_change_tag = s_cols.find('span')
                                if s_change_tag:
                                    s_change_text = s_change_tag.text.strip().replace('%','').replace('+','').replace(' ','')
                                    try:
                                        s_change = float(s_change_text)
                                        if 'nv01' in s_change_tag.get('class', []):
                                            s_change = -s_change
                                    except:
                                        s_change = 0.0
                                else:
                                    try:
                                        s_change = float(s_cols.text.strip().replace('%','').replace('+','').replace(' ',''))
                                    except:
                                        s_change = 0.0
                                    
                                all_stocks.append({
                                    "테마": t_info["테마"],
                                    "테마등락률": t_info["테마등락률"],
                                    "종목명": s_name,
                                    "현재가": s_price,
                                    "등락률": s_change
                                })
                                s_count += 1
                                if s_count >= 5: # 테마별 주도종목 5개씩 매핑
                                    break
            except Exception:
                continue
                
        return pd.DataFrame(all_stocks)
    except Exception:
        return pd.DataFrame()

# 데이터 엔진 가동
with st.spinner("🔄 네이버 증권에서 시장 테마 데이터를 가져오는 중입니다..."):
    df_result = fetch_naver_theme_data()

if not df_result.empty:
    df_result["상자크기"] = df_result["테마등락률"].apply(lambda x: max(x + 25, 5))
    df_result["시장"] = "국내 주식 시장"

    # 3. 상단 대형 트리맵 지도 시각화
    st.subheader("🗺️ 실시간 테마 지도")
    fig = px.treemap(
        df_result,
        path=["시장", "테마", "종목명"],
        values="상자크기",
        color="등락률",
        color_continuous_scale=["blue", "white", "red"],
        color_continuous_midpoint=0,
    )
    fig.update_traces(textinfo="label+value", hovertemplate="<b>%{label}</b><br>등락률: %{color:.2f}%")
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=460)

    selected_points = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

    # 4. 네이버 실시간 뉴스 검색 크롤러
    def get_stock_news(keyword):
        try:
            encText = urllib.parse.quote(keyword + " 주식 뉴스")
            url = f"https://naver.com{encText}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            
            titles = re.findall(r'class="news_tit"[^>]*title="([^"]+)"', html)[:6]
            links = re.findall(r'class="news_tit"[^>]*href="([^"]+)"', html)[:6]
            
            news_list = []
            for t, l in zip(titles, links):
                news_list.append({"제목": t, "링크": l})
            return news_list
        except Exception:
            return [{"제목": "실시간 뉴스를 불러올 수 없습니다.", "링크": "#"}]

    # 5. 하단 5:5 완벽 연동 레이아웃
    st.write("---")
    selected_theme = None

    if selected_points and "points" in selected_points and len(selected_points["points"]) > 0:
        point_data = selected_points["points"]
        if "entry" in point_data:
            selected_theme = point_data["entry"]
        elif "label" in point_data:
            label = point_data["label"]
            if label in df_result["테마"].unique():
                selected_theme = label
            else:
                matched = df_result[df_result["종목명"] == label]
                if not matched.empty:
                    selected_theme = matched.iloc["테마"].values

    if selected_theme:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📈 {selected_theme} 관련 종목")
            df_filtered = df_result[df_result["테마"] == selected_theme][["종목명", "현재가", "등락률"]].sort_values(by="등락률", ascending=False)
            df_filtered["현재가"] = df_filtered["현재가"].apply(lambda x: f"{x:,}원")
            df_filtered["등락률"] = df_filtered["등락률"].apply(lambda x: f"+{x}%" if x > 0 else f"{x}%")
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            
        with col2:
            st.subheader(f"📰 {selected_theme} 관련 실시간 뉴스")
            news_data = get_stock_news(selected_theme)
            for item in news_data:
                st.markdown(f"• [{item['제목']}]({item['링크']})")
    else:
        st.info("💡 위 실시간 테마 지도에서 궁금한 테마 상자(예: '2차전지' 등)를 마우스로 클릭해 보세요! 하단에 종목 리스트와 실시간 뉴스가 좌우로 연동되어 나타납니다.")
else:
    st.warning("⚠️ 주말 또는 장마감 데이터 동기화 대기 중입니다. 잠시 후 새로고침(F5) 해주세요.")

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
st.caption(f"최근 업데이트: {today_str} | 데이터 제공: 네이버 페이 증권 크롤링 엔진")
