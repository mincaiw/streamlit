from dataclasses import dataclass, field
from typing import Optional, Tuple
import datetime
import uuid

@dataclass
class Minwon:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    date: datetime.date = field(default_factory=datetime.date.today)
    korean_address: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None
    author: Optional[str] = None
    category: str = "기타"
    like_count: int = 0
    status: str = "미해결"

    def to_display_string(self) -> str:
        # ...
        pass

# ====입력 필드====
def get_minwon_title_input() -> str:
    return st.text_input("민원 제목:", key="minwon_title_input", placeholder="민원의 주요 내용을 간략하게 입력해주세요.")

def get_minwon_content_input() -> str:
    return st.text_area("민원 내용:", height=150, key="minwon_content_input", placeholder="상세한 민원 내용을 작성해주세요.")

def get_minwon_category_input() -> str:
    categories = ["교통 불편", "환경 문제", "시설 개선", "안전 문제", "기타 건의"]
    return st.selectbox("민원 유형:", categories, key="minwon_category_input")

def get_minwon_date_input() -> datetime.date:
    return st.date_input("날짜 선택:", value=datetime.date.today(), key="minwon_date_input")

def get_minwon_author_input() -> str:
    return st.text_input("제출자 이름 (선택 사항):", key="minwon_author_input", placeholder="이름을 남겨주세요.")
    
#====지도====   
def display_interactive_map():
    st.subheader("1. 지도에서 민원 위치 선택")
    if "map_center" not in st.session_state:
        st.session_state.map_center = INITIAL_MAP_CENTER
    if "selected_map_coordinates" not in st.session_state:
        st.session_state.selected_map_coordinates = None
    if "selected_korean_address" not in st.session_state:
        st.session_state.selected_korean_address = ""

    m = folium.Map(location=st.session_state.map_center, zoom_start=INITIAL_MAP_ZOOM)
    if st.session_state.selected_map_coordinates:
        folium.Marker(
            location=st.session_state.selected_map_coordinates,
            popup=st.session_state.selected_korean_address or "선택된 위치",
            tooltip=st.session_state.selected_korean_address or "선택된 위치"
        ).add_to(m)

    map_data = st_folium(m, width=700, height=500, key="interactive_map")
    if map_data and map_data.get("last_clicked"):
        last_click = map_data["last_clicked"]
        clicked_coords_tuple = (last_click["lat"], last_click["lng"])
        if clicked_coords_tuple != st.session_state.selected_map_coordinates:
            st.session_state.selected_map_coordinates = clicked_coords_tuple
            st.session_state.map_center = [last_click["lat"], last_click["lng"]]
            address = get_address_from_coords(last_click["lat"], last_click["lng"])
            st.session_state.selected_korean_address = address if address else "주소를 찾을 수 없습니다."

    if st.session_state.selected_map_coordinates:
        lat, lon = st.session_state.selected_map_coordinates
        st.success(f"선택된 좌표: 위도 {lat:.5f}, 경도 {lon:.5f}")
        if st.session_state.selected_korean_address:
            st.info(f"자동 인식된 주소: {st.session_state.selected_korean_address}")
    else:
        st.info("지도에서 민원 발생 위치를 클릭해주세요.")

    return st.session_state.selected_map_coordinates, st.session_state.selected_korean_address