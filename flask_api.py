import json
import asyncio
import threading
from flask import Flask, request, jsonify
from datetime import datetime
import re

app = Flask(__name__)
match_data = []
DATE_FORMAT = "%d %b %H:%M"

async def load_data():
    global match_data
    while True:
        try:
            with open('../match_data.json', 'r') as f:
                match_data = json.load(f)
            print("Data reloaded from match_data.json")
        except Exception as e:
            print(f"Failed to load data from match_data.json: {e}")
        await asyncio.sleep(5)

@app.route('/api/live', methods=['GET'])
def get_live_matches():
    live_matches = [match for match in match_data if match.get('status') == 'Live' or match.get('status') == 'Halftime']
    return jsonify(live_matches), 200

@app.route('/api/upcoming', methods=['GET'])
def get_upcoming_matches():
    upcoming_matches = [match for match in match_data if 'Upcoming' in match['status'] or 'DATE NOT FOUND' in match['status']]
    

    # Extract datetime from the status string and start_time
    def extract_datetime(match):
        if 'DATE NOT FOUND' in match['status']:
            # Return a very small datetime to place it at the beginning
            return datetime.min
        match_date_str = match['status'].replace('Upcoming ', '') + ' ' + match['start_time']
        try:
            return datetime.strptime(match_date_str, DATE_FORMAT)
        except ValueError as e:
            print(f"Error parsing date for match {match['home_team']} vs {match['away_team']}: {e}")
            return datetime.max
    
    sorted_upcoming_matches = sorted(upcoming_matches, key=lambda x: (extract_datetime(x) == datetime.min, extract_datetime(x)))
    print(sorted_upcoming_matches)
    return jsonify(sorted_upcoming_matches)

@app.route('/api/finished', methods=['GET'])
def get_finished_matches():
    finished_matches = [match for match in match_data if match.get('status') == 'Finished']
    return jsonify(finished_matches), 200

@app.route('/api/match', methods=['GET'])
def get_match_by_team():
    team_name = request.args.get('team')
    if not team_name:
        return jsonify({"error": "No team name provided"}), 400

    matches = [match for match in match_data if match.get('home_team') == team_name or match.get('away_team') == team_name]
    live_matches = [match for match in matches if match.get('status') == 'Live']

    if not live_matches:
        return jsonify({"message": "No live matches found for the given team"}), 404

    return jsonify(live_matches), 200

def start_flask_app():
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(load_data())

        # Run Flask app in a separate thread
        flask_thread = threading.Thread(target=start_flask_app)
        flask_thread.start()

        # Run the asyncio event loop
        loop.run_forever()
    except KeyboardInterrupt:
        print("API Stopped by user.")
