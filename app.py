import requests
import pandas as pd
import time
from datetime import datetime
import logging
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit.components.v1 as components

# 📌 API Configuration
API_KEY = "5373f92626b54a5f9324fc7d9ef9a1a9"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

# === FETCH UPCOMING MATCHES ===
def get_upcoming_matches():
    """Fetch next 10 scheduled Premier League matches"""
    logger.info("📅 Fetching upcoming matches...")
    url = f"{BASE_URL}/competitions/PL/matches?status=SCHEDULED"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        matches = response.json().get("matches", [])
        fixtures = [
            {
                "Date": match["utcDate"],
                "Home": match["homeTeam"]["name"],
                "Away": match["awayTeam"]["name"],
            }
            for match in matches[:10]  # Get only the next 10 matches
        ]
        return pd.DataFrame(fixtures)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching matches: {e}")
        return None

# === FETCH PAST RESULTS ===
def get_past_results():
    """Fetch last 10 completed Premier League results"""
    logger.info("📜 Fetching past match results...")
    url = f"{BASE_URL}/competitions/PL/matches?status=FINISHED"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        matches = response.json().get("matches", [])
        results = [
            {
                "Date": match["utcDate"],
                "Home": match["homeTeam"]["name"],
                "Away": match["awayTeam"]["name"],
                "Home Goals": match["score"]["fullTime"].get("home", 0),
                "Away Goals": match["score"]["fullTime"].get("away", 0),
                "Winner": "Home" if match["score"]["fullTime"].get("home", 0) > match["score"]["fullTime"].get("away", 0)
                else "Away" if match["score"]["fullTime"].get("home", 0) < match["score"]["fullTime"].get("away", 0)
                else "Draw",
            }
            for match in matches[-10:]  # Get last 10 results
        ]
        return pd.DataFrame(results)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching past results: {e}")
        return None

# === FETCH LEAGUE STANDINGS ===
def get_standings():
    """Fetch Premier League standings"""
    logger.info("🏆 Fetching Premier League standings...")
    url = f"{BASE_URL}/competitions/PL/standings"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        standings = response.json().get("standings", [])[0]["table"]
        standings_data = [{"Team": team["team"]["name"], "Position": team["position"], "Points": team["points"]} for team in standings]
        return pd.DataFrame(standings_data)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching standings: {e}")
        return None

# === PREDICT MATCH OUTCOME ===
def predict_match(home, away, past_results):
    """Predict match outcome based on last 10 results"""
    if past_results is None or past_results.empty:
        return "🔍 Not enough data for prediction."

    home_games = past_results[past_results["Home"] == home]
    away_games = past_results[past_results["Away"] == away]

    # Calculate performance
    home_wins = (home_games["Winner"] == "Home").sum()
    away_wins = (away_games["Winner"] == "Away").sum()
    draws = (home_games["Winner"] == "Draw").sum() + (away_games["Winner"] == "Draw").sum()

    # Determine prediction
    if home_wins > away_wins:
        return f"🏆 {home} is likely to win!"
    elif away_wins > home_wins:
        return f"🔥 {away} might win!"
    else:
        return "⚖️ This match could be a draw!"

# === DISPLAY DATA IN STREAMLIT ===
def display_upcoming_matches(fixtures_df):
    """Display upcoming matches in Streamlit"""
    if fixtures_df is not None and not fixtures_df.empty:
        st.write("### Upcoming Premier League Matches")
        st.dataframe(fixtures_df, use_container_width=True)
    else:
        st.write("❌ No upcoming matches available.")

def display_past_results(past_results_df):
    """Display past results in Streamlit"""
    if past_results_df is not None and not past_results_df.empty:
        st.write("### Past Match Results")
        st.dataframe(past_results_df, use_container_width=True)
    else:
        st.write("❌ No past results available.")

def display_standings(standings_df):
    """Display Premier League standings"""
    if standings_df is not None and not standings_df.empty:
        st.write("### Premier League Standings")
        st.dataframe(standings_df, use_container_width=True)
    else:
        st.write("❌ No standings available.")

def display_predictions(fixtures_df, past_results_df):
    """Display predictions with color coding"""
    st.write("### Predictions for Upcoming Matches")
    prediction_col = st.empty()

    for _, row in fixtures_df.iterrows():
        result = predict_match(row["Home"], row["Away"], past_results_df)
        match_date = datetime.strptime(row["Date"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y, %H:%M")
        st.markdown(f"**{match_date}** | {row['Home']} vs {row['Away']} ➡️ {result}")

        if "win" in result:
            prediction_col.markdown(f"<p style='color:green; font-weight: bold'>{result}</p>", unsafe_allow_html=True)
        elif "draw" in result:
            prediction_col.markdown(f"<p style='color:gray; font-weight: bold'>{result}</p>", unsafe_allow_html=True)
        else:
            prediction_col.markdown(f"<p style='color:red; font-weight: bold'>{result}</p>", unsafe_allow_html=True)

# === STREAMLIT INTERFACE ===
def main():
    st.set_page_config(page_title="Premier League Match Prediction", page_icon="⚽", layout="wide")
    st.title("Premier League Match Prediction 🏆")
    st.write(
        "This app fetches the latest Premier League match data and predicts the outcome of upcoming matches based on past results."
    )

    # Sidebar for Navigation
    st.sidebar.title("Navigation")
    option = st.sidebar.radio("Choose a section", ["Home", "Upcoming Matches", "Past Results", "Predictions", "League Table"])

    # Home Page
    if option == "Home":
        st.markdown("<h2 style='text-align: center;'>Welcome to the Premier League Match Prediction App!</h2>", unsafe_allow_html=True)
        st.write(
            "Navigate through the sections to explore upcoming matches, past results, and predictions. Choose a section below to get started!"
        )
        
        # Create Buttons for Navigation in a Card Layout
        st.write("<hr>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Upcoming Matches", key="upcoming", help="Check the next matches!"):
                st.session_state["selected_option"] = "Upcoming Matches"
        with col2:
            if st.button("Past Results", key="past", help="See what has already happened!"):
                st.session_state["selected_option"] = "Past Results"
        with col3:
            if st.button("Predictions", key="predictions", help="Predict the future match outcomes!"):
                st.session_state["selected_option"] = "Predictions"

        col4, col5 = st.columns(2)
        
        with col4:
            if st.button("League Table", key="table", help="See how teams are ranked!"):
                st.session_state["selected_option"] = "League Table"

        st.write("<hr>", unsafe_allow_html=True)

    # Fetch Data with Loading States
    with st.spinner('Fetching Latest Data...'):
        try:
            fixtures_df = get_upcoming_matches()
            past_results_df = get_past_results()
            standings_df = get_standings()
            st.success("✅ Data fetched successfully!")
        except Exception as e:
            st.error("❌ Error fetching data. Please try again later.")
            logger.error(f"Failed to fetch data: {e}")
            return

    # Display Data based on session state selection
    selected_option = st.session_state.get("selected_option", "Home")
    if selected_option == "Upcoming Matches":
        display_upcoming_matches(fixtures_df)
    elif selected_option == "Past Results":
        display_past_results(past_results_df)
    elif selected_option == "Predictions":
        if fixtures_df is not None and past_results_df is not None:
            display_predictions(fixtures_df, past_results_df)
    elif selected_option == "League Table":
        display_standings(standings_df)

if __name__ == "__main__":
    main()
