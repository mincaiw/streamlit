import streamlit as st
st.set_page_config(page_title="민원 접수 및 조회 시스템", layout="wide")
import os
import datetime
from dataclasses import dataclass, field
from typing import Tuple, Optional, List
import uuid
import pandas as pd
import folium
from streamlit_folium import st_folium
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import ast
import requests
from folium.plugins import MarkerCluster

# ====Google Sheets 설정정====
GS_COL_ID = 0
GS_COL_TITLE = 1
GS_COL_CONTENT = 2
GS_COL_DATE = 3
GS_COL_COORDINATES = 4
GS_COL_AUTHOR = 5
GS_COL_CATEGORY = 6
GS_COL_KOREAN_ADDRESS = 7
GS_COL_LIKE_COUNT = 8
GS_COL_STATUS = 9

try:
    SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
    if not os.path.exists(creds_path):
        st.error(f"Google Sheets 인증 정보 파일 ('token.json')을 다음 경로에서 찾을 수 없습니다: {creds_path}")
        st.stop()
    CREDS = ServiceAccountCredentials.from_json_keyfile_name(creds_path, SCOPE)
    GSPREAD_CLIENT = gspread.authorize(CREDS)
    YOUR_SHEET_NAME = '민원신청표'
    SHEET = GSPREAD_CLIENT.open(YOUR_SHEET_NAME).sheet1
    GOOGLE_SHEETS_ENABLED = True
except Exception as e:
    st.sidebar.error(f"Google Sheets 연결 실패: {e}")
    st.sidebar.warning("Google Sheets 기능이 비활성화됩니다. 데이터는 현재 세션에만 임시 저장됩니다.")
    GOOGLE_SHEETS_ENABLED = False
    SHEET = None

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

# ====== Google Sheets操作 ======
def save_minwon_to_gsheet(minwon_item: Minwon):
    if not GOOGLE_SHEETS_ENABLED or SHEET is None:
        st.warning("Google Sheets에 연결되지 않아 저장할 수 없습니다.")
        return
    try:
        row_to_append = [
            minwon_item.id,
            minwon_item.title,
            minwon_item.content,
            minwon_item.date.isoformat(),
            str(minwon_item.coordinates) if minwon_item.coordinates else "None",
            minwon_item.author or "익명",
            minwon_item.category,
            minwon_item.korean_address or "",
            minwon_item.like_count,
            minwon_item.status     # status 추가
        ]
        SHEET.append_row(row_to_append)
        st.success(f"민원 (ID: {minwon_item.id})이 Google Sheets에 성공적으로 저장되었습니다!")
    except Exception as e:
        st.error(f"Google Sheets에 저장 실패: {e}")

def load_minwons_from_gsheet() -> List[Minwon]:
    if not GOOGLE_SHEETS_ENABLED or SHEET is None:
        st.warning("Google Sheets에 연결되지 않아 불러올 수 없습니다.")
        return []
    try:
        all_rows_with_header = SHEET.get_all_values()
        if not all_rows_with_header or len(all_rows_with_header) < 1:
            st.info("Google Sheets에 데이터가 없습니다 (헤더 포함). 'ID', 'Title', 'Content', 'Date', 'Coordinates', 'Author', 'Category', 'Korean Address', 'Like Count', 'Status' 순서로 헤더를 만들어주세요.")
            return []

        header = all_rows_with_header[0]
        if len(all_rows_with_header) < 2:
            st.info("Google Sheets에 저장된 민원 데이터가 없습니다.")
            return []

        data_rows = all_rows_with_header[1:]
        minwons_list = []

        for i, row_data in enumerate(data_rows):
            try:
                num_expected_cols = 10
                if len(row_data) < num_expected_cols:
                    row_data.extend([""] * (num_expected_cols - len(row_data)))

                coords_str = row_data[GS_COL_COORDINATES]
                coordinates = None
                if coords_str and coords_str.lower() != "none" and coords_str.strip() != "":
                    try:
                        coordinates = ast.literal_eval(coords_str)
                        if not (isinstance(coordinates, tuple) and len(coordinates) == 2 and
                                all(isinstance(c, (float, int)) for c in coordinates)):
                            coordinates = None
                    except (ValueError, SyntaxError):
                        coordinates = None

                minwon_obj = Minwon(
                    id=row_data[GS_COL_ID],
                    title=row_data[GS_COL_TITLE],
                    content=row_data[GS_COL_CONTENT],
                    date=datetime.date.fromisoformat(row_data[GS_COL_DATE]) if row_data[GS_COL_DATE] else datetime.date.today(),
                    coordinates=coordinates,
                    author=row_data[GS_COL_AUTHOR] or "익명",
                    category=row_data[GS_COL_CATEGORY] or "기타",
                    korean_address=row_data[GS_COL_KOREAN_ADDRESS] or "",
                    like_count=int(row_data[GS_COL_LIKE_COUNT]) if row_data[GS_COL_LIKE_COUNT].isdigit() else 0,
                    status=row_data[GS_COL_STATUS] if len(row_data) > GS_COL_STATUS and row_data[GS_COL_STATUS] else "미해결"
                )
                minwons_list.append(minwon_obj)
            except Exception as e:
                st.error(f"행 데이터 처리 중 오류 발생 (행 번호 {i+2}, 내용: {row_data}): {e}")
        return minwons_list
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"오류: Google Sheet '{YOUR_SHEET_NAME}'을(를) 찾을 수 없습니다. 이름을 확인하고 서비스 계정에 접근 권한이 있는지 확인하세요.")
        return []
    except Exception as e:
        st.error(f"Google Sheets에서 데이터를 불러오는 중 오류 발생: {e}")