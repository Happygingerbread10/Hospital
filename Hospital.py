import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

@st.cache_data
def load_data():
    df = pd.read_csv("your_hospital_data.csv", encoding="cp949")  # 또는 utf-8
    df.columns = df.columns.str.strip()

    # EPSG:5174 → WGS84 변환기
    transformer = Transformer.from_crs("epsg:5174", "epsg:4326", always_xy=True)

    # 좌표 변환
    def convert_coords(row):
        try:
            lon, lat = transformer.transform(row["좌표정보x(epsg5174)"], row["좌표정보y(epsg5174)"])
            return pd.Series([lat, lon])
        except:
            return pd.Series([None, None])

    df[["위도", "경도"]] = df.apply(convert_coords, axis=1)

    # 주소에서 시/구 추출
    df["시"] = df["소재지전체주소"].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
    df["구"] = df["소재지전체주소"].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else "")
    df = df.dropna(subset=["위도", "경도"])
    return df

# 데이터 불러오기
df = load_data()

st.title("🏥 시/구 기반 병원 위치 안내")

# 사용자 입력
cities = sorted(df["시"].unique())
selected_city = st.selectbox("거주 중인 시를 선택하세요", cities)

gus = sorted(df[df["시"] == selected_city]["구"].unique())
selected_gu = st.selectbox(f"{selected_city}의 구를 선택하세요", gus)

# 필터링
filtered = df[(df["시"] == selected_city) & (df["구"] == selected_gu)]

if not filtered.empty:
    st.subheader(f"🗺️ {selected_city} {selected_gu} 지역 병원 지도")
    m = folium.Map(location=[filtered["위도"].mean(), filtered["경도"].mean()], zoom_start=13)

    for _, row in filtered.iterrows():
        popup_text = (
            f"<b>{row['사업장명']}</b><br>"
            f"{row['소재지전체주소']}<br>"
            f"☎ {row['소재지전화']}<br>"
            f"종별: {row.get('의료기관종별명', '-')}, 진료과: {row.get('진료과목내용명', '-')}"
        )
        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=popup_text,
            tooltip=row["사업장명"]
        ).add_to(m)

    col1, col2 = st.columns([2, 1])

    with col1:
        st_folium(m, width=800, height=500)

    with col2:
        st.markdown("### 📋 병원 요약 정보")
        for _, row in filtered.iterrows():
            st.markdown(f"""
            **🏥 {row['사업장명']}**  
            - 주소: {row['소재지전체주소']}  
            - 전화: {row['소재지전화']}  
            - 유형: {row.get('의료기관종별명', '-')}, 과목: {row.get('진료과목내용명', '-')}\n
            ---
            """)

    st.subheader("📊 전체 병원 정보")
    st.dataframe(filtered[["사업장명", "소재지전체주소", "소재지전화", "의료기관종별명", "진료과목내용명"]])

else:
    st.warning(f"{selected_city} {selected_gu} 지역 병원 정보가 없습니다.")
