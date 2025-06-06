import streamlit as st
import datetime
from dataclasses import dataclass, field
from typing import Optional, Tuple

@dataclass
class Minwon:
    id: str
    title: str
    content: str
    date: datetime.date
    coordinates: Optional[Tuple[float, float]]
    author: Optional[str]
    category: str
    like_count: int
    status: str

def main():
    st.title("민원 접수 및 조회 시스템")

if __name__ == "__main__":
    main()
