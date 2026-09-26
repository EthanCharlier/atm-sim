# ATM Simulation

Local Air Traffic Management (ATM) simulation replaying real flights from
historical OpenSky Network data (via Trino). A learning project to explore
ATM concepts, simulation engines, and 4D trajectories.

## Table of contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Code quality](#code-quality)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

## Features

- **Data source**: OpenSky Trino (`pyopensky`) — real position, speed,
  vertical rate and on-ground status, point by point
- **Flight selection modes** (mutually exclusive, one at a time):
  - by airport (departure OR arrival) — `--airport`
  - by departure airport(s) — `--origin`
  - by arrival airport(s) — `--destination`
  - by precise route (origin × destination) — `--origin` + `--destination`
  - by callsign — `--callsign`
  - by icao24 (transponder address) — `--icao24`
- **Post-selection filters**: min/max altitude, min ground speed, min flight
  duration
- **Aircraft type**: automatically enriched via OpenSky's public aircraft
  database (registration, manufacturer, model, typecode), cached locally
  after the first download
- **Quotas**: flights distributed evenly across query specs, the remainder
  assigned randomly
- **Simulation engine**: global timeline (an aircraft can start already in
  flight or finish after the simulated window ends), 7 fixed speed levels,
  pause/resume, live speed adjustment
- **Console renderer**: table sorted by status, colored states, throttled
  refresh rate
- **Logging**: redirected to a file (`atm-sim.log`), console reserved for
  the live render

## Installation

```bash
git clone https://github.com/EthanCharlier/atm-sim.git
cd atm-sim
pip install -e ".[dev]"
```

Set your OpenSky Trino credentials in a `.env` file at the project root:

```
TRINO_USERNAME=...
TRINO_PASSWORD=...
```

## Usage

```bash
atm-sim --help
```

Examples:

```bash
# All traffic at an airport over a period
atm-sim --airport LFBO --start 2026-09-01T06:00:00 --end 2026-09-01T08:00:00

# Departures only
atm-sim --origin LFBO --start 2026-09-01T06:00:00 --end 2026-09-01T08:00:00

# A precise route
atm-sim --origin LFBO --destination LFPO --start 2026-09-01T06:00:00 --end 2026-09-01T08:00:00

# A specific flight by callsign
atm-sim --callsign AFR123 --start 2026-09-01T06:00:00 --end 2026-09-01T08:00:00

# Combined filters
atm-sim --airport LFBO --min-altitude 1000 --max-altitude 35000 --min-speed 100 --min-duration 300

# Only Air France flights at an airport
atm-sim --airport LFPG --airline AFR --start 2026-09-01T06:00:00 --end 2026-09-01T08:00:00
```

Controls while running: `[SPACE]` pause/resume, `[+/-]` speed, `[ESC]` quit.

## Architecture

`src-layout` package, split into layers:

```
src/atm_sim/
├── entities/     # domain objects (AircraftEntity, TrajectoryEntity, ClockEntity, ...)
├── services/     # application logic (OpenSkyService, SimulationService, ...)
├── enums/        # statuses (AircraftStatusEnum, SimulationStatusEnum)
├── constants/    # conversion factors, default values, CLI config
├── exceptions/   # dedicated domain exceptions
└── main.py       # CLI entry point (argparse)
```

## Code quality

- `ruff` (`select = ["ALL"]`, no rule ignored without a scoped justification)
- `mypy --strict`
- SonarCloud (analysis via GitHub Actions on every push/PR)

```bash
ruff check src
ruff format src
mypy src --strict
```

## Known limitations

These are data limitations, not bugs:

- ADS-B coverage gaps: some aircraft appear already airborne or disappear
  before landing
- `departure`/`arrival` are OpenSky estimates and can be missing — flights
  without both are filtered out
- Ground speed / vertical rate are real measured values, but linearly
  interpolated between two ADS-B points
- No SID/STAR, no airway network, no real ATC procedures — trajectories are
  replayed as observed, not computed from a flight plan

## Roadmap

### Done

- [x] Filter by callsign / icao24
- [x] Filter by airline (callsign prefix)
- [x] Aircraft type (OpenSky aircraft database)
- [x] Basic CI (SonarCloud + GitHub Actions)
- [x] Logs redirected to a file

### Pending / to do

1. **Visual interface** — a web map (Leaflet) fed by a small FastAPI +
   WebSocket server exposing simulation state in real time
2. **Persistence (SQLite)** — save an imported fleet to replay it later
   without re-querying Trino
3. **Unit tests** — `NavigationService` and `TrajectoryEntity` are the
   simplest, most valuable candidates to cover first (also blocks the
   SonarCloud Quality Gate, currently at 0% coverage)
4. **Export simulation data** — dump each aircraft's trajectory to CSV/JSON
   after import
5. **End-of-simulation statistics** — total flights, average duration, max
   altitude/speed observed
6. **Config file** (YAML/TOML) as an alternative to CLI arguments
7. **Basic ATC** — give an in-flight instruction (heading/altitude change)
   that deviates an aircraft from its real imported trajectory
8. **Compare multiple days**
9. **Basic anomaly detection**
10. **Geographic filtering by area (bounding box)** — new selection mode via
    `Trino.history(bounds=...)`, pending validation of the input format
    (`--min-lat`/`--max-lat`/`--min-lon`/`--max-lon`)
11. **Conflict detection** (vertical/horizontal separation)
12. **Exclusion zones / simplified airspace**
13. **Fast-forward to a specific event**
14. **Local cache of Trino results**
15. **"Dry-run" mode** — preview before import
16. **Weather at flight time** (wind, temperature)
17. **Remaining distance / ETA**
18. **Interactive filtering/sorting in the display**
19. **Aircraft detail view on selection**
20. **Sound/visual notifications on events**
21. **Typed centralized config** (dataclass/Pydantic)
22. **"Replay" vs "live" mode**
23. **Synchronized multi-screen replay**
24. **"Replay bookmarks" system**
25. **Emergency squawk detection** (7500/7600/7700)
26. **Go-around detection**
27. **Diversion detection**
28. **Scheduled vs actual time comparison**
29. **Delay propagation analysis**
30. **Airport connection network graph**
31. **Traffic density heatmap**
32. **Seasonal traffic comparison**
33. **Terrain/elevation map overlay**
34. **Visual day/night cycle in the simulation**
35. **Airspace class overlay**
36. **Squawk code display per aircraft**
37. **Aircraft photo** (Planespotters-like API)
38. **Airline logo/livery**
39. **ML-based delay prediction**
40. **Fuel consumption estimation**
41. **Cross-validation** with FlightRadar24/ADS-B Exchange
42. **Multi-provider data system** (fallback if Trino is unavailable)
43. **Retry/backoff strategy** for Trino queries
44. **Diff between two simulation runs**
45. **REST API** to drive the simulation externally
46. **Mobile companion view**
47. **Voice announcements** (text-to-speech) for events
48. **Console display i18n**
49. **Docker packaging**
50. **One-click installer**
51. **Save/resume session** between two launches
52. **Speed change undo/redo**
53. **Plugin system** for custom renderers
54. **Automated versioning and changelog**
55. **Video/GIF generation** of a simulation
56. **Overview mini-map**

## Attribution

This is a personal, non-commercial research/learning project using flight
and aircraft data from [The OpenSky Network](https://opensky-network.org/).
See [NOTICE.md](NOTICE.md) for the required citation and license scope.
