import os
import glob
from datetime import datetime

REV_SEASONS = {0: 'Winter', 1: 'Spring', 2: 'Summer', 3: 'Fall'}
SEASONS_MAP = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
OUTPUT_FILE = "group_missing_seasons_report.txt"

def str_to_val(season_str):
    """Converts a string like 'Winter 2001' or 'BEGINNING_OF_TIME' back to an integer."""
    if season_str == "BEGINNING_OF_TIME":
        return 0 # Use 0 as the absolute minimum bound for set math
    parts = season_str.split()
    season = parts[0]
    year = int(parts[1])
    return (year * 4) + SEASONS_MAP[season]

def val_to_str(val):
    """Converts an integer back to 'Winter 2001'."""
    year = val // 4
    season = REV_SEASONS[val % 4]
    return f"{season} {year}"

def format_missing_ranges(missing_vals):
    """Takes a set of missing season integers and formats them into continuous ranges descending."""
    if not missing_vals:
        return []

    missing_vals = list(missing_vals)
    
    # Temporarily remove BEGINNING_OF_TIME (0) to process standard ranges
    has_bot = 0 in missing_vals
    if has_bot:
        missing_vals.remove(0)

    if not missing_vals:
        return ["BEGINNING_OF_TIME"] if has_bot else []

    # Sort descending (newest to oldest)
    missing_vals = sorted(missing_vals, reverse=True)
    ranges = []
    
    start_range = missing_vals[0]
    prev_val = missing_vals[0]

    for val in missing_vals[1:]:
        if val == prev_val - 1:
            # Sequence continues
            prev_val = val
        else:
            # Sequence broken
            if start_range == prev_val:
                ranges.append(val_to_str(start_range))
            else:
                ranges.append(f"{val_to_str(prev_val)} - {val_to_str(start_range)}")
            start_range = val
            prev_val = val

    # Handle the final block and append BEGINNING_OF_TIME logic
    if has_bot:
        # If the contiguous block reaches all the way down to 1, it connects to 0 (BOT)
        if prev_val == 1:
            ranges.append(f"BEGINNING_OF_TIME - {val_to_str(start_range)}")
        else:
            if start_range == prev_val:
                ranges.append(val_to_str(start_range))
            else:
                ranges.append(f"{val_to_str(prev_val)} - {val_to_str(start_range)}")
            ranges.append("BEGINNING_OF_TIME")
    else:
        if start_range == prev_val:
            ranges.append(val_to_str(start_range))
        else:
            ranges.append(f"{val_to_str(prev_val)} - {val_to_str(start_range)}")

    return ranges

def main():
    # Find all report files in the current directory, ignoring the group output file if it exists
    report_files = [f for f in glob.glob("missing_seasons_report_*.txt") if f != OUTPUT_FILE]
    
    if not report_files:
        print("No user report files found! Run the main script on some users first.")
        return
        
    print(f"Found {len(report_files)} report files. Parsing and finding intersections...")
    
    # Structure: filter_sets[filter_header] = [set_for_user1, set_for_user2, ...]
    filter_sets = {}
    parsed_users = []

    for filename in report_files:
        username = filename.replace("missing_seasons_report_", "").replace(".txt", "")
        parsed_users.append(username)
        
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_filter = None
        user_missing = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("--- Filters:"):
                current_filter = line
                user_missing[current_filter] = set()
            elif line.startswith("* ") and current_filter:
                range_str = line[2:] # strip off the "* "
                
                if " - " in range_str:
                    parts = range_str.split(" - ")
                    # Sort the bounds safely just in case
                    bound1 = str_to_val(parts[0])
                    bound2 = str_to_val(parts[1])
                    lower_bound = min(bound1, bound2)
                    upper_bound = max(bound1, bound2)
                    
                    # Add all seasons in this contiguous range to the user's set
                    user_missing[current_filter].update(range(lower_bound, upper_bound + 1))
                else:
                    # Single season
                    user_missing[current_filter].add(str_to_val(range_str))
                    
        # Append this user's parsed sets to the global tracker
        for filt, season_set in user_missing.items():
            if filt not in filter_sets:
                filter_sets[filt] = []
            filter_sets[filt].append(season_set)

    print(f"Writing group intersection data to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("GROUP MISSING SEASONS REPORT\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Users Included ({len(parsed_users)}): {', '.join(parsed_users)}\n")
        f.write("="*80 + "\n\n")
        f.write("HOW TO READ THIS REPORT:\n")
        f.write("This file is an aggregate intersection. The seasons listed under each filter combination represent the times when literally NOBODY in this group watched a qualifying anime. If even one person in the group watched a show from a season, that season is eliminated from this list.\n\n")
        f.write("="*80 + "\n\n")

        for filt, sets_list in filter_sets.items():
            # If a filter didn't exist in all files for some reason, skip it to prevent bad data
            if len(sets_list) != len(report_files):
                continue
                
            # Intersect all sets using Python's native set unpacking
            intersected_seasons = set.intersection(*sets_list)
            
            ranges = format_missing_ranges(intersected_seasons)
            
            f.write(f"{filt}\n")
            if not ranges:
                f.write("None! Between everyone in the group, at least one person has watched something from every possible season under these criteria.\n\n")
            else:
                for r in ranges:
                    f.write(f"* {r}\n")
                f.write("\n")
                
    print("Done! Group report generated.")

if __name__ == "__main__":
    main()
