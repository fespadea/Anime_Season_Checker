# MyAnimeList Missing Seasons Calculator

A Python script that analyzes a MyAnimeList (MAL) user's list to determine which anime seasons (e.g., Winter 2006, Spring 2012) they have *completely missed*, meaning they haven't watched a single qualifying anime that originally aired during that time.

Because people have different definitions of what "counts" as having watched something from a season, this script calculates **multiple lists of missing seasons based on different combinations of filters** (Status, Media Type, and Runtime).

## Features

* **Comprehensive Filter Combinations (Ablations):** Generates reports analyzing your missing seasons with 100+ different filter combinations.
* **List Status Filtering:** Choose whether to include Dropped, On-Hold, or just Completed/Watching shows. (Plan to Watch is always ignored).
* **Media Type Filtering:** Progressively excludes Specials, OVAs, Movies, and ONAs to see how your missing seasons change if you only count traditional TV broadcasts.
* **Runtime Filtering:** Excludes short clips or micro-series by setting total runtime minimums (>24 mins, >60 mins, >120 mins, >240 mins). Correctly handles "ongoing" series runtimes.
* **Smart Local Caching:** Saves your MAL list to a local JSON file (`mal_cache_<username>.json`) after the first run. Subsequent runs are instantaneous and require no API key!
* **Contiguous Range Formatting:** Automatically groups sequential missing seasons into easy-to-read ranges (e.g., `Winter 2001 - Spring 2006`).

## Prerequisites

1. **Python 3.x** installed on your system.
2. The `requests` library. Install it via terminal/command prompt:
   ```bash
   pip install requests
   ```
3. A **MyAnimeList API Client ID**. 
   * Go to the [MAL API Panel](https://myanimelist.net/apiconfig).
   * Click "Create ID" and fill out the required fields (you can just put placeholder info for the App details).
   * Copy your newly generated `Client ID`.

## Usage

Run the script from your terminal or command prompt.

### First Run (Requires Client ID)
To fetch a user's list for the first time, you must provide your Client ID:
```bash
python mal_missing_seasons.py <MAL_USERNAME> <YOUR_CLIENT_ID>
```
*Example:*
```bash
python mal_missing_seasons.py Guts xyz123abc456
```

### Subsequent Runs (No Client ID Needed!)
Once a user's list has been cached locally, you can run the script instantly without needing your Client ID:
```bash
python mal_missing_seasons.py <MAL_USERNAME>
```

### Forcing an Update
If the user has watched new shows and you want to pull fresh data from MAL, add the `--force_update` flag (you will need to provide your Client ID again):
```bash
python mal_missing_seasons.py <MAL_USERNAME> <YOUR_CLIENT_ID> --force_update
```

## Understanding the Output

The script generates a text file named `missing_seasons_report_<username>.txt` in the same directory. 

At the top of the file, you will find a "How to Read This Report" preamble explaining the filters. Below that, the script will list out every single combination of filters and the resulting missing seasons for that specific criteria, sorted from newest to oldest.

**Example output snippet:**
```text
--- Filters: [No Dropped] | [No Specials (and above)] | [> 60 Mins] ---
* Fall 2023 - Winter 2024
* Spring 2018
* BEGINNING_OF_TIME - Winter 2005
```

## Notes
* **Ongoing Shows:** The script smartly evaluates ongoing shows by assuming a minimum episode count of `2`. This ensures that a currently airing standard-length episode will pass the `> 24 Mins` filter.
* **Rate Limiting:** The script has a built-in 1-second delay between pagination requests to remain polite to the MyAnimeList API.

## Bonus: Group Missing Seasons Aggregator

Want to find a retro anime to watch with your friends, but need to make sure *nobody* has seen it yet? The repository includes a bonus script: `group_seasons_aggregator.py`.

This script scans the directory for all individual user reports and calculates the **intersection** of missing seasons. It outputs a master list of seasons where literally no one in the group watched a qualifying show.

### How to Use

1. Run the main `mal_missing_seasons.py` script for each friend in your group.
2. Ensure all of their `missing_seasons_report_<username>.txt` files are located in the same directory as the aggregator script.
3. Run the aggregator from your terminal:
   ```bash
   python group_seasons_aggregator.py
   ```
4. Open the newly generated `group_missing_seasons_report.txt` to see your group's shared blind spots!

*Note: You can safely rerun this script anytime you add a new friend's report to the folder. It automatically ignores its own output file.*
