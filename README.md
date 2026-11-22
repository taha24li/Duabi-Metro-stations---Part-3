# Space, Budget and the Dubai Metro

CS333 Intro to Data Visualization, Part 3 (Group 7).

**Live visualization:** https://taha24li.github.io/Duabi-Metro-stations---Part-3/

An interactive Vega-Lite visualization of existing 2-bedroom flat sales in Dubai
(Jan 2024 to Aug 2026, DLD 10% sample). It asks: given a budget and a distance to
the metro, how many sales are big enough, where are they, and what is around the station?

## Views (linked)
1. Heatmap: budget ceiling x distance band; colour = share of sales meeting the size target.
2. Map: areas (circles = sales meeting budget and size), metro stations, nearby recorded venues.
3. Floor-space chart: median and middle 50% of floor area per area, against the size target.
4. Scatterplot: price against floor area for every sale in the selected cell.

## Files
- `index.html`: the page. It embeds the Vega-Lite specification with vega-embed.
- `vegalite_spec.json`: the same Vega-Lite specification as a stand-alone file.
- `area_metro.json`: each area's nearest station and straight-line distance from the area centre.
- `stations.json`: stations with their current names.
- `station_venues.json`: venues within 1 km of their nearest station.
- `area_venues.json`: venues within 1.5 km of the centre of each area more than 2 km from a station.
- `prep_area_metro.py`: script that derives `area_metro.json` from the course files.

## Data and data quality
- Sources: DLD transactions (10% sample), community boundaries, metro stations and
  venues, all from the course repository.
- Sales kept: existing 2-bedroom flats, AED 1,000 to 100,000 per m², floor area 30 to 400 m².
- Counts come from the 10% sample and are not scaled up.
- Distances are straight lines from the area centre, so they are approximate.
- Venues are circa 2020 and capped at 100 per community, so coverage is uneven.
