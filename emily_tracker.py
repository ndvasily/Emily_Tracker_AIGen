import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- FILE MANAGEMENT ---
FEEDING_FILE = "feedings.csv"
SLEEP_FILE = "sleeps.csv"

# Function to load data from CSV
def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    else:
        return []

# Function to save data to CSV
def save_data(file_path, data):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

# Initialize session state variables
if 'feedings' not in st.session_state:
    st.session_state.feedings = load_data(FEEDING_FILE)
if 'sleeps_total' not in st.session_state:
    st.session_state.sleeps_total = load_data(SLEEP_FILE)
if 'current_sleep_start' not in st.session_state:
    st.session_state.current_sleep_start = None

# --- FEEDING SECTION ---
st.header("Feeding Log")

# Input fields for feeding data
ml = st.number_input("Amount (ml)", min_value=0, step=10)
milk_type = st.selectbox("Type of Milk", ["Formula", "Breast Milk", "Other"])
additional_food = st.text_input("Additional Food (optional)")
time_str = st.text_input("Time of Day (HH:MM)", value=datetime.now().strftime("%H:%M"))
date_str = st.text_input("Date (YYYY-MM-DD)", value=date.today().isoformat())

if st.button("Log Feeding"):
    try:
        feeding_time = datetime.strptime(time_str, "%H:%M").time()
        new_feeding = {
            'date': date_str,
            'time': feeding_time.isoformat(),
            'ml': ml,
            'milk_type': milk_type,
            'additional_food': additional_food
        }
        if 'feedings' not in st.session_state:
            st.session_state.feedings = []
        st.session_state.feedings.append(new_feeding)
        save_data(FEEDING_FILE, st.session_state.feedings)
        st.success("Feeding logged!")
    except ValueError:
        st.error("Invalid time format. Please use HH:MM.")

# Display latest feedings
st.subheader("Latest Feedings")

def sort_feedings(feedings):
    if not isinstance(feedings, list):
        return []
    return sorted(feedings, key=lambda x: (x['date'], x['time']), reverse=True)

if 'feedings' in st.session_state:
    st.session_state.feedings = sort_feedings(st.session_state.feedings)

if 'feedings' in st.session_state and st.session_state.feedings:
    feedings_df = pd.DataFrame(st.session_state.feedings)
    st.dataframe(feedings_df[['date', 'time', 'ml', 'milk_type', 'additional_food']].head())
else:
    st.write("No feedings logged yet.")

# --- SLEEP SECTION ---
st.header("Sleep Log")

# Sleep Logging
if st.session_state.current_sleep_start is None:
    sleep_time_str = st.text_input("Fell Asleep At (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    if st.button("Start Sleep"):
        try:
            st.session_state.current_sleep_start = datetime.fromisoformat(sleep_time_str)
            st.success("Sleep started!")
        except ValueError:
            st.error("Invalid datetime format. Please use YYYY-MM-DD HH:MM.")
        st.rerun()

else:
    wake_time_str = st.text_input("Woke Up At (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    if st.button("End Sleep"):
        sleep_start = st.session_state.current_sleep_start
        try:
            wake_time_combined = datetime.fromisoformat(wake_time_str)

            # Ensure wake_time is after sleep_time
            if wake_time_combined <= sleep_start:
                st.error("Wake time must be after sleep time.")
            else:
                new_sleep = {
                    'date': sleep_start.date().isoformat(),
                    'sleep_time': sleep_start.isoformat(),
                    'wake_time': wake_time_combined.isoformat(),
                    'duration': (wake_time_combined - sleep_start).total_seconds() / 3600
                }
                if 'sleeps' not in st.session_state:
                    st.session_state.sleeps = []

                st.session_state.sleeps.append(new_sleep)

                # Update the total sleep duration
                st.session_state.sleeps_total = sum(s['duration'] for s in st.session_state.sleeps)
                save_data(SLEEP_FILE, st.session_state.sleeps)
                st.session_state.current_sleep_start = None
                st.success("Sleep logged!")


        except ValueError:
            st.error("Invalid datetime format. Please use YYYY-MM-DD HH:MM.")
        st.rerun()

# Display latest sleeps
st.subheader("Latest Sleeps")

def sort_sleeps(sleeps):
    if not isinstance(sleeps, list):
        return []
    return sorted(sleeps, key=lambda x: (x['date'], x['sleep_time']), reverse=True)

if 'sleeps' in st.session_state:
    st.session_state.sleeps = sort_sleeps(st.session_state.sleeps)

if 'sleeps' in st.session_state and st.session_state.sleeps:
    sleeps_df = pd.DataFrame(st.session_state.sleeps)
    st.dataframe(sleeps_df[['date', 'sleep_time', 'wake_time', 'duration']].head())
else:
    st.write("No sleeps logged yet.")

# --- DAILY INFORMATION SECTION ---
st.header("Daily Summary")
today = date.today().isoformat()

# Calculate totals for the day
total_ml = 0
milk_types = set()
if 'feedings' in st.session_state and st.session_state.feedings:
    today_feedings = [f for f in st.session_state.feedings if f['date'] == today]
    total_ml = sum(f['ml'] for f in today_feedings)
    milk_types = set(f['milk_type'] for f in today_feedings)

total_sleep_duration = 0
if 'sleeps' in st.session_state and st.session_state.sleeps:
    today_sleeps =  [s for s in st.session_state.sleeps if s['date'] == today]
    total_sleep_duration = sum(s['duration'] for s in today_sleeps)


# Create a DataFrame to display the information
daily_summary = pd.DataFrame({
    'Date': [date.fromisoformat(today).strftime('%Y-%m-%d')],
    'Total Feeding (ml)': [total_ml],
    'Milk Types': [', '.join(milk_types)],
    'Total Sleep (hours)': [total_sleep_duration]
})

# Display the DataFrame
st.dataframe(daily_summary)
