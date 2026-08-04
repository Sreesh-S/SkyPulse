"""
Sidebar Component for Atmosphere OS.
Provides multi-page navigation, city search input, quick presets, units toggle,
and favorite city shortcuts using native Streamlit UI elements.
"""

import streamlit as st
from typing import Tuple, List, Dict

try:
    import config
    POPULAR_CITIES = getattr(config, "POPULAR_CITIES", [
        {"name": "Tokyo", "country": "JP", "flag": "🇯🇵", "lat": 35.6762, "lon": 139.6503},
        {"name": "New York", "country": "US", "flag": "🇺🇸", "lat": 40.7128, "lon": -74.0060},
        {"name": "London", "country": "GB", "flag": "🇬🇧", "lat": 51.5074, "lon": -0.1278},
        {"name": "Paris", "country": "FR", "flag": "🇫🇷", "lat": 48.8566, "lon": 2.3522},
        {"name": "Sydney", "country": "AU", "flag": "🇦🇺", "lat": -33.8688, "lon": 151.2093},
        {"name": "Dubai", "country": "AE", "flag": "🇦🇪", "lat": 25.2048, "lon": 55.2708},
        {"name": "Singapore", "country": "SG", "flag": "🇸🇬", "lat": 1.3521, "lon": 103.8198},
        {"name": "Kochi", "country": "IN", "flag": "🇮🇳", "lat": 9.9312, "lon": 76.2673},
    ])
    DEFAULT_CITY = getattr(config, "DEFAULT_CITY", "Tokyo")
except Exception:
    DEFAULT_CITY = "Tokyo"
    POPULAR_CITIES = [
        {"name": "Tokyo", "country": "JP", "flag": "🇯🇵", "lat": 35.6762, "lon": 139.6503},
        {"name": "New York", "country": "US", "flag": "🇺🇸", "lat": 40.7128, "lon": -74.0060},
        {"name": "London", "country": "GB", "flag": "🇬🇧", "lat": 51.5074, "lon": -0.1278},
        {"name": "Paris", "country": "FR", "flag": "🇫🇷", "lat": 48.8566, "lon": 2.3522},
        {"name": "Sydney", "country": "AU", "flag": "🇦🇺", "lat": -33.8688, "lon": 151.2093},
        {"name": "Dubai", "country": "AE", "flag": "🇦🇪", "lat": 25.2048, "lon": 55.2708},
        {"name": "Singapore", "country": "SG", "flag": "🇸🇬", "lat": 1.3521, "lon": 103.8198},
        {"name": "Kochi", "country": "IN", "flag": "🇮🇳", "lat": 9.9312, "lon": 76.2673},
    ]


def render_sidebar() -> Tuple[str, str, str, str]:
    """Render the application sidebar and return navigation state."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-weight: 800; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; color: transparent;">
                    ATMOSPHERE OS
                </h3>
                <p style="margin: 0.25rem 0 0; color: var(--text-muted); font-size: 0.8rem;">
                    Weather Analytics Suite
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page_items = [
            ("Dashboard", "⚡ Overview"),
            ("Forecast", "📅 5-Day Forecast"),
            ("Analytics", "📊 Climate Analytics"),
            ("Air Quality", "🍃 Air Quality"),
            ("About", "ℹ️ About Platform"),
        ]

        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = "Dashboard"

        for page_key, label in page_items:
            is_selected = st.session_state["selected_page"] == page_key
            button_type = "primary" if is_selected else "secondary"
            if st.button(label, key=f"nav_btn_{page_key}", type=button_type, use_container_width=True):
                if st.session_state["selected_page"] != page_key:
                    st.session_state["selected_page"] = page_key
                    st.rerun()

        selected_page = st.session_state["selected_page"]
        st.divider()

        st.caption("SEARCH LOCATION")
        city_input = st.text_input(
            label="Search City",
            value=st.session_state.get("current_city", DEFAULT_CITY),
            placeholder="e.g. Tokyo, Paris, Kochi...",
            label_visibility="collapsed",
        )

        st.caption("POPULAR DESTINATIONS")
        cols = st.columns(4)
        selected_preset = None
        for idx, city_obj in enumerate(POPULAR_CITIES[:8]):
            with cols[idx % 4]:
                if st.button(city_obj["flag"], key=f"btn_city_{idx}", help=city_obj["name"], use_container_width=True):
                    selected_preset = city_obj["name"]

        final_city = selected_preset if selected_preset else city_input
        st.session_state["current_city"] = final_city
        st.divider()

        st.caption("SETTINGS & UNITS")
        unit_col1, unit_col2 = st.columns(2)
        with unit_col1:
            unit_option = st.radio(
                "Units",
                options=["metric", "imperial"],
                format_func=lambda x: "°C Metric" if x == "metric" else "°F Imperial",
                index=0 if st.session_state.get("units", "metric") == "metric" else 1,
                label_visibility="collapsed",
            )
            st.session_state["units"] = unit_option

        with unit_col2:
            theme_option = st.radio(
                "Theme",
                options=["dark", "light"],
                format_func=lambda x: "🌙 Dark" if x == "dark" else "☀️ Light",
                index=0 if st.session_state.get("theme", "dark") == "dark" else 1,
                label_visibility="collapsed",
            )
            st.session_state["theme"] = theme_option

        st.divider()
        st.caption("FAVORITE CITIES")
        favorites: List[str] = st.session_state.get("favorites", ["Tokyo", "New York", "Kochi"])

        if final_city not in favorites:
            if st.button(f"+ Add {final_city} to Favorites", key="btn_add_fav", use_container_width=True):
                favorites.append(final_city)
                st.session_state["favorites"] = favorites
                st.rerun()

        for fav_item in favorites:
            if st.button(f"📍 {fav_item}", key=f"fav_btn_{fav_item}", use_container_width=True):
                st.session_state["current_city"] = fav_item
                st.rerun()

        return selected_page, final_city, unit_option, theme_option
