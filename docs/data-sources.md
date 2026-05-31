# Data Sources

All data used in this project comes from open, safe sources.

## Primary

### International Football Results (martj42)

- **URL:** https://github.com/martj42/international_results
- **Use:** Historical match results, goals, dates, tournament context (~49k rows)
- **Local path:** `data/raw/results.csv` (downloaded by `backend/scripts/build_features.py`)

### OpenFootball — World Cup datasets

- **URL:** https://github.com/openfootball/worldcup
- **Use:** World Cup squads, fixtures, and tournament structure
- **Local path:** `data/raw/openfootball/`

## Optional (later)

### API-Football

- **URL:** https://www.api-football.com/
- **Use:** Live injuries, lineups, current team news
- **Note:** Requires API key; not needed for MVP

## Static profiles

Team scouting profiles (style, strengths, key players) live in `data/profiles/` as JSON and are maintained manually for the MVP.
