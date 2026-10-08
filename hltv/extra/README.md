# hltv/extra

Data that fills gaps in the scraper's files without touching them. The scraper never writes here.

- `event-matches.json`: per event id, HLTV match ids (`events`), plus a summary of each match (`matches`: time, BO, teams, score, winner, map scores, line-up nicks). From ali's Apify scrape of 2026-10-08; rows that HLTV filed under a different event were left out. The app adds these ids to an event's matches when it fills the bracket.
- `players.json`: HLTV player id → nick, real name, team, age, Rating 3.0 and the seven skill ratings (69 players of the top teams).
- `rankings.json`: HLTV world top 30 with points, change and line-up nicks.
