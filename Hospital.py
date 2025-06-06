import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import chardet

# ✅ CSV 자동 인코딩 감지 후 불러오기
@st.cache_data
def load_data(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']

    df = pd.read_csv(file_path, encoding=encoding)
    df.columns = df.columns.str.strip()  # 공백 제거

    # 좌표 변환기: EPSG 5174 → WGS84
    transformer = Transformer.from_crs("epsg:5174", "epsg:4326", always_xy=True)

    def convert_coords(row):
        try:
            lon, lat = transformer.transform(row["좌표정보x(epsg5174)"], row["좌표정보y(epsg5174)"])
            return pd.Series([lat, lon])
        except:
            return pd.Series([None, None])

    df[["위도", "경도"]] = df.apply(convert_coords, axis=1)

    # 시/구 추출
    df["시"] = df["소재지전체주소"].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
    df["구"] = df["소재지전체주소"].apply(lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else "")

    # 정상 데이터만 필터
    df = df.dropna(subset=["위도", "경도"])
    df = df[df["영업상태명"] == "영업/정상"]

    return df

# 🏁 시작
st.set_page_config(page_title="병원 위치 지도", layout="wide")
st.title("🏥 시/구 기반 병원 지도 및 정보 앱")

# CSV 파일 경로 설정
csv_path = "your_hospital_data.csv"  # ← 여기를 자신의 파일명으로 바꾸세요!
df = load_data(csv_path)

# 사용자 선택
cities = sorted(df["시"].dropna().unique())
selected_city = st.selectbox("시를 선택하세요", cities)

gus = sorted(df[df["시"] == selected_city]["구"].dropna().unique())
selected_gu = st.selectbox(f"{selected_city}의 구를 선택하세요", gus)

filtered = df[(df["시"] == selected_city) & (df["구"] == selected_gu)]

# 지도 + 정보
if not filtered.empty:
    st.subheader(f"🗺️ {selected_city} {selected_gu} 병원 지도")
    m = folium.Map(location=[filtered["위도"].mean(), filtered["경도"].mean()], zoom_start=13)

    for _, row in filtered.iterrows():
        popup = f"""
        <b>{row['사업장명']}</b><br>
        주소: {row['소재지전체주소']}<br>
        전화: {row['소재지전화']}<br>
        종별: {row.get('의료기관종별명', '-')},<br>
        진료과: {row.get('진료과목내용명', '-')}
        """
        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=popup,
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
            - 유형: {row.get('의료기관종별명', '-')}  
            - 과목: {row.get('진료과목내용명', '-')}\n
            ---
            """)

    st.subheader("📊 전체 병원 정보")
    st.dataframe(filtered[["사업장명", "소재지전체주소", "소재지전화", "의료기관종별명", "진료과목내용명"]], use_container_width=True)

else:
    st.warning(f"{selected_city} {selected_gu} 지역에는 병원 정보가 없습니다.")
