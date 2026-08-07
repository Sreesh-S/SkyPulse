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

    # ── Animated weather background — pure CSS (guaranteed to work in Streamlit Cloud) ──
    # st.markdown DOES render <style> and animated HTML; only <script> is blocked.
    import random as _rng
    _rng.seed(7)
    _dark = is_dark

    # Generate rain drops HTML
    _rain_rgb  = "147,197,253" if _dark else "180,220,255"
    _rain_html = ""
    for _i in range(90):
        _l  = round(_rng.uniform(0, 100), 1)
        _ht = round(_rng.uniform(14, 65))
        _dl = round(_rng.uniform(0, 9), 2)
        _dr = round(_rng.uniform(0.5, 2.2), 2)
        _op = round(_rng.uniform(0.2, 0.85), 2)
        _w  = round(_rng.uniform(0.8, 2.0), 1)
        _rain_html += (
            f'<div class="spr" style="left:{_l}%;height:{_ht}px;'
            f'animation-delay:-{_dl}s;animation-duration:{_dr}s;'
            f'opacity:{_op};width:{_w}px"></div>'
        )

    # Generate twinkling stars HTML
    _star_rgb  = "255,255,255" if _dark else "96,165,250"
    _star_html = ""
    for _i in range(65):
        _l  = round(_rng.uniform(0, 100), 1)
        _t  = round(_rng.uniform(0, 100), 1)
        _sz = round(_rng.uniform(1, 3.2), 1)
        _dl = round(_rng.uniform(0, 5), 2)
        _dr = round(_rng.uniform(1.5, 5), 2)
        _star_html += (
            f'<div class="sps" style="left:{_l}%;top:{_t}%;'
            f'width:{_sz}px;height:{_sz}px;'
            f'animation-delay:-{_dl}s;animation-duration:{_dr}s"></div>'
        )

    # Theme colours
    _bg_a  = "#04091a" if _dark else "#1565c0"
    _bg_b  = "#080f22" if _dark else "#1976d2"
    _bg_c  = "#0c1833" if _dark else "#42a5f5"
    _orb1c = "#1a3a8a" if _dark else "#90caf9"
    _orb2c = "#0e7a8a" if _dark else "#ce93d8"
    _orb3c = "#4a1d96" if _dark else "#80deea"
    _cloud = "rgba(180,210,255,0.10)" if _dark else "rgba(255,255,255,0.72)"

    st.markdown(f"""
<style>
/* ── Strip all Streamlit backgrounds ── */
body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="stMainBlockContainer"],.main,.main>div{{background:transparent!important;}}
.block-container{{position:relative;z-index:2!important;}}

/* ── Full-screen weather BG ── */
#sp-bg{{
  position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;
  background:linear-gradient(155deg,{_bg_a} 0%,{_bg_b} 50%,{_bg_c} 100%);
  animation:bgShift 16s ease-in-out infinite alternate;
}}
@keyframes bgShift{{
  0%  {{background:linear-gradient(155deg,{_bg_a} 0%,{_bg_b} 50%,{_bg_c} 100%);}}
  50% {{background:linear-gradient(200deg,{_bg_b} 0%,{_bg_c} 40%,{_bg_a} 100%);}}
  100%{{background:linear-gradient(240deg,{_bg_c} 0%,{_bg_a} 50%,{_bg_b} 100%);}}
}}

/* ── Aurora glow orbs ── */
.spo{{position:absolute;border-radius:50%;filter:blur(90px);animation:orbDrift ease-in-out infinite alternate;}}
.spo1{{width:620px;height:620px;background:{_orb1c};top:-160px;left:-160px;animation-duration:16s;opacity:0.75;}}
.spo2{{width:520px;height:520px;background:{_orb2c};bottom:-130px;right:-120px;animation-duration:20s;animation-delay:-7s;opacity:0.65;}}
.spo3{{width:380px;height:380px;background:{_orb3c};top:28%;left:48%;animation-duration:12s;animation-delay:-4s;opacity:0.55;}}
@keyframes orbDrift{{
  0%  {{transform:translate(0,0) scale(1);}}
  33% {{transform:translate(30px,-22px) scale(1.10);}}
  66% {{transform:translate(-15px,18px) scale(0.95);}}
  100%{{transform:translate(20px,10px) scale(1.05);}}
}}

/* ── Drifting clouds ── */
.spc{{
  position:absolute;background:{_cloud};
  border-radius:80px;filter:blur(22px);
  animation:cloudDrift linear infinite;
}}
@keyframes cloudDrift{{
  from{{transform:translateX(-320px);}}
  to  {{transform:translateX(110vw);}}
}}

/* ── Rain drops ── */
.spr{{
  position:absolute;top:-70px;
  background:linear-gradient(to bottom,transparent,rgba({_rain_rgb},0.85));
  border-radius:2px;
  animation:rainFall linear infinite;
}}
@keyframes rainFall{{
  from{{transform:translateY(0) translateX(0);opacity:0;}}
  5%  {{opacity:1;}}
  95% {{opacity:1;}}
  to  {{transform:translateY(108vh) translateX(-10px);opacity:0;}}
}}

/* ── Twinkling stars/sparkles ── */
.sps{{
  position:absolute;background:rgba({_star_rgb},0.9);border-radius:50%;
  box-shadow:0 0 5px 2px rgba({_star_rgb},0.7);
  animation:starTwinkle ease-in-out infinite alternate;
}}
@keyframes starTwinkle{{
  from{{opacity:0.05;transform:scale(0.6);}}
  to  {{opacity:1;transform:scale(1.6);}}
}}
</style>

<div id="sp-bg">
  <div class="spo spo1"></div>
  <div class="spo spo2"></div>
  <div class="spo spo3"></div>
  <div class="spc" style="width:480px;height:95px;top:7%;animation-duration:28s;"></div>
  <div class="spc" style="width:340px;height:70px;top:21%;animation-duration:36s;animation-delay:-11s;"></div>
  <div class="spc" style="width:520px;height:85px;top:53%;animation-duration:31s;animation-delay:-6s;"></div>
  <div class="spc" style="width:290px;height:58px;top:71%;animation-duration:23s;animation-delay:-17s;"></div>
  <div class="spc" style="width:410px;height:75px;top:86%;animation-duration:40s;animation-delay:-2s;"></div>
  {_rain_html}
  {_star_html}
</div>
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