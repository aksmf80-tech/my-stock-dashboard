# ---------------------------------------------------------
# 구역 1: 등락률 시각화용 트리맵 (색상 밸런스 정밀 조정)
# ---------------------------------------------------------
# 🎨 핀업처럼 깔끔한 대칭 색상을 위해 데이터의 절댓값 최댓값을 구합니다.
v_min = df['등락률'].min()
v_max = df['등락률'].max()
abs_max = max(abs(v_min), abs(v_max), 3.0) # 최소 보정치 3% 확보

fig = px.treemap(
    df, 
    path=['테마'], 
    values='화면크기_고정',  
    color='등락률',        
    color_continuous_scale='RdBu_r', # 역방향 Red-Blue (상승 빨강, 하락 파랑)
    range_color=[-abs_max, abs_max], # ⚠️ 핵심: 0을 정확히 중심으로 잡기 위해 마이너스 값 대칭 강제 지정
    hover_data=['종목명']
)

# 🎨 핀업 스타일처럼 테두리를 하얀색 선으로 깔끔하게 마감하고 가독성 확보
fig.update_traces(
    maxdepth=1, 
    textinfo="label+value",
    marker=dict(line=dict(width=1.5, color='white')) # 사각형 구분선 굵게 조정
)

fig.update_layout(
    dragmode=False,    
    margin=dict(t=10, l=10, r=10, b=10), 
    height=380,
    coloraxis_continuous_scale='RdBu_r',
    coloraxis_midpoint=0 # ⚠️ 핵심: 등락률 0% 지점을 무조건 완전한 보합 색상(흰색/연회색)으로 고정
)

# 차트 표출
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
