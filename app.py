import os
import sys
import textwrap
import streamlit.components.v1 as components

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd

from api.weather import (
    get_current_weather, get_forecast, get_air_quality, get_city_from_coords
)
from utils.helpers import (
    get_unit_symbols, deg_to_compass, get_aqi_info, get_weather_color,
    format_timestamp, group_forecast_by_day
)
from utils.charts import create_hourly_chart, create_daily_chart
from utils.export import generate_json_export, generate_csv_export

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkyPulse | Premium Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. SHARED ANIMATIONS CSS (always injected)
# ─────────────────────────────────────────────────────────────────────────────
def load_css(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

load_css("styles/theme.css")

# ─────────────────────────────────────────────────────────────────────────────
# 3. SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "has_searched": False,
    "selected_city": "",
    "recent_searches": [],
    "theme_mode": "dark",
    "unit_system": "metric",
    "search_box_value": "",
    "geo_loading": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# 4. GEOLOCATION — handle ?lat=&lon= or ?city= query params injected by JS
# ─────────────────────────────────────────────────────────────────────────────
params = st.query_params
if "lat" in params and "lon" in params:
    try:
        lat_p = float(params["lat"])
        lon_p = float(params["lon"])
        with st.spinner("📡 Detecting your location..."):
            detected_city = get_city_from_coords(lat_p, lon_p)
        if detected_city:
            st.session_state.selected_city    = detected_city
            st.session_state.search_box_value = detected_city
            st.session_state.has_searched     = True
            if detected_city not in st.session_state.recent_searches:
                st.session_state.recent_searches.append(detected_city)
        st.query_params.clear()
        st.rerun()
    except Exception:
        st.query_params.clear()
elif "city" in params:
    try:
        c_p = str(params["city"]).strip()
        if c_p:
            st.session_state.selected_city    = c_p
            st.session_state.search_box_value = c_p
            st.session_state.has_searched     = True
            if c_p not in st.session_state.recent_searches:
                st.session_state.recent_searches.append(c_p)
        st.query_params.clear()
        st.rerun()
    except Exception:
        st.query_params.clear()

# ─────────────────────────────────────────────────────────────────────────────
# 5. THEME PALETTE  (must be defined before any CSS injection or HTML)
# ─────────────────────────────────────────────────────────────────────────────
is_dark = (st.session_state.theme_mode == "dark")

if is_dark:
    BG         = "#0B1120"
    CARD       = "#1E293B"
    GLASS      = "rgba(30,41,59,0.88)"
    BORDER     = "#334155"
    SHADOW     = "rgba(0,0,0,0.55)"
    GLOW       = "rgba(34,211,238,0.18)"
    TXT1       = "#F8FAFC"
    TXT2       = "#CBD5E1"
    TXTM       = "#94A3B8"
    BLUE       = "#60A5FA"
    CYAN       = "#22D3EE"
    HERO_GRAD  = "linear-gradient(135deg,#0F172A 0%,#111827 50%,#1E293B 100%)"
    BTN_GRAD   = "linear-gradient(135deg,#3B82F6 0%,#06B6D4 100%)"
    INPUT_BG   = "#1E293B"
    SIDEBAR_BG = "#0D1526"
    TAB_BG     = "#1E293B"
    METRIC_BG  = "rgba(30,41,59,0.72)"
    LAND_GRAD  = "radial-gradient(ellipse at 50% 40%, #0F2040 0%, #0B1120 60%, #050A14 100%)"
    GLOW_DOT   = "rgba(96,165,250,0.12)"
else:
    BG         = "#F0F4F8"
    CARD       = "#FFFFFF"
    GLASS      = "rgba(255,255,255,0.92)"
    BORDER     = "#D1DAE6"
    SHADOW     = "rgba(15,23,42,0.10)"
    GLOW       = "rgba(59,130,246,0.14)"
    TXT1       = "#0F172A"
    TXT2       = "#334155"
    TXTM       = "#64748B"
    BLUE       = "#3B82F6"
    CYAN       = "#06B6D4"
    HERO_GRAD  = "linear-gradient(135deg,#DBEAFE 0%,#F0F9FF 50%,#ECFEFF 100%)"
    BTN_GRAD   = "linear-gradient(135deg,#3B82F6 0%,#06B6D4 100%)"
    INPUT_BG   = "#FFFFFF"
    SIDEBAR_BG = "#FFFFFF"
    TAB_BG     = "#E8EEF5"
    METRIC_BG  = "rgba(255,255,255,0.85)"
    LAND_GRAD  = "radial-gradient(ellipse at 50% 40%, #E0F2FE 0%, #F0F4F8 60%, #E8EEF5 100%)"
    GLOW_DOT   = "rgba(59,130,246,0.08)"

# ─────────────────────────────────────────────────────────────────────────────
# 6. GLOBAL CSS (always injected — hides toolbar, sets base colors)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Hide Streamlit chrome ──────────────────────── */
#MainMenu,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
div[data-testid="stToolbarActions"] {{
    display: none !important;
    height: 0 !important;
}}

/* ── Base fonts ─────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* ── App shell ──────────────────────────────────── */
body,
.stApp,
.stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .main > div {{
    background-color: {BG} !important;
    color: {TXT1} !important;
}}
.block-container {{
    background-color: transparent !important;
    padding-top: 1rem !important;
}}

/* ── All text ───────────────────────────────────── */
p, span, li, label, h1, h2, h3, h4, h5, h6,
div[data-testid="stMarkdownContainer"],
div[data-testid="stMarkdownContainer"] *,
.stMarkdown, .stMarkdown * {{
    color: {TXT1} !important;
}}

/* ── Inputs ─────────────────────────────────────── */
div.stTextInput > div > div,
div.stTextInput > div > div > input {{
    background-color: {INPUT_BG} !important;
    color: {TXT1} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px {SHADOW} !important;
}}
div.stTextInput > div > div > input::placeholder {{ color: {TXTM} !important; }}
div.stTextInput > div > div > input:focus {{
    border-color: {BLUE} !important;
    box-shadow: 0 0 0 3px {GLOW} !important;
}}

/* ── Buttons ─────────────────────────────────────── */
div.stButton > button {{
    background: {BTN_GRAD} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px {GLOW} !important;
    transition: all 0.22s ease !important;
}}
div.stButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-2px) !important;
}}
div.stButton > button * {{ color: #fff !important; }}
div.stDownloadButton > button {{
    background: {BTN_GRAD} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}}

/* ── Radio ──────────────────────────────────────── */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] span,
div[data-testid="stRadio"] p {{ color: {TXT1} !important; }}

/* ── Tabs ───────────────────────────────────────── */
div[data-baseweb="tab-list"] {{
    background-color: {TAB_BG} !important;
    border-radius: 14px !important;
    padding: 4px !important;
    border: 1px solid {BORDER} !important;
}}
button[data-baseweb="tab"] {{ background-color: transparent !important; border-radius: 10px !important; }}
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {{ color: {TXTM} !important; font-weight: 600 !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ background-color: {BLUE} !important; }}
button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {{ color: #fff !important; }}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div {{
    background-color: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER} !important;
}}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {{
    color: {TXT1} !important;
}}
section[data-testid="stSidebar"] hr {{ border-color: {BORDER} !important; }}

