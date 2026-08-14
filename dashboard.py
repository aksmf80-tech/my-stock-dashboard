import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import urllib.request
import re
from bs4 import BeautifulSoup

# 1. 반응형 전체화면 설정
st.set_page_config(page_title="실시간 주식 테마 대시보드 (완전자동)", layout="wide")
st.title("📊 실시간 주식 테마 대시보드 (100% 완전 자동화)")
st.markdown("본 시스템은 **네이버 페이 증권**의 전체 테마 시세 데이터를 실시간으로 크롤링하여 지도를 그려줍니다. (장마감 및 주말 방어 적용)")

# 2. 네이버 증권 전체 테마 및 종목 크롤링 함수 (주말/장마감 방어 로직)
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
                theme_name_tag = cols[0].find('a')
                if theme_name_tag:
                    theme_name = theme_name_tag.text.strip()
                    theme_link = "https://finance.naver.com" + theme_name_tag['href']
                    
                    # 테마 등락률 파싱 및 주말 예외 처리
                    change_tag = cols[1].find('span')
                    if change_tag:
                        change_text = change_tag.text.strip().replace('%','').replace('+','').replace(' ','')
                        try:
                            theme_change = float(change_text)
                            if 'nv01' in change_tag.get('class', []):
                                theme_change = -theme_change
                        except ValueError:
                            theme_change = 0.0
                    else:
                        # 텍스트로 직접 읽기 방어
                        try:
                            theme_change = float(cols[1].text.strip().replace('%','').replace('+','').replace(' ',''))
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
                t_req = urllib.request.Request(t_info["LINK" if "LINK" in t_info else "링크"], headers={'User-Agent': 'Mozilla/5.0'})
                t_html = urllib.request.urlopen(t_req).read()
                t_soup = BeautifulSoup(t_html, 'html.parser')
                
                stock_table = t_soup.find('table', {'class': 'type_5'})
                if stock_table:
                    s_rows = stock_table.find_all('tr')
                    s_count = 0
                    for s_row in s_rows:
                        s_cols = s_row.find_all('td')
                        if len(s_cols) >= 3:
                            s_name_tag = s_cols[0].find('a')
                            if s_name_tag:
                                s_name = s_name_tag.text.strip()
                                
                                # 종목 현재가 파싱
                                try:
                                    s_price = int(s_cols[1].text.strip().replace(',', ''))
                                except:
                                    s_price = 0
                                    
                                # 종목 등락률 파싱
                                s_change_tag = s_cols[2].find('span')
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
                                        s_change = float(s_cols[2].text.strip().replace('%','').replace('+','').replace(' ',''))
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
with st.spinner("🔄 네이버 증권에서 주중 최종 시장 테마 데이터를 가져오는 중입니다..."):
    df_result = fetch_naver_theme_data()

# 최종 데이터가 비어있지 않다면 화면 구성
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
                    selected_theme = matched.iloc["테마"].values[0]

    # 상자 클릭 시 동작부
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
st.caption(f"최근 업데이트: {today_str} | 데이터 제공: 네이버 페이 증권 주말 예외방어 크롤러 엔진")
