import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 데이터 불러오기 (자신의 CSV 경로로 교체)
@st.cache_data
def load_data():
    df = pd.read_csv("your_hospital_data.csv")  # UTF-8 또는 CP949 인코딩 확인
    df = df.dropna(subset=["소재지전체주소", "위도", "경도"])
    return df

df = load_data()

# 주소에서 시, 구 추출
df['시'] = df['소재지전체주소'].apply(lambda x: x.split()[0] if isinstance(x, str) else '')
df['구'] = df['소재지전체주소'].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else '')

st.title("🏥 지역 기반 병원 위치 및 정보 안내 앱")

# 사용자 입력
cities = sorted(df['시'].dropna().unique())
selected_city = st.selectbox("어디 시에 사시나요?", cities)

filtered_city = df[df['시'] == selected_city]
gus = sorted(filtered_city['구'].dropna().unique())
selected_gu = st.selectbox(f"{selected_city}의 어느 구에 사시나요?", gus)

# 병원 필터링
filtered = df[(df['시'] == selected_city) & (df['구'] == selected_gu)]

st.subheader(f"🗺️ {selected_city} {selected_gu} 병원 지도")

if not filtered.empty:
    avg_lat = filtered['위도'].astype(float).mean()
    avg_lon = filtered['경도'].astype(float).mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

    for _, row in filtered.iterrows():
        popup_text = (
            f"<b>{row['사업장명']}</b><br>"
            f"{row['소재지전체주소']}<br>"
            f"☎ {row['소재지전화']}<br>"
            f"📍 진료과목: {row.get('진료과목내용명', '-')}"
        )
        folium.Marker(
            location=[row['위도'], row['경도']],
            popup=popup_text,
            tooltip=row['사업장명']
        ).add_to(m)

    col1, col2 = st.columns([2, 1])

    with col1:
        st_folium(m, width=800, height=500)

    with col2:
        st.markdown("### 📋 병원 목록")
        for i, row in filtered.iterrows():
            st.markdown(f"""
            **🏥 {row['사업장명']}**  
            주소: {row['소재지전체주소']}  
            전화번호: {row['소재지전화']}  
            진료과: {row.get('진료과목내용명', '-')}\n
            ---""")

    # 병원 표
    st.subheader("📊 병원 정보 표")
    st.dataframe(
        filtered[["사업장명", "소재지전체주소", "소재지전화", "의료기관종별명", "진료과목내용명"]],
        use_container_width=True
    )

else:
    st.warning(f"{selected_city} {selected_gu} 지역에는 병원 정보가 없습니다.")
