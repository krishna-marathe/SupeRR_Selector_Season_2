import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

import pandas as pd
import numpy as np
from config.settings import settings

# Load mapping table
mappings = pd.read_csv(settings.MAPPINGS_PATH)
matches = pd.read_csv(settings.MATCHES_PATH)
p11 = pd.read_csv(settings.PLAYING_ELEVEN_PATH)

target_names = [
    "Rashid Khan", "Abdul Samad", "Haider Ali", "Basil Hameed",
    "Muhammad Farooq", "Bashir Ahmad", "Mahendra Singh Dhoni",
    "Piyush Chawla", "Ishant Sharma", "Nathan Bracken", "Virat Kohli",
    "Faf du Plessis", "Wriddhiman Saha", "Rohit Sharma", "Shikhar Dhawan",
    "Dinesh Karthik", "Pradeep Sangwan", "Ravindra Jadeja",
    "Amit Mishra", "Dwayne Bravo"
]

print("--- Resolving Names ---")
resolved = {}
for n in target_names:
    sub = mappings[mappings['player_name'].str.contains(n, case=False, na=False)]
    if len(sub) == 0:
        # try last name or parts
        parts = n.split()
        sub = mappings[mappings['player_name'].str.contains(parts[-1], case=False, na=False)]
    
    unique_p = sub[['player_id', 'player_name']].drop_duplicates()
    print(f"\nQuery: '{n}' -> {len(unique_p)} matches:")
    for _, r in unique_p.iterrows():
        print(f"  ID: {r['player_id']}, Name: {r['player_name']}")
    resolved[n] = unique_p

