import argparse
import requests
import json
import os
import time
from datetime import datetime
from itertools import product

# MAL API constants
MAL_API_URL = "https://api.myanimelist.net/v2/users/{}/animelist"
MAL_SEASONS = {'winter': 0, 'spring': 1, 'summer': 2, 'fall': 3}
REV_SEASONS = {0: 'Winter', 1: 'Spring', 2: 'Summer', 3: 'Fall'}

def val_to_str(val):
    """Converts a season integer value back to a string like 'Winter 2001'."""
    year = val // 4
    season = REV_SEASONS[val % 4]
    return f"{season} {year}"

def get_current_season_val():
    """Calculates the integer value of the current season."""
    now = datetime.now()
    year = now.year
    # Winter: Jan-Mar, Spring: Apr-Jun, Summer: Jul-Sep, Fall: Oct-Dec
    if 1 <= now.month <= 3: season_index = 0
    elif 4 <= now.month <= 6: season_index = 1
    elif 7 <= now.month <= 9: season_index = 2
    else: season_index = 3
    
    return (year * 4) + season_index

def fetch_user_list(username, client_id, force_update):
    """Fetches the user's list from MAL, utilizing local caching to avoid API limits."""
    cache_file = f"mal_cache_{username}.json"
    
    if not force_update and os.path.exists(cache_file):
        print(f"Loading cached data for {username}...")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    print(f"Fetching data for {username} from MyAnimeList API...")
    headers = {'X-MAL-CLIENT-ID': client_id}
    params = {
        'limit': 1000,
        'fields': 'list_status,start_season,media_type,num_episodes,average_episode_duration'
    }
    
    all_data = []
    url = MAL_API_URL.format(username)
    
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break
            
        data = response.json()
        all_data.extend(data.get('data', []))
        
        # Pagination
        url = data.get('paging', {}).get('next')
        if url:
            params = {} # params are already included in the 'next' URL
            print("Fetching next page...")
            time.sleep(1) # Be polite to the API
            
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f)
        
    return all_data

def format_missing_ranges(missing_vals, min_watched_val):
    """Formats a list of missing season values into continuous ranges descending."""
    if not missing_vals:
        return []

    # Sort descending (newest to oldest)
    missing_vals = sorted(list(missing_vals), reverse=True)
    ranges = []
    
    start_range = missing_vals[0]
    prev_val = missing_vals[0]

    for val in missing_vals[1:]:
        if val == prev_val - 1:
            # Continues the sequence
            prev_val = val
        else:
            # Sequence broken, save the completed range
            if start_range == prev_val:
                ranges.append(val_to_str(start_range))
            else:
                ranges.append(f"{val_to_str(prev_val)} - {val_to_str(start_range)}")
            
            # Start new range
            start_range = val
            prev_val = val

    # Append the final sequence group
    if start_range == prev_val:
        ranges.append(val_to_str(start_range))
    else:
        ranges.append(f"{val_to_str(prev_val)} - {val_to_str(start_range)}")

    # Add the beginning of time range
    if min_watched_val is not None:
        ranges.append(f"BEGINNING_OF_TIME - {val_to_str(min_watched_val - 1)}")
    else:
        ranges.append(f"BEGINNING_OF_TIME - {val_to_str(get_current_season_val())}")

    return ranges

def main():
    parser = argparse.ArgumentParser(description="Find missing anime seasons for a MAL user.")
    parser.add_argument("username", help="MyAnimeList Username")
    parser.add_argument("client_id", help="MyAnimeList API Client ID")
    parser.add_argument("--force_update", action="store_true", help="Ignore cache and fetch fresh data")
    args = parser.parse_args()

    raw_data = fetch_user_list(args.username, args.client_id, args.force_update)
    current_val = get_current_season_val()
    
    # Process and normalize data into an easy-to-filter format
    processed_entries = []
    for item in raw_data:
        node = item['node']
        status = item['list_status']['status']
        
        # We never care about PTW
        if status == 'plan_to_watch':
            continue
            
        # We can't track entries that have no known start season
        if 'start_season' not in node:
            continue
            
        season = node['start_season']
        season_val = (season['year'] * 4) + MAL_SEASONS[season['season']]
        
        media_type = node.get('media_type', 'unknown')
        
        # Calculate runtime (MAL gives average_episode_duration in seconds)
        episodes = max(1, node.get('num_episodes', 0)) # Treat ongoing (0) as at least 1 episode
        duration_mins = node.get('average_episode_duration', 0) / 60
        total_runtime_mins = episodes * duration_mins
        
        processed_entries.append({
            'title': node.get('title'),
            'status': status,
            'season_val': season_val,
            'media_type': media_type,
            'runtime': total_runtime_mins
        })

    # ABLATION DEFINITIONS
    status_filters = {
        "Base (Completed, Watching, Hold, Dropped)": ['completed', 'watching', 'on_hold', 'dropped'],
        "No Dropped": ['completed', 'watching', 'on_hold'],
        "No Dropped & No Hold": ['completed', 'watching'],
        "Completed Only": ['completed']
    }

    media_filters = {
        "All Types": [],
        "No CM/PV/Music/Other": ['cm', 'pv', 'music', 'other', 'unknown'],
        "No OVA (and above)": ['cm', 'pv', 'music', 'other', 'unknown', 'ova'],
        "No Movies (and above)": ['cm', 'pv', 'music', 'other', 'unknown', 'ova', 'movie'],
        "No ONAs (and above)": ['cm', 'pv', 'music', 'other', 'unknown', 'ova', 'movie', 'ona']
    }

    runtime_filters = {
        "Any Runtime": 0,
        "> 24 Mins": 24,
        "> 60 Mins": 60,
        "> 120 Mins": 120,
        "> 240 Mins": 240
    }

    output_filename = f"missing_seasons_report_{args.username}.txt"
    print(f"Processing ablations and writing to {output_filename}...")
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(f"MISSING SEASONS REPORT FOR: {args.username}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

        # Iterate through every combination of ablations
        for (s_name, s_vals), (m_name, m_vals), (r_name, r_val) in product(
            status_filters.items(), media_filters.items(), runtime_filters.items()
        ):
            # Apply filters to find all watched seasons under these conditions
            watched_seasons = set()
            for entry in processed_entries:
                if entry['status'] in s_vals:
                    if entry['media_type'] not in m_vals:
                        if entry['runtime'] >= r_val:
                            watched_seasons.add(entry['season_val'])

            # Find missing seasons
            if watched_seasons:
                min_watched = min(watched_seasons)
                all_possible = set(range(min_watched, current_val + 1))
                missing_vals = all_possible - watched_seasons
            else:
                min_watched = None
                missing_vals = set()

            # Format the output
            ranges = format_missing_ranges(missing_vals, min_watched)

            # Write header block for this ablation
            f.write(f"--- Filters: [{s_name}] | [{m_name}] | [{r_name}] ---\n")
            if not ranges:
                f.write("No missing seasons based on these criteria.\n\n")
            else:
                for r in ranges:
                    f.write(f"* {r}\n")
                f.write("\n")

    print("Done! Check the generated text file for your results.")

if __name__ == "__main__":
    main()
