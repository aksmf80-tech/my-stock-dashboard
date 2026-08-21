import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import datetime
from supabase import create_client, Client

# =================================================================
# 1. 페이지 레이아웃 세팅 (상단 시스템 여백 전면 개방)
# =================================================================
st.set_page_config(
    page_title="실시간 주도주 테마 전광판",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =================================================================
# 2. HTS 스타일 컴팩트 CSS 세팅 (🚨 카페 배너 & 종목 짤림 절대 방어막)
# =================================================================
st.markdown("""
    <style>
    /* [천장 차단막 완전 철거]: 스트림릿 고유 상단 투명 헤더의 억압을 완벽하게 부수고 밀어 올립니다! */
    [data-testid="stHeader"] { background: transparent !important; height: 0rem !important; display: none !important; }
    
    /* 전체 화면 가두리 패딩을 위쪽으로 넉넉하게 6.5rem 확장하여 배너가 절대 안 잘리게 방어합니다. */
    .block-container { padding-top: 6.5rem !important; padding-bottom: 0.5rem !important; }
    [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
    hr { margin: 0.6rem 0 !important; }
    
    /* 네이버 카페 배너 박스 절대 좌표 고정 */
    .cafe-banner-container {
        margin-top: -5.0rem !important;
        margin-bottom: 1.8rem !important;
        text-align: center !important;
        width: 100% !important;
    }
    
    /* HTS 전광판 규격 대왕 글씨 배너 테두리 및 정렬 최적화 */
    .master-box-custom-up {
        background-color: #1E293B !important;
        border-left: 8px solid #EF4444 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    .master-box-custom-down {
        background-color: #1E293B !important;
        border-left: 8px solid #3B82F6 !important;
        padding: 16px 22px !important;
        border-radius: 6px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center;
    }
    
    /* 우측 종목 박스 가독성 및 HTS 호가창 규격 대형화 서체 */
    .stock-box-up {
        border-left: 8px solid #EF4444 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stock-box-down {
        border-left: 8px solid #3B82F6 !important;
        background-color: #1E293B !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stock-name-up { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-name-down { color: #FFF !important; font-weight: 800 !important; font-size: 18px !important; }
    .stock-rate-up { color: #F87171 !important; font-weight: 900 !important; font-size: 19px !important; }
    .stock-rate-down { color: #60A5FA !important; font-weight: 900 !important; font-size: 19px !important; }
    </style>
""", unsafe_allow_html=True)
# =================================================================
# 3. 수파베이스 클라우드 직통 연결 인증 및 데이터 파이프라인 (대형주 해제 버전)
# =================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=1)
def load_market_data():
    try:
        response = supabase.table("kiwoom_themes").select("*").execute()
        rows = []
        for item in response.data:
            r_val = item.get('theme_flu_rt')
            p_val = item.get('current_price')
            t_name = str(item.get('theme_name', '미분류')).strip()
            
            rows.append({
                'theme': t_name,
                'name': str(item.get('stock_name', '알수없음')).strip(),
                'code': str(item.get('stock_code', '005930')).strip(),
                'rate': float(r_val) if r_val is not None else 0.0,
                'price': int(p_val) if p_val is not None else 0
            })
        base_df = pd.DataFrame(rows)
    except Exception as e:
        base_df = pd.DataFrame(columns=['theme', 'name', 'code', 'rate', 'price'])

    if not base_df.empty:
        # 🚨 [형님 특명 - 가두리 전면 철거 완공]: '대형주마스터'를 여기서 절대 지우지 않습니다!
        # 대한민국 2,200마리 고기 원본을 그대로 통투과시켜야 삼전/하이닉스 시세가 뚫고 나옵니다.
        filtered_df = base_df[~base_df['theme'].isin(['미분류', '빈방_대기', '준비중_테마', 'SKELETON_BASE', ''])]
        
        if not filtered_df.empty:
            # 💡 [히트맵 분리 장치]: 좌측 히트맵 그리드에서만 '대형주마스터' 블록을 안 보이게 숨겨서 전광판을 컴팩트하게 만들고,
            # 대장주 시세 조회용 원본 데이터셋에는 완벽하게 생존시켜 둡니다!
            heatmap_target_df = filtered_df[filtered_df['theme'] != '대형주마스터']
            
            if not heatmap_target_df.empty:
                agg_df = heatmap_target_df.groupby('theme')['rate'].mean().reset_index()
            else:
                agg_df = pd.DataFrame(columns=['theme', 'rate'])
            
            kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            current_time_str = kst_now.strftime('%Y-%m-%d %H:%M:%S')
            
            if not agg_df.empty:
                status_df = pd.DataFrame({
                    '테마': agg_df['theme'],
                    '등락률': agg_df['rate'].round(2),
                    '업데이트시간': [current_time_str] * len(agg_df)
                })
                status_df = status_df.sort_values(by='등락률', ascending=False).reset_index(drop=True)
                status_df['화면크기_가중치'] = np.linspace(35, 10, len(status_df)) if len(status_df) > 0 else []
            else:
                status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        else:
            status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
    else:
        status_df = pd.DataFrame(columns=['테마', '등락률', '화면크기_가중치', '업데이트시간'])
        
    # 🚨 [중요]: 삼성전자와 SK하이닉스가 100% 살아 숨쉬는 filtered_df를 첫 번째 인자로 정직하게 밀어줍니다!
    return filtered_df, status_df

# 변수 매핑 연동 최종 완공
raw_df, status_df = load_market_data()

kst_current = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
update_time = kst_current.strftime('%H:%M:%S')

# =================================================================
# 4. 🏛️ 시그널공장 네이버 카페 대문 부활 표출
# =================================================================
st.markdown(
    "<div class='cafe-banner-container'>\n"
    "  <a href='https://naver.com' target='_blank' style='text-decoration:none;'>\n"
    "    <button style='background-color:#03C75A; color:white; font-weight:bold; font-size:18px; \n"
    "    border:none; padding:15px 24px; border-radius:6px; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); width:100%; font-family:sans-serif;'>\n"
    "      🏛️ 시그널공장 네이버 카페 바로가기\n"
    "    </button>\n"
    "  </a>\n"
    "</div>", 
    unsafe_allow_html=True
)

st.markdown(f"<p style='text-align:right; margin:0; padding-bottom:12px; color:#64748B; font-size:12px; font-weight:bold;'>🔄 실시간 동기화: {update_time}</p>", unsafe_allow_html=True)

# =================================================================
# 5. [HTS 규격 대왕 글씨] 삼성전자 & SK하이닉스 상시 배치 (🚨 최종 변수 싱크 완공)
# =================================================================
master_2_cols = st.columns(2)
m_targets = [("삼성전자", "005930"), ("SK하이닉스", "000660")]

for idx, (m_name, m_code) in enumerate(m_targets):
    m_price = 0  
    m_rate = 0.0
    is_data_loaded = False

    try:
        if not raw_df.empty:
            # 🚨 [최종 버그 사멸]: load_market_data()에서 이미 'code' 필드로 변환 포장해 두었으므로,
            # 'code' 컬럼을 1대1로 직접 저격해야 한 치의 오차도 없이 시세가 관통되어 들어옵니다!
            raw_df['code_clean'] = raw_df['code'].astype(str).str.strip()
            target_rows = raw_df[raw_df['code_clean'] == m_code]
            
            if not target_rows.empty:
                latest_row = target_rows.iloc[-1]
                
                # 가공 완료된 딕셔너리 명칭인 'price'와 'rate' 축으로 정확하게 데이터 강탈 완료
                p_live = int(latest_row['price'])
                r_live = float(latest_row['rate'])
                
                if p_live > 0:
                    m_price = p_live
                    m_rate = r_live
                    is_data_loaded = True
    except:
        pass

    with master_2_cols[idx]:
        # 💡 매핑 엇박자 오류가 완전히 분쇄되어 월요일 장전 찐 시세 데이터 패킷이 다이렉트로 상단 배너에 꽂힙니다!
        if is_data_loaded:
            price_display = f"{m_price:,}원"
            sign_str = "+" if m_rate > 0 else ""
            if m_rate >= 0:
                st.markdown(f"""
                    <div class='master-box-custom-up'>
                        <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                        <span style='color:#EF4444; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} ({sign_str}{m_rate:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='master-box-custom-down'>
                        <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                        <span style='color:#3B82F6; font-weight:900; font-size:26px; margin-left:auto;'>{price_display} ({m_rate:.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='master-box-custom-up' style='border-left:8px solid #64748B !important;'>
                    <span style='color:#FFFFFF; font-weight:800; font-size:24px;'>🏛️ {m_name}</span>
                    <span style='color:#94A3B8; font-weight:900; font-size:24px; margin-left:auto;'>대기중 (0원)</span>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =================================================================
# 6. 하단 레이아웃 (핀업 스타일 컬러링 + [좌:상승 / 우:하락] 완공 버전)
# =================================================================

# 세션 상태 사전 완전 초기화
if "selected_theme_click" not in st.session_state:
    st.session_state.selected_theme_click = ""

# 초기 화면 공백 파괴: 장 시작 시 등락률 대장 1위 테마 자동 프리로딩
if not st.session_state.selected_theme_click and not status_df.empty:
    st.session_state.selected_theme_click = str(status_df['테마'].iloc[0]).strip()

left_layout, right_layout = st.columns([4.4, 5.6], gap="large")

with left_layout:
    st.markdown("### 🗺️ 실시간 주도 테마 히트맵 (좌상단 상승 저격형)")

    if not status_df.empty:
        try:
            # 🎨 [HTS 신호등 5단 그라데이션 엔진]: 마이너스는 블루, 0% 보합은 다크, 플러스는 핀업 레드로 고정
            hts_color_scale = [
                [0.0, "#0044AA"],   # 하락 극대값
                [0.45, "#1E293B"],  # 미세 하락
                [0.5, "#0F172A"],   # 🎯 정확한 0.00% 보합 영점 (HTS 순정 리얼 블랙)
                [0.55, "#2D1515"],  # 미세 상승
                [1.0, "#CC0000"]    # 당일 주도 테마 강렬한 레드
            ]
            
            max_rate = float(status_df['등락률'].max())
            min_rate = float(status_df['등락률'].min())
            bound = max(abs(max_rate), abs(min_rate), 1.0)

            fig = px.treemap(
                status_df, 
                path=['테마'], 
                values='화면크기_가중치', 
                color='등락률',             
                color_continuous_scale=hts_color_scale, 
                range_color=[-bound, bound], 
                custom_data=['테마']
            )
            
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{color:.2f}%", 
                textfont=dict(size=15, color="white", family="sans-serif"), 
                textposition="middle center"
            )
            
            fig.update_layout(
                margin=dict(t=5, b=5, l=5, r=5), 
                height=620,
                coloraxis_showscale=False, 
                template="plotly_dark"
            )
            
            chart_res = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # 🎯 [트리맵 클릭 0초 반응 매핑]: 누르는 족족 우측 리더보드가 칼같이 변합니다.
            if chart_res and isinstance(chart_res, dict) and "selection" in chart_res:
                points_list = chart_res["selection"].get("points", [])
                if points_list and len(points_list) > 0:
                    first_point = points_list[0]
                    
                    if isinstance(first_point, dict):
                        custom_data_val = first_point.get("customdata", [])
                        label_val = first_point.get("label", "")
                        
                        chosen_lbl = custom_data_val[0] if (custom_data_val and isinstance(custom_data_val, list)) else label_val
                        
                        if chosen_lbl and str(chosen_lbl).strip() != st.session_state.selected_theme_click:
                            st.session_state.selected_theme_click = str(chosen_lbl).strip()
                            st.rerun()
                            
        except Exception as chart_err:
            st.error(f"📊 히트맵 컬러 엔진 연동 오류 방어: {chart_err}")
    else:
        st.info("📊 수파베이스 양식장 통덤프 패킷을 수신 대기 중입니다.")

with right_layout:
    chosen_theme = str(st.session_state.selected_theme_click).strip()
    
    if not status_df.empty and chosen_theme:
        st.markdown(f"### 🗂️ <span style='font-size:24px;'><b>[{chosen_theme}]</b> 테마 양방향 포지션 보드</span>", unsafe_allow_html=True)
        
        final_stock_list = []
        if not raw_df.empty:
            raw_df['theme_clean'] = raw_df['theme'].astype(str).str.strip()
            theme_detail_df = raw_df[raw_df['theme_clean'] == chosen_theme].copy()
            
            for _, row in theme_detail_df.iterrows():
                s_price = int(row.get('price', 0))
                s_name = str(row.get('name', '알수없음')).strip()
                s_rate = float(row.get('rate', 0.0))
                s_code = str(row.get('code', '005930')).strip()
                final_stock_list.append((s_name, s_rate, s_price, s_code))
                
        # 등락률 포지션별 안전 해체
        up_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r >= 0]
        down_stocks = [(n, r, p, c) for n, r, p, c in final_stock_list if r < 0]
        
        # 🔺 상승주 대장 순 정렬(내림차순) / 🔹 하락주 소외주 순 정렬(오름차순) 축 고정
        up_stocks = sorted(up_stocks, key=lambda x: x[1], reverse=True)
        down_stocks = sorted(down_stocks, key=lambda x: x[1], reverse=False)
        
        # 💡 [형님 특명 완공 레이아웃]: 뉴스를 싹 다 걷어내고, 좌상승 우하락 1대1 대칭 듀얼 호가창 가동!
        sub_col1, sub_col2 = st.columns([5.0, 5.0], gap="medium")
        
        with sub_col1:
            st.markdown(f"#### 🔺 소속 상승 종목 ({len(up_stocks)}개)", unsafe_allow_html=True)
            with st.container(height=520, border=True):
                if up_stocks:
                    for s_name, s_rate, s_price, s_code in up_stocks[:50]:
                        st.markdown(
                            f"<div class='stock-box-up' style='padding: 10px 14px !important; margin-bottom: 5px !important;'>"
                            f"  <span class='stock-name-up' style='font-size:16px !important;'>🔺 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-up' style='font-size:16px !important;'>{s_price:,}원 (+{s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                else:
                    st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 상승 종목이 없습니다.</p>", unsafe_allow_html=True)
                    
        with sub_col2:
            st.markdown(f"#### 🔹 소속 하락 종목 ({len(down_stocks)}개)", unsafe_allow_html=True)
            with st.container(height=520, border=True):
                if down_stocks:
                    for s_name, s_rate, s_price, s_code in down_stocks[:50]:
                        st.markdown(
                            f"<div class='stock-box-down' style='padding: 10px 14px !important; margin-bottom: 5px !important;'>"
                            f"  <span class='stock-name-down' style='font-size:16px !important;'>🔹 {s_name} <small style='font-size:11px; color:#94A3B8;'>{s_code}</small></span>"
                            f"  <span class='stock-rate-down' style='font-size:16px !important;'>{s_price:,}원 ({s_rate:.2f}%)</span>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                else:
                    st.write("<p style='color:#64748B; padding:10px;'>당일 해당 테마에 하락 종목이 없습니다.</p>", unsafe_allow_html=True)
    else:
        st.markdown("### 🗂️ 소속 종목 리더보드")
        st.info("🔄 데이터 패킷 수신 대기 중...")

# =================================================================
# 7. 오토 리프레시 엔진 구동
# =================================================================
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, key="market_data_refresh_engine_24h")
except:
    pass
