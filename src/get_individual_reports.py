# There are some newutral cases with no signal in the final report
# Trend Without a Catalyst (historical_result) (for the last 6 days) : The Technology sector might have a positive trend, but if today's news is neutral and boring, there's no immediate reason to act. The bot waits.
# Catalyst Without a Trend (today_result): A big, positive news event might happen for the Energy sector, but if there's no underlying positive trend, the bot sees it as an isolated event, not a high-confidence signal.
import json
from src.analysis.historical_analyzer import analyze_historical_trends
from src.analysis.today_analyzer import analyze_todays_impact
from src.database import init_db

def fetch_independent_analyses():
    """
    Runs the two analysis modules independently and prints their structured output.
    """
    print("--- Initializing Database ---")
    init_db()

    print("\n" + "="*50)
    print("Fetching: 1. Historical Trend (Last 6 Days)")
    print("="*50)
    historical_result = analyze_historical_trends()
    # Pretty-print the JSON-like dictionary
    print(json.dumps(historical_result, indent=2))

    print("\n" + "="*50)
    print("Fetching: 2. Today's Catalyst (Today's News)")
    print("="*50)
    today_result = analyze_todays_impact()
    # Pretty-print the JSON-like dictionary
    print(json.dumps(today_result, indent=2))


if __name__ == '__main__':
    fetch_independent_analyses()
