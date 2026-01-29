import random
from typing import Dict

import streamlit as st
import streamlit.components.v1 as components

__all__ = [
    "st_label",
    "st_style_page_margin_hidden",
    "st_style_toolbar_hidden",
    "st_div_divider",
    "st_style_page_margin",
    "st_settings_panel_show",
]


# Streamlit text_input과 동일한 기본 스타일
DEFAULT_LABEL_STYLE: Dict[str, str] = {
    "border": "0px solid #FFFFFF",
    "border-radius": "8px",
    "padding": "8px 12px",
    "background-color": "#FFFFFF",
    "color": "#31333F",
    "height": "38px",
    "line-height": "22px",
    "font-size": "14px",
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
    "text-align": "center",
}


def st_label(text: str, **kwargs: str) -> None:
    """Streamlit text_input과 동일한 스타일의 커스텀 라벨을 렌더링합니다.

    기본 스타일은 Streamlit의 text_input 위젯과 동일하며,
    **kwargs를 통해 원하는 CSS 속성을 자유롭게 오버라이드할 수 있습니다.

    Args:
        text: 표시할 텍스트 내용
        **kwargs: CSS 속성을 snake_case로 전달 (자동으로 kebab-case로 변환됨)
                 예: text_align="center", background_color="#f0f0f0"

    Examples:
        >>> # 기본 스타일 사용
        >>> st_label("Hello World")

        >>> # 가운데 정렬, 빨간색 텍스트
        >>> st_label("Centered Text", text_align="center", color="#ff0000")

        >>> # 배경색, 폰트 크기, 높이 변경
        >>> st_label(
        ...     "Custom Label",
        ...     background_color="#e3f2fd",
        ...     font_size="16px",
        ...     height="50px",
        ...     font_weight="bold"
        ... )

        >>> # kebab-case로 직접 전달도 가능 (비권장)
        >>> st_label("Test", **{"text-align": "right"})

    Notes:
        - snake_case 키는 자동으로 kebab-case CSS로 변환됩니다
          (예: text_align → text-align, background_color → background-color)
        - 기본 스타일: Streamlit 1.31.0 text_input 기반 (높이 38px, 폰트 14px 등)
        - 모든 CSS 속성을 자유롭게 사용 가능합니다
    """
    # 기본 스타일 복사
    merged_style = DEFAULT_LABEL_STYLE.copy()

    # kwargs를 kebab-case로 변환하여 병합
    for key, value in kwargs.items():
        css_key = key.replace("_", "-")
        merged_style[css_key] = value

    # CSS 문자열 생성
    style_string = "; ".join(f"{k}: {v}" for k, v in merged_style.items())

    # HTML 렌더링
    st.html(f'<div style="{style_string}">{text}</div>')


def st_style_page_margin_hidden(
    top: int = 0, left: int = 10, right: int = 10, bottom: int = 0
) -> None:
    """상단 여백을 제거하면서 사이드바 토글 버튼은 유지합니다.

    Streamlit의 기본 헤더/툴바를 숨기고 페이지 상단 여백을 제거하여
    더 많은 화면 공간을 확보합니다. 단, 사이드바 토글 버튼은 유지합니다.

    적용되는 스타일:
        - Streamlit 헤더/툴바 숨김
        - 메인 컨테이너 상단 여백 제거
        - 텍스트 요소 여백 최소화
        - 사이드바 토글 버튼 유지
    """
    st.html(
        f"""<style>
[data-testid="stHeader"] {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}        
.stMainBlockContainer {{
    padding-top: {top}px !important;
    padding-left: {left}px !important;
    padding-right: {right}px !important;
    padding-bottom: {bottom}px !important;
}}
.stVerticalBlock:first-of-type {{ margin: 0 !important; padding: 0 !important; }}
h1, h2, h3, h4, h5, h6, p, div {{ margin: 0 !important; padding: 0 !important; }}
hr.compact {{ display: none !important; margin: 0 !important; padding: 0 !important; }}
[data-testid="stSidebarNav"] {{ display: block !important; }}
</style>
"""
    )


def st_style_toolbar_hidden() -> None:
    """상단 여백을 제거하면서 사이드바 토글 버튼은 유지합니다.

    Streamlit의 기본 헤더/툴바를 숨기고 페이지 상단 여백을 제거하여
    더 많은 화면 공간을 확보합니다. 단, 사이드바 토글 버튼은 유지합니다.

    적용되는 스타일:
        - Streamlit 헤더/툴바 숨김
        - 메인 컨테이너 상단 여백 제거
        - 텍스트 요소 여백 최소화
        - 사이드바 토글 버튼 유지
    """
    st.html(
        """
<style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
</style>
"""
    )


def st_div_divider(height: int = 1, color: str = "#ddd") -> None:
    """여백 최소화 가로선을 렌더링합니다.

    기본 st.markdown("---")의 과도한 여백을 제거하고
    얇은 회색 구분선만 표시합니다.

    사용 예:
        st_div_divider()  # 1px 회색 구분선 표시
    """
    st.html(
        f'<div style="height: {height}px; background-color: {color}; margin: 0; padding: 0;"></div>'
    )


def st_style_page_margin(
    top: int = 0, left: int = 10, right: int = 10, bottom: int = 0
) -> None:
    """상단 여백을 제거하면서 사이드바 토글 버튼은 유지합니다.

    Streamlit의 기본 헤더/툴바를 숨기고 페이지 상단 여백을 제거하여
    더 많은 화면 공간을 확보합니다. 단, 사이드바 토글 버튼은 유지합니다.

    적용되는 스타일:
        - Streamlit 헤더/툴바 숨김
        - 메인 컨테이너 상단 여백 제거
        - 텍스트 요소 여백 최소화
        - 사이드바 토글 버튼 유지
    """
    st.html(
        f"""<style>
.stMainBlockContainer {{
    padding-top: {top}px !important;
    padding-left: {left}px !important;
    padding-right: {right}px !important;
    padding-bottom: {bottom}px !important;
}}
</style>"""
    )


def st_settings_panel_show() -> None:
    """상단 설정 패널을 렌더링합니다."""
    # 매번 다른 코드로 인식되도록 고유 ID 추가
    unique_id = random.randint(1000, 9999)

    components.html(
        f"""
        <script>
        // 고유 ID: {unique_id}
        (function() {{
            setTimeout(function() {{
                const targetDoc = window.parent.document;
                const mainMenuButton = targetDoc.querySelector('[data-testid="stMainMenu"] button');
                
                if (mainMenuButton) {{
                    mainMenuButton.click();
                    console.log('MainMenu opened (ID: {unique_id})');
                }} else {{
                    console.error('MainMenu button not found');
                }}
            }}, 100);
        }})();
        </script>
        """,
        height=0,
    )
