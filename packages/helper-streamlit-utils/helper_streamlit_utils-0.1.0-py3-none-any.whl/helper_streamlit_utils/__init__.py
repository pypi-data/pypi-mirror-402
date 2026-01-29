"""
helper-streamlit-utils
============

Streamlit 유틸리티 모음 라이브러리

주요 기능:
- st_label: Streamlit text_input과 동일한 스타일의 커스텀 라벨
- st_style_page_margin_hidden: 페이지 여백 및 헤더/툴바 숨김
- st_style_toolbar_hidden: 툴바만 숨김
- st_div_divider: 여백 최소화 구분선
- st_style_page_margin: 페이지 여백 커스터마이징
- st_settings_panel_show: 설정 패널 표시

기본 사용법:
    # 커스텀 라벨
    from helper_streamlit_utils import st_label
    st_label("Hello World", color="#ff0000")

    # 페이지 스타일링
    from helper_streamlit_utils import st_style_page_margin_hidden
    st_style_page_margin_hidden(top=0, left=10, right=10, bottom=0)

    # 구분선
    from helper_streamlit_utils import st_div_divider
    st_div_divider(height=2, color="#ddd")
"""

__version__ = "0.1.0"

# Import main functions
from .helper_streamlit_utils import (
    st_label,
    st_style_page_margin_hidden,
    st_style_toolbar_hidden,
    st_div_divider,
    st_style_page_margin,
    st_settings_panel_show,
)

__all__ = [
    # Streamlit utilities
    "st_label",
    "st_style_page_margin_hidden",
    "st_style_toolbar_hidden",
    "st_div_divider",
    "st_style_page_margin",
    "st_settings_panel_show",
    # Version
    "__version__",
]
