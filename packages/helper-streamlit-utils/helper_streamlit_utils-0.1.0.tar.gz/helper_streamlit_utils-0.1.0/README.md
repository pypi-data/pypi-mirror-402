# helper-streamlit-utils

Streamlit 애플리케이션을 위한 유틸리티 모음 라이브러리

## 설치

```bash
pip install helper-streamlit-utils
```

## 주요 기능

### 1. 커스텀 라벨 (`st_label`)

Streamlit의 `text_input`과 동일한 스타일의 커스텀 라벨을 생성합니다.

```python
from helper_streamlit_utils import st_label

# 기본 스타일 사용
st_label("Hello World")

# 커스텀 스타일링
st_label("Custom Label",
         color="#ff0000",
         background_color="#f0f0f0",
         font_size="16px",
         font_weight="bold")
```

### 2. 페이지 스타일링

#### 페이지 여백 및 헤더 숨김 (`st_style_page_margin_hidden`)

```python
from helper_streamlit_utils import st_style_page_margin_hidden

# 상단/하단 여백 제거, 좌우 10px 유지
st_style_page_margin_hidden(top=0, left=10, right=10, bottom=0)
```

#### 툴바만 숨김 (`st_style_toolbar_hidden`)

```python
from helper_streamlit_utils import st_style_toolbar_hidden

st_style_toolbar_hidden()
```

#### 페이지 여백 커스터마이징 (`st_style_page_margin`)

```python
from helper_streamlit_utils import st_style_page_margin

# 상단 20px, 좌우 15px 여백 설정
st_style_page_margin(top=20, left=15, right=15, bottom=10)
```

### 3. 구분선 (`st_div_divider`)

여백 없는 구분선을 생성합니다.

```python
from helper_streamlit_utils import st_div_divider

# 기본 1px 회색 구분선
st_div_divider()

# 커스텀 구분선
st_div_divider(height=2, color="#ff0000")
```

### 4. 설정 패널 표시 (`st_settings_panel_show`)

Streamlit 설정 패널을 프로그래밍 방식으로 표시합니다.

```python
from helper_streamlit_utils import st_settings_panel_show

st_settings_panel_show()
```

## 전체 사용 예제

```python
import streamlit as st
from helper_streamlit_utils import (
    st_style_page_margin_hidden,
    st_label,
    st_div_divider
)

# 페이지 여백 제거
st_style_page_margin_hidden(top=0, left=10, right=10, bottom=0)

# 커스텀 라벨
st_label("Welcome to My App",
         font_size="24px",
         font_weight="bold",
         color="#1f77b4")

# 구분선
st_div_divider(height=2, color="#ddd")

# 일반 Streamlit 위젯들
st.write("This is a Streamlit app with custom styling!")
```

## 의존성

- `streamlit>=1.20.0`
- `helper-dev-utils>=0.5.0`

## 라이선스

MIT License

## 작성자

c0z0c (c0z0c.dev@gmail.com)

## 저장소

- Homepage: https://github.com/c0z0c-helper/helper_streamlit_utils
- Issues: https://github.com/c0z0c-helper/helper_streamlit_utils/issues
