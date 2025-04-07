import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide")

def get_hourly_weather(lat, lon, location_name):
    start_date = datetime.utcnow().date()
    max_end = datetime(2025, 4, 22).date()  # API-limiet
    end_date = min(start_date + pd.Timedelta(days=21), max_end)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,apparent_temperature,precipitation"
        f"&start_date={start_date}&end_date={end_date}"
        f"&timezone=Europe%2FBerlin"
    )

    response = requests.get(url)
    data = response.json()

    if "hourly" not in data:
        st.warning(f"⚠️ Geen data voor {location_name}: {data.get('reason', 'Onbekende fout')}")
        return pd.DataFrame()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df["location"] = location_name
    return df


# Locaties
locations = {
    "Tar, Kroatië": (45.3064, 13.6158),
    "Leeuwarden, Nederland": (53.2012, 5.7999),
}

st.title("🕐 Uurlijkse weersvoorspelling (max 21 dagen)")

# Data ophalen
dfs = []
for loc, (lat, lon) in locations.items():
    df = get_hourly_weather(lat, lon, loc)
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)

# Stop als alles leeg is
if combined.empty:
    st.error("❌ Geen weerdata beschikbaar.")
    st.stop()

# Filter rijen zonder temperatuur of gevoelstemperatuur
combined = combined.dropna(subset=["temperature_2m", "apparent_temperature", "precipitation"])

# --- Area plot temperatuur ---

# --- Mooie area plot tussen echte en gevoelstemperatuur ---
st.subheader("🌡️ Temperatuur: verschil tussen echt en gevoel")

fig1, ax1 = plt.subplots(figsize=(18, 6))

for loc in locations.keys():
    subset = combined[combined["location"] == loc].copy()
    # Bereken min/max per tijdstip tussen gevoel en echt
    temp_low = subset[["temperature_2m", "apparent_temperature"]].min(axis=1)
    temp_high = subset[["temperature_2m", "apparent_temperature"]].max(axis=1)

    # Plot het gebied ertussen
    ax1.fill_between(subset["time"], temp_low, temp_high, alpha=0.3, label=f"{loc}: verschil gevoel ↔ echt")
    
    # Extra: lijn voor echte temperatuur
    ax1.plot(subset["time"], subset["temperature_2m"], linestyle="-", linewidth=1.2, label=f"{loc}: temperatuur")

ax1.set_ylabel("Temperatuur (°C)")
ax1.set_xlabel("Datum en tijd")
ax1.legend()
st.pyplot(fig1)



ax1.set_ylabel("Temperatuur (°C)")
ax1.set_xlabel("Datum en tijd")
ax1.legend()
st.pyplot(fig1)

# --- Area plot neerslag ---
st.subheader("🌧️ Neerslag")
fig2, ax2 = plt.subplots(figsize=(18, 6))
for loc in locations.keys():
    subset = combined[combined["location"] == loc]
    ax2.fill_between(subset["time"], 0, subset["precipitation"], alpha=0.3, label=loc)
ax2.set_ylabel("Neerslag (mm)")
ax2.set_xlabel("Datum en tijd")
ax2.legend()
st.pyplot(fig2)

# --- Optioneel: tabel
with st.expander("📊 Bekijk ruwe data"):
    st.dataframe(combined)
