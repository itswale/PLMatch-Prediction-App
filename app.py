import requests
import pandas as pd
from datetime import datetime
import logging
import streamlit as st
import time

# 📌 API Configuration
API_KEY = "5373f92626b54a5f9324fc7d9ef9a1a9"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

# Enable caching for API calls
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(url):
    """Fetch data from the API with error handling."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching data: {e}")
        return None

# === FETCH UPCOMING MATCHES ===
def get_upcoming_matches():
    """Fetch next 10 scheduled Premier League matches."""
    logger.info("📅 Fetching upcoming matches...")
    url = f"{BASE_URL}/competitions/PL/matches?status=SCHEDULED"
    data = fetch_data(url)
    if data:
        matches = data.get("matches", [])
        fixtures = [
            {
                "Date": match["utcDate"],
                "Home": match["homeTeam"]["name"],
                "Away": match["awayTeam"]["name"],
            }
            for match in matches[:10]  # Get only the next 10 matches
        ]
        return pd.DataFrame(fixtures)
    return None

# === FETCH PAST RESULTS ===
def get_past_results():
    """Fetch last 10 completed Premier League results."""
    logger.info("📜 Fetching past match results...")
    url = f"{BASE_URL}/competitions/PL/matches?status=FINISHED"
    data = fetch_data(url)
    if data:
        matches = data.get("matches", [])
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
    return None

# === FETCH LEAGUE STANDINGS ===
def get_standings():
    """Fetch Premier League standings."""
    logger.info("🏆 Fetching Premier League standings...")
    url = f"{BASE_URL}/competitions/PL/standings"
    data = fetch_data(url)
    if data:
        standings = data.get("standings", [])[0]["table"]
        standings_data = [{"Team": team["team"]["name"], "Position": team["position"], "Points": team["points"]} for team in standings]
        return pd.DataFrame(standings_data)
    return None

# === PREDICT MATCH OUTCOME ===
def predict_match(home, away, past_results):
    """Predict match outcome based on last 10 results."""
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
    """Display upcoming matches in Streamlit."""
    if fixtures_df is not None and not fixtures_df.empty:
        st.write("### Upcoming Premier League Matches")
        st.dataframe(fixtures_df, use_container_width=True)
    else:
        st.error("❌ No upcoming matches available. Please refresh the page or try again later.")

def display_past_results(past_results_df):
    """Display past results in Streamlit."""
    if past_results_df is not None and not past_results_df.empty:
        st.write("### Past Match Results")
        st.dataframe(past_results_df, use_container_width=True)
    else:
        st.error("❌ No past results available. Please refresh the page or try again later.")

def display_predictions(fixtures_df, past_results_df):
    """Display predictions with color coding."""
    st.write("### Predictions for Upcoming Matches")
    if fixtures_df is None or past_results_df is None:
        st.error("❌ Data not available for predictions. Please refresh the page or try again later.")
        return

    for _, row in fixtures_df.iterrows():
        result = predict_match(row["Home"], row["Away"], past_results_df)
        match_date = datetime.strptime(row["Date"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y, %H:%M")
        st.markdown(f"**{match_date}** | {row['Home']} vs {row['Away']} ➡️ {result}")

        # Improved color coding for predictions
        if "win" in result:
            st.markdown(f"<p style='color:#34B1AA; font-weight: bold'>{result}</p>", unsafe_allow_html=True)
        elif "draw" in result:
            st.markdown(f"<p style='color:#E0B50F; font-weight: bold'>{result}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color:#F29F67; font-weight: bold'>{result}</p>", unsafe_allow_html=True)

# === STREAMLIT INTERFACE ===
def main():
    st.set_page_config(page_title="Premier League Match Prediction", page_icon="⚽", layout="wide")
    
    # Custom CSS for better styling
    st.markdown(
        """
        <style>
        /* General Styling */
        body {
            font-family: 'Arial', sans-serif;
            background-color: #1E1E2C; /* Dark background */
            color: #FFFFFF; /* White text */
        }
        h1, h2, h3 {
            color: #F29F67; /* Primary color for headings */
        }
        p {
            color: #FFFFFF; /* White text */
        }
        .stButton button {
            background-color: #3B8FF3; /* Supporting color for buttons */
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .stButton button:hover {
            background-color: #34B1AA; /* Supporting color for button hover */
        }
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        /* Card Styling */
        .card {
            padding: 20px;
            background-color: #1E1E2C; /* Dark background */
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.2s;
        }
        .card:hover {
            transform: scale(1.05);
        }
        .card h3 {
            color: #F29F67; /* Primary color for card headings */
        }
        .card p {
            color: #FFFFFF; /* White text */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Header Section
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #F29F67;">Premier League Match Prediction 🏆</h1>
            <p style="color: #FFFFFF; font-size: 18px;">
            Explore the latest Premier League data and predictions. Choose a section below to get started!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch Data with Loading Spinner
    with st.spinner("Fetching data..."):
        time.sleep(2)  # Simulate a delay to make the loading visible
        fixtures_df = get_upcoming_matches()
        past_results_df = get_past_results()
        standings_df = get_standings()

    # Create Cards for Navigation
    st.write("<hr>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="card">
                <h3>📅 Upcoming Matches</h3>
                <p>{len(fixtures_df) if fixtures_df is not None else 0} matches scheduled</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View Matches", key="upcoming"):
            st.session_state["selected_option"] = "Upcoming Matches"

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <h3>📜 Past Results</h3>
                <p>{len(past_results_df) if past_results_df is not None else 0} results available</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View Results", key="past"):
            st.session_state["selected_option"] = "Past Results"

    with col3:
        st.markdown(
            f"""
            <div class="card">
                <h3>🔮 Predictions</h3>
                <p>{len(fixtures_df) if fixtures_df is not None else 0} matches to predict</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View Predictions", key="predictions"):
            st.session_state["selected_option"] = "Predictions"

    st.write("<hr>", unsafe_allow_html=True)

    # Display Data based on session state selection
    selected_option = st.session_state.get("selected_option")
    if selected_option == "Upcoming Matches":
        with st.spinner("Loading Upcoming Matches..."):
            time.sleep(1)  # Simulate a delay to make the loading visible
            display_upcoming_matches(fixtures_df)
    elif selected_option == "Past Results":
        with st.spinner("Loading Past Results..."):
            time.sleep(1)  # Simulate a delay to make the loading visible
            display_past_results(past_results_df)
    elif selected_option == "Predictions":
        with st.spinner("Loading Predictions..."):
            time.sleep(1)  # Simulate a delay to make the loading visible
            display_predictions(fixtures_df, past_results_df)

    # Refresh Button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

if __name__ == "__main__":
    main()