# TLE Cache — Downloaded 2026-03-01T02:11:00+05:00

Cached from CelesTrak (celestrak.org/NORAD/elements/).

## Catalogs

| File | Group | Satellites | Lines |
|------|-------|-----------|-------|
| active.tle | Active satellites | ~14,544 | 43,632 |
| starlink.tle | SpaceX Starlink | ~5,414 | 16,242 |
| oneweb.tle | OneWeb constellation | ~364 | 1,092 |
| geo.tle | Geostationary | ~318 | 954 |
| resource.tle | Earth resources | ~90 | 270 |
| weather.tle | Weather satellites | ~39 | 117 |
| amateur.tle | Amateur radio sats | ~54 | 162 |
| sarsat.tle | Search & rescue | ~47 | 141 |
| iridium.tle | Iridium NEXT | ~44 | 132 |
| intelsat.tle | Intelsat | ~32 | 96 |
| ses.tle | SES | ~37 | 111 |
| noaa.tle | NOAA | ~12 | 36 |
| gps.tle | GPS constellation | ~17 | 51 |
| galileo.tle | Galileo constellation | ~18 | 54 |
| goes.tle | GOES | ~10 | 30 |
| stations.tle | Space stations (ISS etc) | ~19 | 57 |

## Freshness

TLEs are valid for approximately 1-2 weeks for LEO satellites (SGP4 accuracy degrades with age).
For GEO satellites, TLEs remain useful for months.

**To refresh:** Run `python3 scripts/cache_tles_bulk.py` when internet is available.

## Usage (Offline)

All SATx scripts support `--offline` flag which reads from this cache:
```bash
python3 scripts/fetch_tles.py --offline
python3 scripts/predict_passes.py --offline --lat 33.6844 --lon 73.0479
```
