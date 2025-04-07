import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide")

def get_weather_data(lat, lon, location_name):
    start_date = datetime.utcnow().date()
    max_end = datetime(2025, 4, 22).date()  # Limiet van de API voor hourly
    end_date = min(start_date + pd.Timedelta(days=16), max_end)

    base_url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "timezone": "Europe/Berlin",
        "hourly": "apparent_temperature",
        "daily": "temperature_2m_min,temperature_2m_max",
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if "hourly" not in data or "daily" not in data:
        st.warning(f"⚠️ Geen data voor {location_name}: {data.get('reason', 'Onbekende fout')}")
        return pd.DataFrame(), pd.DataFrame()

    # Uurlijkse gevoelstemperatuur
    df_hourly = pd.DataFrame(data["hourly"])
    df_hourly["time"] = pd.to_datetime(df_hourly["time"])
    df_hourly["location"] = location_name

    # Dagelijkse min/max temperatuur
    df_daily = pd.DataFrame(data["daily"])
    df_daily["time"] = pd.to_datetime(df_daily["time"])
    df_daily["location"] = location_name

    return df_hourly, df_daily

# 🌍 Locaties
locations = {
    "Tar, Kroatië": (45.3064, 13.6158),
    "Leeuwarden, Nederland": (53.2012, 5.7999),
}

st.title("🕐 Uurlijkse gevoelstemperatuur & dagelijkse min/max temperatuur")

# Data ophalen
hourly_dfs = []
daily_dfs = []

for loc, (lat, lon) in locations.items():
    df_hourly, df_daily = get_weather_data(lat, lon, loc)
    hourly_dfs.append(df_hourly)
    daily_dfs.append(df_daily)

hourly_combined = pd.concat(hourly_dfs, ignore_index=True)
daily_combined = pd.concat(daily_dfs, ignore_index=True)

if hourly_combined.empty or daily_combined.empty:
    st.error("❌ Geen weerdata beschikbaar.")
    st.stop()

# 🔍 Filter ontbrekende waarden
hourly_combined = hourly_combined.dropna(subset=["apparent_temperature"])
daily_combined = daily_combined.dropna(subset=["temperature_2m_min", "temperature_2m_max"])

# 📈 Plot
st.subheader("🌡️ Dagelijkse min/max temperatuur met uurlijkse gevoelstemperatuur")

fig, ax = plt.subplots(figsize=(18, 6))

for loc in locations.keys():
    daily = daily_combined[daily_combined["location"] == loc]
    hourly = hourly_combined[hourly_combined["location"] == loc]

    # Area tussen min en max
    ax.fill_between(daily["time"], daily["temperature_2m_min"], daily["temperature_2m_max"],
                    alpha=0.3, label=f"{loc}: dag min/max")

    # Uurlijkse gevoelstemperatuur
    ax.plot(hourly["time"], hourly["apparent_temperature"],
            linestyle="dotted", linewidth=1.2, label=f"{loc}: gevoel")

ax.set_ylabel("Temperatuur (°C)")
ax.set_xlabel("Datum")
ax.set_title("🌡️ Dagelijkse min/max temperatuur (area) + gevoelstemperatuur (stippellijn)")
ax.legend()
st.pyplot(fig)

# 📊 Tabel bekijken (optioneel)
with st.expander("📋 Toon ruwe gegevens"):
    st.subheader("Dagelijkse temperatuurgegevens")
    st.dataframe(daily_combined)

    st.subheader("Uurlijkse gevoelstemperatuur")
    st.dataframe(hourly_combined)
