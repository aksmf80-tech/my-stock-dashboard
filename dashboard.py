# =========================================================================
# 3. 🎯 하단 종목 및 뉴스 동시 가변 연동 구역 (문법 에러 완벽 수정본)
# =========================================================================
st.subheader(f"📂 {chosen_theme} 테마 상세분석 정보")

@st.cache_data(ttl=600)
def fetch_theme_news(keyword):
    news_list = []
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://naver.com{encoded_keyword}&sm=tab_srt&sort=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        res = requests.get(url, headers=headers, timeout=3)
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

# 뉴스 크롤링 데이터 확보
current_news = fetch_theme_news(chosen_theme)

# [가변 레이아웃 조건 처리] 뉴스가 있을 때와 없을 때 분기
if current_news:
    # 📰 실시간 뉴스가 존재함 -> 5:5 비율로 화면 분할 레이아웃 작동
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 🔥 {chosen_theme} 소속 대장 종목 리스트")
        try:
            if 'theme' in raw_df.columns:
                theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
                avail_cols = []
                col_names = []
                if 'name' in theme_detail_df.columns: 
                    avail_cols.append('name'); col_names.append('종목명')
                if 'code' in theme_detail_df.columns: 
                    avail_cols.append('code'); col_names.append('종목코드')
                if 'market' in theme_detail_df.columns: 
                    avail_cols.append('market'); col_names.append('시장구분')
                    
                theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
                theme_df_clean.columns = col_names
                st.table(theme_df_clean.head(7))
            else:
                st.info("데이터셋에 theme 열이 존재하지 않습니다.")
        except Exception:
            st.info("종목 데이터를 읽어오는 중입니다...")

    with col2:
        st.markdown(f"### 📰 {chosen_theme} 관련 실시간 뉴스 정보")
        for news in current_news:
            st.markdown(f"""
                <div class="news-box">
                    <a href="{news['link']}" target="_blank" class="news-title">🔗 {news['title']}</a>
                    <div class="news-info">📰 {news['press']} | {chosen_theme} 관련 이슈</div>
                </div>
            """, unsafe_allow_html=True)

else:
    # 💡 실시간 뉴스가 완전히 없음 -> 100% 레이아웃 강제 활성화 및 try-except 예외 처리 보완 완료
    st.markdown(f"### 🔥 {chosen_theme} 소속 대장 종목 리스트 (실시간 뉴스 없음)")
    try:
        if 'theme' in raw_df.columns:
            theme_detail_df = raw_df[raw_df['theme'] == chosen_theme].copy()
            avail_cols = []
            col_names = []
            if 'name' in theme_detail_df.columns: 
                avail_cols.append('name'); col_names.append('종목명')
            if 'code' in theme_detail_df.columns: 
                avail_cols.append('code'); col_names.append('종목코드')
            if 'market' in theme_detail_df.columns: 
                avail_cols.append('market'); col_names.append('시장구분')
                
            theme_df_clean = theme_detail_df[avail_cols].reset_index(drop=True)
            theme_df_clean.columns = col_names
            st.table(theme_df_clean.head(15))
        else:
            st.info("데이터셋에 theme 열이 존재하지 않습니다.")
    except Exception:
        st.info("종목 데이터를 읽어오는 중입니다...")

# =========================================================================
# 4. 실시간 세션 자동 갱신 및 캐시 제어 타이머
# =========================================================================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 60:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
