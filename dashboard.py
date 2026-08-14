import datetime
import pandas as pd
import plotly.express as px
import FinanceDataReader as fdr
import streamlit as st

# 1. 웹사이트 상단 타이틀 및 레이아웃 설정
st.set_page_config(page_title="실시간 주식 테마 지니", layout="wide")
st.title("📊 실시간 주식 테마 대시보드")
st.markdown("FinanceDataReader와 Streamlit을 활용한 실시간 테마별 등락률 지도입니다.")

# 2. 샘플 종목 데이터 구성
theme_data = [
    {"테마": "자동차 부품", "종목명": "명신산업", "티커": "009900"},
    {"테마": "자동차 부품", "종목명": "네오오토", "티커": "212390"},
    {"테마": "자동차 부품", "종목명": "대원강업", "티커": "000430"},
    {"테마": "시스템 반도체", "종목명": "삼성전자", "티커": "005930"},
    {"테마": "시스템 반도체", "종목명": "SK하이닉스", "티커": "000660"},
    {"테마": "시스템 반도체", "종목명": "한미반도체", "티커": "042700"},
    {"테마": "제약/바이오", "종목명": "삼성바이오로직스", "티커": "207940"},
    {"테마": "제약/바이오", "종목명": "셀트리온", "티ker": "068270"},
    {"테마": "제약/바이오", "종목명": "유한양행", "티커": "000100"},
]
df_theme = pd.DataFrame(theme_data)

# 3. 데이터 로딩 메시지 띄우기
with st.spinner("실시간 주가 데이터를 불러오는 중입니다..."):
    rows = []
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    for idx, row in df_theme.iterrows():
        try:
            df_price = fdr.DataReader(row["티커"], today_str)
            if not df_price.empty:
                change_pct = df_price.iloc[-1]["Change"] * 100
                rows.append({"테마": row["테마"], "종목명": row["종목명"], "등락률": round(change_pct, 2)})
            else:
                rows.append({"테마": row["테마"], "종목명": row["종목명"], "등락률": 0.0})
        except Exception:
            rows.append({"테마": row["테마"], "종목명": row["종목명"], "등락률": 0.0})

    df_result = pd.DataFrame(rows)
    df_result["시장"] = "국내 주식 시장"

# 4. 화면을 반으로 쪼개서 좌측엔 트리맵, 우측엔 상세 표 보여주기
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 테마 트리맵 지도")
    fig = px.treemap(
        df_result,
        path=["시장", "테마", "종목명"],
        values=None,
        color="등락률",
        color_continuous_scale=["blue", "white", "red"],
        color_continuous_midpoint=0,
    )
    fig.update_traces(textinfo="label+value", hovertemplate="<b>%{label}</b><br>등락률: %{color:.2f}%")
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 실시간 등락률 순위")
    df_sorted = df_result[["테마", "종목명", "등락률"]].sort_values(by="등락률", ascending=False)
    st.dataframe(df_sorted, use_container_width=True, hide_index=True)

st.caption(f"최근 업데이트: {today_str} | 데이터 제공: FinanceDataReader")