/* ── Misc ───────────────────────────────────────── */
hr, [data-testid="stDivider"] {{
    border-color: {BORDER} !important;
    border-top: 1px solid {BORDER} !important;
}}
[data-testid="column"] {{ background-color: transparent !important; }}
* {{ scrollbar-color: {BLUE} transparent; scrollbar-width: thin; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-thumb {{ background: {BLUE}; border-radius: 99px; }}

/* ── Custom cards ────────────────────────────────── */
.sub-metric-card {{
    background: {METRIC_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 20px !important;
    padding: 18px 14px !important;
    text-align: center !important;
    box-shadow: 0 4px 20px {SHADOW} !important;
    transition: all 0.25s ease !important;
}}
.sub-metric-card:hover {{
    transform: translateY(-3px) !important;
    border-color: {BLUE} !important;
    box-shadow: 0 10px 24px {GLOW} !important;
}}
.sub-metric-value {{
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: {TXT1} !important;
    margin: 4px 0 !important;
}}
.sub-metric-label {{
    font-size: 0.76rem !important;
    color: {TXTM} !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
}}
.glass-card {{
    background: {GLASS} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 24px !important;
    padding: 24px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 10px 30px {SHADOW} !important;
    transition: all 0.3s ease !important;
}}
.glass-card:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 20px 40px {GLOW} !important;
    border-color: {BLUE} !important;
}}
.hourly-scroll-container {{
    display: flex; gap: 14px; overflow-x: auto;
    padding: 8px 4px 16px 4px; scrollbar-width: thin;
    scrollbar-color: {BLUE} transparent !important;
}}
.hourly-card {{
    min-width: 110px; border-radius: 20px;
    padding: 16px 12px; text-align: center; flex-shrink: 0;
    transition: all 0.25s cubic-bezier(0.16,1,0.3,1); cursor: pointer;
    background: {GLASS} !important;
    border: 1px solid {BORDER} !important;
    box-shadow: 0 4px 16px {SHADOW} !important;
}}
.hourly-card:hover {{
    border-color: {BLUE} !important;
    transform: translateY(-4px) scale(1.03) !important;
    box-shadow: 0 10px 24px {GLOW} !important;
}}
.day-card {{
    display: flex; align-items: center; justify-content: space-between;
    border-radius: 20px; padding: 18px 24px; margin-bottom: 12px;
    transition: all 0.25s ease;
    background: {GLASS} !important;
    border: 1px solid {BORDER} !important;
    box-shadow: 0 4px 16px {SHADOW} !important;
}}
.day-card:hover {{
    border-color: {BLUE} !important;
    transform: translateX(4px) !important;
    box-shadow: 0 8px 24px {GLOW} !important;
}}
.suggestion-pill button {{
    background: {GLASS} !important;
    color: {TXT1} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 999px !important;
    padding: 5px 14px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: all 0.18s ease !important;
}}
.suggestion-pill button:hover {{
    background: {BLUE} !important;
    color: #fff !important;
    border-color: {BLUE} !important;
    transform: translateY(-1px) !important;
}}

/* ── Results slide-in animation ──────────────────── */
@keyframes slideUpFade {{
    from {{ opacity: 0; transform: translateY(32px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.results-container {{
    animation: slideUpFade 0.4s ease forwards;
}}

/* ── Landing search input override ───────────────── */
.land-input div.stTextInput > div > div > input {{
    font-size: 1.1rem !important;
    padding: 14px 22px !important;
    border-radius: 18px !important;
    border: 1.5px solid {BORDER} !important;
    background: {INPUT_BG} !important;
    color: {TXT1} !important;
    box-shadow: 0 4px 24px {SHADOW} !important;
    text-align: left !important;
}}
.land-input div.stTextInput > div > div > input:focus {{
    border-color: {BLUE} !important;
    box-shadow: 0 0 0 3px {GLOW}, 0 4px 24px {SHADOW} !important;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 7. CITY SUGGESTIONS LIST
# ─────────────────────────────────────────────────────────────────────────────
CITY_SUGGESTIONS = [
    # ── Indian States (searchable by state name) ───────────────────────────
    "Kerala", "Karnataka", "Tamil Nadu", "Andhra Pradesh", "Telangana",
    "Maharashtra", "Goa", "Gujarat", "Rajasthan", "Madhya Pradesh",
    "Uttar Pradesh", "Bihar", "West Bengal", "Odisha", "Jharkhand",
    "Assam", "Meghalaya", "Manipur", "Mizoram", "Nagaland",
    "Arunachal Pradesh", "Tripura", "Sikkim", "Uttarakhand", "Himachal Pradesh",
    "Punjab", "Haryana", "Delhi", "Jammu", "Ladakh", "Chhattisgarh",

    # ── Kerala Cities & Districts ──────────────────────────────────────────
    "Kottayam", "Kochi", "Kozhikode", "Kollam", "Kannur",
    "Kasaragod", "Kasaragod District",
    "Thiruvananthapuram", "Thrissur", "Alappuzha", "Palakkad", "Malappuram",
    "Pathanamthitta", "Idukki", "Ernakulam", "Wayanad",
    "Kayamkulam", "Kalpetta", "Karunagappally", "Kothamangalam",
    "Kunnamkulam", "Kodungallur", "Kanjirappally", "Kattappana",
    "Manarcadu", "Munnar", "Nedumangad", "Neyyattinkara",
    "Perinthalmanna", "Perumbavoor", "Ponnani", "Thodupuzha",
    "Tirur", "Tiruvalla", "Varkala", "Vatakara",

    # ── Karnataka Cities ───────────────────────────────────────────────────
    "Bangalore", "Bengaluru", "Mysuru", "Mysore", "Mangalore", "Mangaluru",
    "Hubli", "Dharwad", "Belgaum", "Belagavi", "Bellary", "Ballari",
    "Shimoga", "Shivamogga", "Tumkur", "Tumakuru", "Udupi",
    "Bidar", "Kalaburagi", "Gulbarga", "Raichur", "Vijayapura",

    # ── Tamil Nadu Cities ──────────────────────────────────────────────────
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Trichy",
    "Salem", "Tirunelveli", "Vellore", "Erode", "Tirupur",
    "Dindigul", "Thanjavur", "Tanjore", "Kanchipuram", "Pondicherry",
    "Pudukkottai", "Nagercoil", "Cuddalore", "Kumbakonam",

    # ── Andhra Pradesh / Telangana ─────────────────────────────────────────
    "Hyderabad", "Visakhapatnam", "Vizag", "Vijayawada", "Guntur",
    "Nellore", "Kurnool", "Tirupati", "Rajahmundry", "Kakinada",
    "Warangal", "Nizamabad", "Karimnagar",

    # ── Maharashtra ────────────────────────────────────────────────────────
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
    "Solapur", "Amravati", "Kolhapur", "Thane", "Navi Mumbai",
    "Vasai", "Malegaon", "Sangli", "Satara", "Ratnagiri",

    # ── North India ────────────────────────────────────────────────────────
    "New Delhi", "Noida", "Gurugram", "Gurgaon", "Faridabad", "Agra",
    "Lucknow", "Kanpur", "Varanasi", "Allahabad", "Prayagraj",
    "Meerut", "Ghaziabad", "Bareilly", "Aligarh", "Moradabad",
    "Mathura", "Vrindavan",
    "Jaipur", "Jodhpur", "Udaipur", "Ajmer", "Kota",
    "Chandigarh", "Amritsar", "Ludhiana", "Patiala", "Jalandhar",
    "Dehradun", "Haridwar", "Rishikesh", "Shimla", "Manali", "Dharamsala",
    "Srinagar", "Jammu",

    # ── East & Northeast India ─────────────────────────────────────────────
    "Kolkata", "Howrah", "Asansol", "Durgapur", "Siliguri",
    "Patna", "Gaya", "Bhagalpur",
    "Bhubaneswar", "Cuttack", "Rourkela",
    "Guwahati", "Dispur", "Shillong", "Imphal", "Agartala",
    "Ranchi", "Jamshedpur", "Dhanbad",

    # ── Central & West India ───────────────────────────────────────────────
    "Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain",
    "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar",
    "Raipur", "Bhilai",

    # ── South India (Other) ────────────────────────────────────────────────
    "Puducherry", "Madurai",

    # ── Asia ──────────────────────────────────────────────────────────────
    "Tokyo", "Osaka", "Kyoto", "Nagoya",
    "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Xi'an",
    "Seoul", "Busan", "Incheon",
    "Singapore",
    "Bangkok", "Chiang Mai", "Pattaya",
    "Jakarta", "Surabaya", "Bandung",
    "Kuala Lumpur", "Penang", "Johor Bahru",
    "Dhaka", "Chittagong",
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
    "Colombo", "Kathmandu", "Pokhara",
    "Hong Kong", "Macau", "Taipei",
    "Manila", "Cebu",
    "Ho Chi Minh City", "Hanoi", "Da Nang",
    "Yangon", "Phnom Penh", "Vientiane",
    "Kabul", "Tashkent", "Almaty",
    "Tehran", "Mashhad", "Isfahan",
    "Baghdad", "Basra", "Mosul",

    # ── Middle East ────────────────────────────────────────────────────────
    "Dubai", "Abu Dhabi", "Sharjah", "Ajman",
    "Riyadh", "Jeddah", "Mecca", "Medina", "Dammam",
    "Doha", "Kuwait City", "Manama", "Muscat", "Salalah",
    "Amman", "Beirut", "Damascus", "Jerusalem", "Tel Aviv",

    # ── Europe ────────────────────────────────────────────────────────────
    "London", "Manchester", "Birmingham", "Liverpool", "Leeds",
    "Glasgow", "Edinburgh",
    "Paris", "Lyon", "Marseille", "Toulouse", "Nice",
    "Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart",
    "Madrid", "Barcelona", "Seville", "Valencia", "Bilbao",
    "Rome", "Milan", "Naples", "Turin", "Florence", "Venice",
    "Amsterdam", "Rotterdam", "The Hague",
    "Brussels", "Antwerp", "Ghent",
    "Vienna", "Graz", "Salzburg",
    "Prague", "Brno",
    "Warsaw", "Krakow", "Lodz", "Wroclaw",
    "Stockholm", "Gothenburg", "Malmo",
    "Oslo", "Bergen",
    "Copenhagen", "Aarhus",
    "Helsinki", "Tampere", "Turku",
    "Zurich", "Geneva", "Basel", "Bern",
    "Lisbon", "Porto",
    "Athens", "Thessaloniki",
    "Budapest", "Debrecen",
    "Bucharest", "Cluj-Napoca",
    "Istanbul", "Ankara", "Izmir", "Antalya",
    "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg",
    "Kyiv", "Kharkiv", "Odesa",
    "Minsk", "Dublin", "Cork",
    "Reykjavik", "Riga", "Tallinn", "Vilnius",
    "Sofia", "Zagreb", "Belgrade", "Sarajevo", "Tirana", "Skopje",
    "Ljubljana", "Bratislava", "Chisinau",

    # ── Americas ──────────────────────────────────────────────────────────
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Seattle", "Denver", "Boston", "Nashville", "Detroit",
    "Las Vegas", "Memphis", "Portland", "Baltimore", "Miami",
    "Atlanta", "Minneapolis", "New Orleans", "Cleveland",
    "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa",
    "Mexico City", "Guadalajara", "Monterrey", "Tijuana",
    "Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza",
    "Buenos Aires", "Cordoba", "Rosario",
    "Lima", "Bogota", "Medellin", "Cali",
    "Santiago", "Valparaiso",
    "Caracas", "Quito", "La Paz", "Asuncion", "Montevideo",
    "Havana", "Santo Domingo", "San Juan",
    "Panama City", "San Jose Costa Rica", "Guatemala City",

    # ── Africa ────────────────────────────────────────────────────────────
    "Cairo", "Alexandria", "Giza",
    "Lagos", "Abuja", "Kano", "Ibadan",
    "Nairobi", "Mombasa",
    "Johannesburg", "Cape Town", "Durban", "Pretoria",
    "Casablanca", "Rabat", "Marrakech", "Fez",
    "Accra", "Kumasi",
    "Addis Ababa", "Dar es Salaam", "Kampala", "Kigali",
    "Dakar", "Kinshasa", "Luanda", "Lusaka", "Harare",
    "Tunis", "Algiers",

    # ── Oceania ───────────────────────────────────────────────────────────
    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
    "Canberra", "Gold Coast", "Newcastle", "Hobart",
    "Auckland", "Wellington", "Christchurch",
    "Suva", "Port Moresby",
]

# ─────────────────────────────────────────────────────────────────────────────
# 8.  GEOLOCATION BUTTON  (srcdoc iframe via components.v1.html)
# Uses postMessage to communicate coords to parent — works on Streamlit Cloud
# where cross-origin iframe access to window.top.location is blocked.
# ─────────────────────────────────────────────────────────────────────────────
_GEO_HTML = f"""
<!DOCTYPE html><html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    height:100%; width:100%;
    background:transparent;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:5px;
}}
button {{
    display:flex; align-items:center; justify-content:center; gap:8px;
    background:transparent; color:{TXT2};
    border:1.5px solid {BORDER}; border-radius:12px;
    padding:10px 18px; font-size:0.88rem; font-weight:600;
    cursor:pointer; font-family:system-ui,sans-serif;
    transition:all 0.2s; white-space:nowrap; width:100%;
}}
button:hover {{ border-color:{BLUE}; color:{BLUE}; background:{GLOW}; }}
button:disabled {{ opacity:0.65; cursor:not-allowed; }}
#s {{ font-size:0.7rem; color:{TXTM}; font-family:system-ui,sans-serif;
      text-align:center; min-height:13px; padding:0 4px; }}
</style></head>
<body>
<button id="b" onclick="go()">📍 Use My Location</button>
<div id="s"></div>
<script>
var done = false;
var btn, status;

function ready(fn) {{
  if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn);
}}

ready(function() {{
  btn = document.getElementById('b');
  status = document.getElementById('s');
}});

// Send coords to parent via postMessage (works even in sandboxed iframes)
function navigate(lat, lon) {{
  if (done) return;
  done = true;
  status.innerText = 'Found! Loading…';
  var payload = {{ type: 'SKYPULSE_GEO', lat: lat, lon: lon }};
  // Try all parent references to ensure delivery
  try {{ window.parent.postMessage(payload, '*'); }} catch(e) {{}}
  try {{ window.top.postMessage(payload, '*'); }} catch(e) {{}}
}}

function fail(msg) {{
  if (done) return;
  done = true;
  btn.disabled = false;
  btn.innerHTML = '📍 Use My Location';
  status.innerText = msg || 'Could not detect location.';
}}

function tryIP1() {{
  fetch('https://ipwho.is/')
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (!done && d && d.success !== false && d.latitude && d.longitude) {{
        navigate(parseFloat(d.latitude).toFixed(6), parseFloat(d.longitude).toFixed(6));
      }} else if (!done) {{
        tryIP2();
      }}
    }})
    .catch(tryIP2);
}}

function tryIP2() {{
  fetch('https://ip-api.com/json/?fields=status,lat,lon')
    .then(function(r) {{ return r.json(); }})
    .then(function(d) {{
      if (!done && d && d.status === 'success' && d.lat && d.lon) {{
        navigate(parseFloat(d.lat).toFixed(6), parseFloat(d.lon).toFixed(6));
      }} else if (!done) {{
        fail('Location not detected. Try searching your city.');
      }}
    }})
    .catch(function() {{
      if (!done) fail('Location not detected. Try searching your city.');
    }});
}}

function go() {{
  btn.disabled = true;
  btn.innerHTML = '⏳ Detecting…';
  status.innerText = 'Getting your location…';
  done = false;

  // GPS via navigator.geolocation (browser will ask permission)
  if (navigator.geolocation) {{
    navigator.geolocation.getCurrentPosition(
      function(pos) {{
        navigate(pos.coords.latitude.toFixed(6), pos.coords.longitude.toFixed(6));
      }},
      function(err) {{
        // GPS denied or unavailable — IP fallback already running
      }},
      {{ enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }}
    );
  }}

  // IP-based fallback runs in parallel
  tryIP1();

  // Safety net: give up after 15s
  setTimeout(function() {{ if (!done) fail('Timed out. Please search manually.'); }}, 15000);
}}
</script></body></html>
"""

# Parent-side postMessage listener injected into Streamlit page.
# Receives {{ type: 'SKYPULSE_GEO', lat, lon }} from the iframe and
# navigates the top-level window to ?lat=...&lon=... to trigger st.query_params.
_GEO_LISTENER_JS = """
<script>
(function() {{
  if (window.__skypulseGeoListenerActive) return;
  window.__skypulseGeoListenerActive = true;
  window.addEventListener('message', function(event) {{
    if (!event.data || event.data.type !== 'SKYPULSE_GEO') return;
    var lat = event.data.lat;
    var lon = event.data.lon;
    if (lat && lon) {{
      var url = window.location.pathname + '?lat=' + lat + '&lon=' + lon;
      window.location.href = url;
    }}
  }}, false);
}})();
</script>
"""


def _smart_suggestions(query: str, limit: int = 10) -> list:
    """Return suggestions: startsWith matches first, then contains matches."""
    q = query.strip().lower()
    if not q:
        return []
    starts   = [c for c in CITY_SUGGESTIONS if c.lower().startswith(q)]
    contains = [c for c in CITY_SUGGESTIONS if q in c.lower() and not c.lower().startswith(q)]
    return (starts + contains)[:limit]




# ─────────────────────────────────────────────────────────────────────────────
# 9. LANDING PAGE  (shown when has_searched == False)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.has_searched:

    # ── Landing-specific CSS: hide sidebar, full-height bg, no padding ──
    st.markdown(f"""
    <style>
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    body, .stApp {{
        background: transparent !important;
    }}
    .block-container {{
        max-width: 680px !important;
        padding-top: 0 !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 2;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Stunning canvas-based weather animation ──
    _dark = is_dark
    _bg0 = "#060c18" if _dark else "#0e4fa3"
    _bg1 = "#0a1628" if _dark else "#1a6abf"
    _bg2 = "#0d1f3c" if _dark else "#2d8dd4"

    st.markdown(f"""
    <style>
    body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    .main, .main > div, .block-container {{
        background: transparent !important;
    }}
    #sp-master-canvas {{
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        z-index: 0;
        pointer-events: none;
        display: block;
    }}
    </style>
    <canvas id="sp-master-canvas"></canvas>
    <script>
    (function() {{
      var C = document.getElementById('sp-master-canvas');
      if (!C || C._spDone) return;
      C._spDone = true;
      var X = C.getContext('2d');
      var W, H, t = 0;

      function resize() {{ W = C.width = window.innerWidth; H = C.height = window.innerHeight; }}
      resize();
      window.addEventListener('resize', resize);

      var DARK = {'true' if _dark else 'false'};

      /* ── Mesh gradient orbs ── */
      var orbs = [
        {{ x:0.15, y:0.20, r:0.55, c:[37,99,235],   vx:0.00025, vy:0.00018 }},
        {{ x:0.82, y:0.65, r:0.48, c:[6,182,212],   vx:-0.00018,vy:0.00025 }},
        {{ x:0.50, y:0.88, r:0.40, c:[124,58,237],  vx:0.00010, vy:-0.00030}},
        {{ x:0.08, y:0.75, r:0.35, c:[16,185,129],  vx:0.00030, vy:0.00012 }},
        {{ x:0.70, y:0.10, r:0.30, c:[239,68,68],   vx:-0.00020,vy:0.00022 }},
      ];

      /* ── Neon rain ── */
      var RCOUNT = DARK ? 160 : 120;
      var rain = [];
      for (var i = 0; i < RCOUNT; i++) rain.push(newDrop(true));
      function newDrop(rand) {{
        return {{
          x: Math.random() * 1.2 - 0.1,
          y: rand ? Math.random() : -0.05,
          len: 0.025 + Math.random() * 0.055,
          spd: 0.004 + Math.random() * 0.009,
          op:  0.15 + Math.random() * 0.65,
          w:   0.6  + Math.random() * 1.4,
          glow:Math.random() < 0.25,
        }};
      }}

      /* ── Fractal lightning ── */
      var bolt = null, bFlash = 0, bTimer = 0, bInterval = 220 + Math.random()*300;
      function makeBolt(x1,y1,x2,y2,d) {{
        if (d===0) return [[x1,y1,x2,y2]];
        var mx=(x1+x2)/2+(Math.random()-0.5)*0.14, my=(y1+y2)/2+(Math.random()-0.5)*0.04;
        var s=[].concat(makeBolt(x1,y1,mx,my,d-1)).concat(makeBolt(mx,my,x2,y2,d-1));
        if (d>1 && Math.random()<0.45) {{
          var bx=mx+(Math.random()-0.3)*0.18, by=my+Math.random()*0.18;
          s=s.concat(makeBolt(mx,my,bx,by,d-2));
        }}
        return s;
      }}

      /* ── Cloud silhouettes ── */
      var clouds = [];
      for (var i=0;i<5;i++) clouds.push(newCloud(true));
      function newCloud(rand) {{
        return {{
          x: rand ? Math.random()*1.8-0.4 : -0.45,
          y: 0.04 + Math.random()*0.38,
          spd: 0.000055 + Math.random()*0.00012,
          sc:  0.9 + Math.random()*1.6,
          op:  DARK ? 0.035+Math.random()*0.07 : 0.55+Math.random()*0.30,
        }};
      }}
      function drawCloud(cx,cy,sc,op) {{
        var bx=cx*W, by=cy*H, s=sc*140;
        X.save();
        X.globalAlpha = op;
        X.fillStyle   = DARK ? 'rgba(160,200,255,1)' : 'rgba(255,255,255,1)';
        X.shadowColor = DARK ? 'rgba(96,165,250,0.6)' : 'rgba(200,230,255,0.9)';
        X.shadowBlur  = DARK ? 22 : 35;
        X.beginPath();
        X.arc(bx,           by,       s*0.48, 0, Math.PI*2);
        X.arc(bx+s*0.42,   by-s*0.12, s*0.38, 0, Math.PI*2);
        X.arc(bx-s*0.30,   by+s*0.05, s*0.32, 0, Math.PI*2);
        X.arc(bx+s*0.75,   by+s*0.08, s*0.30, 0, Math.PI*2);
        X.arc(bx-s*0.05,   by+s*0.15, s*0.28, 0, Math.PI*2);
        X.fill();
        X.restore();
      }}

      /* ── Glowing particles ── */
      var pts = [];
      for (var i=0;i<55;i++) pts.push(newPt());
      function newPt() {{
        var cols = DARK
          ? [[96,165,250],[34,211,238],[167,139,250],[52,211,153]]
          : [[255,255,255],[186,230,253],[224,242,254],[147,197,253]];
        var c = cols[Math.floor(Math.random()*cols.length)];
        return {{
          x: Math.random(), y: Math.random(),
          r: 0.8+Math.random()*2.2,
          vx:(Math.random()-0.5)*0.00025,
          vy:(Math.random()-0.5)*0.00025,
          op:0.25+Math.random()*0.65,
          ph:Math.random()*Math.PI*2,
          spd:0.012+Math.random()*0.025,
          c: c,
        }};
      }}

      /* ── Shooting stars ── */
      var shoots = [], shootTimer = 0, shootInterval = 140+Math.random()*200;
      function newShoot() {{
        return {{
          x: Math.random()*0.7, y: Math.random()*0.4,
          vx: 0.008+Math.random()*0.012,
          vy: 0.003+Math.random()*0.006,
          life: 1, decay: 0.03+Math.random()*0.04,
          len: 0.08+Math.random()*0.10,
        }};
      }}

      /* ═══ MAIN DRAW LOOP ═══ */
      function draw() {{
        t++;
        X.clearRect(0,0,W,H);

        /* — Gradient background — */
        var bg = X.createLinearGradient(0,0,W,H);
        bg.addColorStop(0, '{_bg0}');
        bg.addColorStop(0.5, '{_bg1}');
        bg.addColorStop(1, '{_bg2}');
        X.fillStyle = bg;
        X.fillRect(0,0,W,H);

        /* — Mesh gradient orbs — */
        orbs.forEach(function(o) {{
          o.x += o.vx + Math.sin(t*0.008+o.y*3)*0.00008;
          o.y += o.vy + Math.cos(t*0.010+o.x*3)*0.00006;
          if(o.x<-0.1||o.x>1.1) o.vx*=-1;
          if(o.y<-0.1||o.y>1.1) o.vy*=-1;
          var pulse = 1 + Math.sin(t*0.018+o.x*4)*0.12;
          var g = X.createRadialGradient(o.x*W,o.y*H,0, o.x*W,o.y*H, o.r*Math.min(W,H)*pulse);
          g.addColorStop(0,'rgba('+o.c[0]+','+o.c[1]+','+o.c[2]+','+(DARK?0.52:0.38)+')');
          g.addColorStop(0.5,'rgba('+o.c[0]+','+o.c[1]+','+o.c[2]+','+(DARK?0.18:0.10)+')');
          g.addColorStop(1,'rgba('+o.c[0]+','+o.c[1]+','+o.c[2]+',0)');
          X.fillStyle = g;
          X.fillRect(0,0,W,H);
        }});

        /* — Cloud silhouettes — */
        clouds.forEach(function(c,i) {{
          c.x += c.spd;
          if(c.x>1.5) {{ clouds[i]=newCloud(false); }}
          drawCloud(c.x, c.y, c.sc, c.op*(0.7+0.3*Math.sin(t*0.005+i)));
        }});

        /* — Neon rain — */
        rain.forEach(function(d,i) {{
          d.y += d.spd;
          d.x -= d.spd*0.22;
          if(d.y>1.05) {{ rain[i]=newDrop(false); return; }}
          X.save();
          if(d.glow) {{ X.shadowColor='rgba(96,165,250,0.9)'; X.shadowBlur=8; }}
          var rc = DARK ? '147,197,253' : '255,255,255';
          var grad = X.createLinearGradient(d.x*W, d.y*H, d.x*W - d.len*W*0.22, (d.y+d.len)*H);
          grad.addColorStop(0,'rgba('+rc+',0)');
          grad.addColorStop(1,'rgba('+rc+','+d.op+')');
          X.strokeStyle = grad;
          X.lineWidth   = d.w;
          X.lineCap     = 'round';
          X.beginPath();
          X.moveTo(d.x*W, d.y*H);
          X.lineTo(d.x*W - d.len*W*0.22, (d.y+d.len)*H);
          X.stroke();
          X.restore();
        }});

        /* — Shooting stars — */
        shootTimer++;
        if(shootTimer>shootInterval) {{
          shoots.push(newShoot());
          shootTimer=0;
          shootInterval=140+Math.random()*200;
        }}
        shoots = shoots.filter(function(s) {{
          X.save();
          X.globalAlpha = s.life*0.9;
          X.strokeStyle = DARK?'rgba(255,255,255,1)':'rgba(255,255,255,0.95)';
          X.shadowColor = 'rgba(200,230,255,1)';
          X.shadowBlur  = 12;
          X.lineWidth   = 1.5;
          X.beginPath();
          X.moveTo(s.x*W, s.y*H);
          X.lineTo((s.x-s.len)*W, (s.y-s.len*0.4)*H);
          X.stroke();
          X.restore();
          s.x+=s.vx; s.y+=s.vy; s.life-=s.decay;
          return s.life>0;
        }});

        /* — Lightning — */
        bTimer++;
        if(bTimer>bInterval) {{
          var lx=0.2+Math.random()*0.6;
          bolt=makeBolt(lx,0,lx+(Math.random()-0.5)*0.25,0.65,6);
          bFlash=14; bTimer=0; bInterval=200+Math.random()*420;
        }}
        if(bolt&&bFlash>0) {{
          X.fillStyle='rgba(180,220,255,'+(bFlash/14*0.18)+')';
          X.fillRect(0,0,W,H);
          var alpha=bFlash/14;
          bolt.forEach(function(seg) {{
            X.save();
            X.strokeStyle='rgba(255,255,255,'+alpha+')';
            X.lineWidth  = bFlash>8?2.5:1.2;
            X.shadowColor='rgba(147,197,253,1)';
            X.shadowBlur = bFlash>8?30:14;
            X.lineCap='round';
            X.beginPath();
            X.moveTo(seg[0]*W,seg[1]*H);
            X.lineTo(seg[2]*W,seg[3]*H);
            X.stroke();
            X.restore();
          }});
          bFlash-=1.8;
          if(bFlash<=0) bolt=null;
        }}

        /* — Glowing particles — */
        pts.forEach(function(p) {{
          p.x+=p.vx+Math.sin(t*0.007+p.ph)*0.00012;
          p.y+=p.vy+Math.cos(t*0.009+p.ph)*0.00010;
          if(p.x<0||p.x>1) p.vx*=-1;
          if(p.y<0||p.y>1) p.vy*=-1;
          p.ph+=p.spd;
          var pop=p.op*(0.45+0.55*Math.sin(p.ph));
          X.save();
          X.fillStyle  ='rgba('+p.c[0]+','+p.c[1]+','+p.c[2]+','+pop+')';
          X.shadowColor='rgba('+p.c[0]+','+p.c[1]+','+p.c[2]+',0.9)';
          X.shadowBlur = 10;
          X.beginPath();
          X.arc(p.x*W,p.y*H,p.r,0,Math.PI*2);
          X.fill();
          X.restore();
        }});

        requestAnimationFrame(draw);
      }}
      draw();
    }})();
    </script>
    """, unsafe_allow_html=True)


    # ── Top spacer (~25% viewport height) ──
    st.markdown("<div style='height:18vh;'></div>", unsafe_allow_html=True)


    # ── Logo + branding (pure HTML, no animations) ──
    st.markdown(textwrap.dedent(f"""
    <div style="text-align:center;margin-bottom:36px;">
      <div style="font-size:4.5rem;line-height:1;margin-bottom:12px;">🌤️</div>
      <div style="margin-bottom:10px;">
        <span style="
          font-size:2.9rem;
          font-weight:800;
          display:inline-block;
          background:linear-gradient(135deg,{BLUE},{CYAN});
          -webkit-background-clip:text;
          background-clip:text;
          -webkit-text-fill-color:transparent;
          color:transparent;
          letter-spacing:-0.5px;
          line-height:1.1;
        ">SkyPulse</span>
      </div>
      <div style="font-size:1rem;color:{TXTM};font-weight:500;margin-top:4px;">
        Premium Weather Intelligence &mdash; powered by OpenWeather
      </div>
    </div>
    """), unsafe_allow_html=True)

    # ── Search input ──
    st.markdown('<div class="land-input">', unsafe_allow_html=True)
    land_input = st.text_input(
        "Search",
        value="",
        placeholder="🔍  Search any city in the world...",
        label_visibility="collapsed",
        key="landing_search_input",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Search button ──
    search_go = st.button("🔍 Search Weather", use_container_width=True, key="land_search_btn")

    # Handle search submission
    if search_go and land_input.strip():
        st.session_state.selected_city    = land_input.strip()
        st.session_state.search_box_value = land_input.strip()
        st.session_state.has_searched     = True
        if land_input.strip() not in st.session_state.recent_searches:
            st.session_state.recent_searches.append(land_input.strip())
        st.rerun()

    # ── Live suggestions while typing ──
    typed_land = land_input.strip()
    if typed_land:
        matches_land = _smart_suggestions(typed_land, 10)
        if matches_land:
            st.markdown(
                f"<div style='font-size:0.78rem;color:{TXTM};font-weight:600;"
                f"margin:12px 0 6px;'>💡 Suggestions — click to select</div>",
                unsafe_allow_html=True,
            )
            pill_cols = st.columns(min(len(matches_land), 5))
            for idx, match in enumerate(matches_land):
                with pill_cols[idx % 5]:
                    st.markdown('<div class="suggestion-pill">', unsafe_allow_html=True)
                    if st.button(f"📍 {match}", key=f"lsugg_{idx}", use_container_width=True):
                        st.session_state.selected_city    = match
                        st.session_state.search_box_value = match
                        st.session_state.has_searched     = True
                        if match not in st.session_state.recent_searches:
                            st.session_state.recent_searches.append(match)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        # ── Popular cities when nothing typed ──
        st.markdown(
            f"<div style='font-size:0.78rem;color:{TXTM};font-weight:500;margin:18px 0 8px;'>"
            "🌍 Popular cities</div>",
            unsafe_allow_html=True,
        )
        popular = ["Kottayam", "Mumbai", "Tokyo", "London", "New York", "Dubai", "Paris", "Sydney"]
        pop_cols = st.columns(4)
        for i, name in enumerate(popular):
            with pop_cols[i % 4]:
                st.markdown('<div class="suggestion-pill">', unsafe_allow_html=True)
                if st.button(name, key=f"pop_{name}", use_container_width=True):
                    st.session_state.selected_city    = name
                    st.session_state.search_box_value = name
                    st.session_state.has_searched     = True
                    if name not in st.session_state.recent_searches:
                        st.session_state.recent_searches.append(name)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 10. RESULTS PAGE — sidebar + dashboard
# ─────────────────────────────────────────────────────────────────────────────

# Sidebar
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;margin-bottom:4px;'>"
        "<span style='font-size:1.5rem;'>🌤️</span>"
        "<h2 style='margin:4px 0 0;font-weight:800;font-size:1.7rem;"
        "display:inline-block;"
        "background:linear-gradient(135deg,#3B82F6,#06B6D4);"
        "-webkit-background-clip:text;background-clip:text;"
        "-webkit-text-fill-color:transparent;color:transparent;'>"
        "SkyPulse</h2></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;font-size:0.85rem;font-weight:500;margin-bottom:20px;'>"
        "Commercial SaaS Weather Platform</p>",
        unsafe_allow_html=True,
    )

    # ── Back to home ──
    if st.button("🏠 Back to Home", use_container_width=True, key="back_home"):
        st.session_state.has_searched     = False
        st.session_state.selected_city    = ""
        st.session_state.search_box_value = ""
        st.rerun()

    st.divider()
    st.subheader("🎨 Appearance")
    theme_mode = st.radio(
        "Theme",
        options=["dark", "light"],
        format_func=lambda x: "🌙 Dark Mode" if x == "dark" else "☀️ Light Mode",
        index=0 if st.session_state.theme_mode == "dark" else 1,
        horizontal=True,
        key="theme_radio",
    )
    if theme_mode != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_mode
        st.rerun()

    st.divider()
    st.subheader("⚙️ Units")
    unit_system = st.radio(
        "Temperature",
        options=["metric", "imperial"],
        format_func=lambda x: "°C / m/s" if x == "metric" else "°F / mph",
        index=0 if st.session_state.unit_system == "metric" else 1,
        horizontal=True,
        key="unit_radio",
    )
    st.session_state.unit_system = unit_system
    units = get_unit_symbols(unit_system)

    st.divider()
    st.subheader("🌍 Popular Cities")
    qcols = st.columns(2)
    for idx, name in enumerate(["Kottayam", "Kochi", "Tokyo", "London", "New York", "Paris"]):
        if qcols[idx % 2].button(name, key=f"qc_{name}", use_container_width=True):
            st.session_state.selected_city    = name
            st.session_state.search_box_value = name
            st.rerun()

    st.divider()
    if st.session_state.recent_searches:
        st.subheader("🕒 Recent")
        for prev in reversed(st.session_state.recent_searches[-5:]):
            if st.button(f"📍 {prev}", key=f"rec_{prev}", use_container_width=True):
                st.session_state.selected_city    = prev
                st.session_state.search_box_value = prev
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 11. RESULTS — search bar + weather data
# ─────────────────────────────────────────────────────────────────────────────
units = get_unit_symbols(st.session_state.unit_system)

# Open results container (gets the slide-up animation)
st.markdown('<div class="results-container">', unsafe_allow_html=True)

# ── Search bar ─────────────────────────────────────────────────────────────
hcol1, hcol2 = st.columns([3, 0.9])
with hcol1:
    search_input = st.text_input(
        "Search City",
        value=st.session_state.search_box_value or st.session_state.selected_city,
        placeholder="Search another city...",
        label_visibility="collapsed",
        key="results_search_input",
    )
    st.session_state.search_box_value = search_input

with hcol2:
    search_btn = st.button("🔍 Search", use_container_width=True, key="results_search_btn")



if search_btn and search_input.strip():
    st.session_state.selected_city    = search_input.strip()
    st.session_state.search_box_value = search_input.strip()
    if search_input.strip() not in st.session_state.recent_searches:
        st.session_state.recent_searches.append(search_input.strip())
    st.rerun()

# Live suggestions on results page
typed = search_input.strip()
if typed and typed.lower() != st.session_state.selected_city.lower():
    matches = _smart_suggestions(typed, 8)
    if matches:
        st.markdown(
            f"<div style='font-size:0.78rem;color:{TXTM};font-weight:600;margin-bottom:4px;margin-top:6px;'>"
            "💡 Suggestions — click to select</div>",
            unsafe_allow_html=True,
        )
        pill_cols = st.columns(min(len(matches), 4))
        for idx, match in enumerate(matches):
            with pill_cols[idx % 4]:
                st.markdown('<div class="suggestion-pill">', unsafe_allow_html=True)
                if st.button(f"📍 {match}", key=f"rsugg_{idx}", use_container_width=True):
                    st.session_state.selected_city    = match
                    st.session_state.search_box_value = match
                    if match not in st.session_state.recent_searches:
                        st.session_state.recent_searches.append(match)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

city = st.session_state.selected_city

# ─────────────────────────────────────────────────────────────────────────────
# 12. FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner(f"Fetching weather for {city}..."):
    weather  = get_current_weather(city, units=st.session_state.unit_system)
    forecast = get_forecast(city, units=st.session_state.unit_system)

if not weather:
    st.error(f"❌ Could not retrieve weather for '{city}'. Check the city name and try again.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

aqi_data = None
if weather.get("coord"):
    aqi_data = get_air_quality(weather["coord"]["lat"], weather["coord"]["lon"])

# ─────────────────────────────────────────────────────────────────────────────
# 13. DERIVED VALUES
# ─────────────────────────────────────────────────────────────────────────────
sunrise_time   = format_timestamp(weather["sunrise"], weather["timezone"], "%H:%M")
sunset_time    = format_timestamp(weather["sunset"],  weather["timezone"], "%H:%M")
wind_dir       = deg_to_compass(weather["wind_deg"])
weather_accent = get_weather_color(weather["weather"])

# ─────────────────────────────────────────────────────────────────────────────
# 14. HERO CARD
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(textwrap.dedent(f"""
<div style="background:{HERO_GRAD};border:1px solid {BORDER};border-radius:24px;
  padding:32px 36px;box-shadow:0 16px 48px {SHADOW};overflow:hidden;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:24px;">
    <div>
      <div style="font-size:2.1rem;font-weight:800;color:{TXT1};margin-bottom:2px;">
        📍 {weather['city']}, {weather['country']}
      </div>
      <div style="color:{TXTM};font-size:0.88rem;font-weight:500;margin-bottom:16px;">
        Lat: {weather['coord']['lat']} &nbsp;•&nbsp; Lon: {weather['coord']['lon']}
      </div>
      <div style="font-size:4.5rem;font-weight:800;line-height:1;margin-bottom:14px;color:{TXT1};">
        {weather['temperature']}{units['temp']}
      </div>
      <div style="margin-bottom:14px;">
        <span style="display:inline-block;padding:6px 18px;border-radius:20px;
          background:rgba(59,130,246,0.12);border:1px solid {weather_accent};
          color:{weather_accent};font-weight:700;text-transform:capitalize;font-size:0.95rem;">
          {weather['weather']} &bull; {weather['description']}
        </span>
      </div>
      <div style="color:{TXT2};font-size:1rem;font-weight:500;">
        Feels like <strong style="color:{TXT1};">{weather['feels_like']}{units['temp']}</strong>
        &nbsp;|&nbsp; H: <strong style="color:{TXT1};">{weather['temp_max']}{units['temp']}</strong>
        &nbsp; L: <strong style="color:{TXT1};">{weather['temp_min']}{units['temp']}</strong>
      </div>
    </div>
    <div style="text-align:center;min-width:160px;">
      <img src="https://openweathermap.org/img/wn/{weather['icon']}@4x.png"
        width="170" alt="{weather['weather']}"
        style="filter:drop-shadow(0 8px 24px {GLOW});animation:float 4s ease-in-out infinite;" />
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 15. SUB-METRIC CARDS
# ─────────────────────────────────────────────────────────────────────────────
def metric_card_html(icon_label: str, value: str, sub: str = "") -> str:
    return textwrap.dedent(f"""
    <div class="sub-metric-card">
        <div class="sub-metric-label">{icon_label}</div>
        <div class="sub-metric-value">{value}</div>
        <div style="color:{TXTM};font-size:0.78rem;margin-top:4px;">{sub}</div>
    </div>
    """)

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.markdown(metric_card_html("🌬 Wind",      f"{weather['wind_speed']} {units['speed']}", f"{wind_dir} ({weather['wind_deg']}°)"), unsafe_allow_html=True)
m2.markdown(metric_card_html("💧 Humidity",  f"{weather['humidity']}%",   "Relative Moisture"),  unsafe_allow_html=True)
m3.markdown(metric_card_html("🧭 Pressure",  f"{weather['pressure']}",    units['pressure']),    unsafe_allow_html=True)
m4.markdown(metric_card_html("👀 Visibility", f"{weather['visibility']}", "km"),                 unsafe_allow_html=True)
m5.markdown(metric_card_html("🌅 Sunrise",   sunrise_time,                "Morning"),            unsafe_allow_html=True)
m6.markdown(metric_card_html("🌇 Sunset",    sunset_time,                 "Evening"),            unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 16. TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_hourly, tab_daily, tab_aqi, tab_map, tab_export = st.tabs([
    "📊 Hourly", "📅 5-Day", "🍃 Air Quality", "🗺️ Map", "💾 Export",
])

with tab_hourly:
    if forecast and forecast.get("list"):
        st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>24-Hour Temperature &amp; Rain Trend</h4>", unsafe_allow_html=True)
        st.plotly_chart(create_hourly_chart(forecast["list"], weather["timezone"], units["temp"], is_dark=is_dark), use_container_width=True)
        st.markdown(f"<h4 style='font-weight:700;color:{TXT1};margin-top:10px;'>Hourly Breakdown</h4>", unsafe_allow_html=True)
        cards = []
        for item in forecast["list"][:12]:
            t = format_timestamp(item["dt"], weather["timezone"], "%H:%M")
            cards.append(
                f'<div class="hourly-card">'
                f'<div style="color:{TXTM};font-size:0.83rem;font-weight:600;">{t}</div>'
                f'<img src="https://openweathermap.org/img/wn/{item["icon"]}@2x.png" width="46" style="margin:4px 0;"/>'
                f'<div style="font-weight:700;font-size:1.1rem;color:{TXT1};">{item["temp"]}{units["temp"]}</div>'
                f'<div style="color:{CYAN};font-size:0.8rem;font-weight:600;margin-top:2px;">🌧️ {item["pop"]}%</div>'
                f'</div>'
            )
        st.markdown(f'<div class="hourly-scroll-container">{"".join(cards)}</div>', unsafe_allow_html=True)

with tab_daily:
    if forecast and forecast.get("list"):
        daily = group_forecast_by_day(forecast["list"])
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>Temperature Range</h4>", unsafe_allow_html=True)
            st.plotly_chart(create_daily_chart(daily, units["temp"], is_dark=is_dark), use_container_width=True)
        with c2:
            st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>Daily Overview</h4>", unsafe_allow_html=True)
            for day in daily[:5]:
                st.markdown(textwrap.dedent(f"""
                <div class="day-card">
                  <div style="min-width:80px;">
                    <div style="font-weight:700;color:{TXT1};">{day['day_name']}</div>
                    <div style="color:{TXTM};font-size:0.78rem;">{day['full_date']}</div>
                  </div>
                  <div style="display:flex;align-items:center;gap:8px;">
                    <img src="https://openweathermap.org/img/wn/{day['icon']}@2x.png" width="40"/>
                    <span style="color:{TXT2};font-size:0.88rem;text-transform:capitalize;font-weight:500;">{day['description']}</span>
                  </div>
                  <div style="text-align:right;">
                    <div style="font-weight:700;color:{TXT1};">{day['temp_max']}{units['temp']}</div>
                    <div style="color:{TXTM};font-size:0.83rem;">{day['temp_min']}{units['temp']}</div>
                  </div>
                </div>
                """), unsafe_allow_html=True)

with tab_aqi:
    st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>Air Quality Index &amp; Pollutants</h4>", unsafe_allow_html=True)
    if aqi_data:
        aqi_val  = aqi_data["aqi"]
        aqi_info = get_aqi_info(aqi_val)
        a1, a2   = st.columns([1, 2])
        with a1:
            st.markdown(textwrap.dedent(f"""
            <div class="glass-card" style="text-align:center;padding:28px;">
              <div style="color:{TXTM};font-size:0.8rem;text-transform:uppercase;font-weight:700;margin-bottom:10px;">AQI Rating</div>
              <div style="display:inline-block;padding:12px 24px;border-radius:16px;
                background:{aqi_info['bg']};border:1.5px solid {aqi_info['color']};
                color:{aqi_info['color']};font-size:1.6rem;font-weight:800;">
                {aqi_val} — {aqi_info['label']}
              </div>
              <div style="color:{TXT2};font-size:0.88rem;margin-top:14px;font-weight:500;">{aqi_info['desc']}</div>
            </div>
            """), unsafe_allow_html=True)
        with a2:
            st.markdown(f"<h5 style='color:{TXT1};font-weight:700;'>Pollutant Concentrations (μg/m³)</h5>", unsafe_allow_html=True)
            comp = aqi_data["components"]
            pollutants = [
                ("PM2.5", comp.get("pm2_5", 0), "Fine Particulates"),
                ("PM10",  comp.get("pm10",  0), "Coarse Particulates"),
                ("NO2",   comp.get("no2",   0), "Nitrogen Dioxide"),
                ("O3",    comp.get("o3",    0), "Ozone"),
                ("CO",    comp.get("co",    0), "Carbon Monoxide"),
                ("SO2",   comp.get("so2",   0), "Sulfur Dioxide"),
            ]
            pc = st.columns(3)
            for i, (name, val, label) in enumerate(pollutants):
                pc[i % 3].markdown(textwrap.dedent(f"""
                <div class="sub-metric-card" style="margin-bottom:12px;">
                  <div class="sub-metric-label">{name}</div>
                  <div class="sub-metric-value">{round(val, 1)}</div>
                  <div style="color:{TXTM};font-size:0.73rem;">{label}</div>
                </div>
                """), unsafe_allow_html=True)
    else:
        st.info("Air quality data unavailable for this location.")

with tab_map:
    st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>Location Map — {weather['city']}</h4>", unsafe_allow_html=True)
    lat, lon = weather["coord"]["lat"], weather["coord"]["lon"]
    st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), latitude=lat, longitude=lon, zoom=10)

with tab_export:
    st.markdown(f"<h4 style='font-weight:700;color:{TXT1};'>Export Weather Reports</h4>", unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "📄 Download JSON Report",
            data=generate_json_export(weather, forecast, aqi_data),
            file_name=f"weather_{weather['city'].lower().replace(' ','_')}.json",
            mime="application/json", use_container_width=True, key="dl_json",
        )
    with ec2:
        st.download_button(
            "📊 Download CSV Forecast",
            data=generate_csv_export(forecast),
            file_name=f"forecast_{weather['city'].lower().replace(' ','_')}.csv",
            mime="text/csv", use_container_width=True, key="dl_csv",
        )

# Close results container div
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 17. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"""<hr style="border:none;border-top:1px solid {BORDER};margin:0 0 12px 0;">
<div style="text-align:center;color:{TXTM};font-size:0.82rem;font-weight:500;padding-bottom:20px;">
  SkyPulse SaaS Platform &nbsp;•&nbsp; Apple / Linear / Stripe Design System
  &nbsp;•&nbsp; Powered by OpenWeather API
</div>""",
    unsafe_allow_html=True,
)