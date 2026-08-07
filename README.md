# 🌤️ SkyPulse — Premium Weather Intelligence

<div align="center">

![SkyPulse Banner](https://img.shields.io/badge/SkyPulse-Weather%20Dashboard-60A5FA?style=for-the-badge&logo=cloud&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OpenWeather](https://img.shields.io/badge/OpenWeatherMap-API-EB6E4B?style=for-the-badge&logo=openweathermap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22D3EE?style=for-the-badge)

**A beautiful, real-time weather dashboard built with Streamlit and the OpenWeatherMap API.**  
Live forecasts · Air quality · Interactive charts · Dark & Light mode

🔗 **[Live Demo →](https://skypulse-weather-api.streamlit.app/)**

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌡️ **Real-time Weather** | Current temperature, feels-like, humidity, wind speed, pressure and visibility |
| 📅 **5-Day Forecast** | Hourly and daily forecast breakdown with trend charts |
| 🌫️ **Air Quality Index** | AQI with PM2.5, PM10, O₃, NO₂ pollutant levels |
| 📊 **Interactive Charts** | Plotly-powered temperature and humidity trend graphs |
| 🗺️ **Location Map** | Embedded map centred on the searched city |
| 🔍 **Smart City Search** | Autocomplete suggestions from a global city database |
| 🌙 **Dark / Light Mode** | Fully themed UI that switches seamlessly |
| 📤 **Export Data** | Download weather data as CSV or JSON |
| 🕐 **Recent Searches** | Quick-access history of your last searched cities |
| 🎨 **Animated Landing Page** | Weather-themed background with rain, aurora orbs, drifting clouds and twinkling stars |

---

## 🖼️ Screenshots

> _Landing page with animated weather background_

```
🌤️ SkyPulse
Premium Weather Intelligence — powered by OpenWeather

[ 🔍 Search any city in the world... ]
          [ 🔍 Search Weather ]

🌍 Popular cities
Kottayam  Mumbai  Tokyo  London
New York  Dubai   Paris  Sydney
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- An [OpenWeatherMap API key](https://openweathermap.org/api) (free tier works)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Sreesh-S/SkyPulse.git
cd SkyPulse

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
# Create a .env file in the project root:
echo OPENWEATHER_API_KEY=your_api_key_here > .env

# 5. Run the app
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## ☁️ Deployment (Streamlit Cloud)

This app is deployed on **Streamlit Community Cloud** (free):

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"Create app"** → select this repo → set main file to `app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   OPENWEATHER_API_KEY = "your_api_key_here"
   ```
5. Click **Deploy!** 🚀

---

## 🗂️ Project Structure

```
SkyPulse/
│
├── app.py                  # Main Streamlit application
├── config.py               # API key config (env + Streamlit secrets)
├── requirements.txt        # Python dependencies
│
├── api/
│   ├── __init__.py
│   └── weather.py          # OpenWeatherMap API calls
│
├── components/
│   └── sidebar.py          # Sidebar UI component
│
├── utils/
│   ├── __init__.py
│   ├── charts.py           # Plotly chart builders
│   ├── export.py           # CSV / JSON export helpers
│   └── helpers.py          # Utility functions (unit conversion, formatting)
│
├── styles/
│   └── theme.css           # Custom CSS theme
│
└── .streamlit/
    └── config.toml         # Streamlit configuration
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web app framework |
| [OpenWeatherMap API](https://openweathermap.org/api) | Weather & air quality data |
| [Plotly](https://plotly.com/python/) | Interactive charts |
| [Python-dotenv](https://pypi.org/project/python-dotenv/) | Local environment variable management |
| CSS Animations | Background visual effects |

---

## 🔐 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OPENWEATHER_API_KEY` | Your OpenWeatherMap API key | ✅ Yes |

**Local development:** Add to a `.env` file in the project root.  
**Streamlit Cloud:** Add under App Settings → Secrets.

---

## 📦 Dependencies

```txt
streamlit
requests
python-dotenv
plotly
```

---

## 🤝 Contributing

Contributions, issues and feature requests are welcome!

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Sreesh S**  
[![GitHub](https://img.shields.io/badge/GitHub-Sreesh--S-181717?style=flat&logo=github)](https://github.com/Sreesh-S)

---

<div align="center">

Made with ❤️ and ☁️ · Powered by [OpenWeatherMap](https://openweathermap.org) · Built with [Streamlit](https://streamlit.io)

</div>
