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
4. **Filter by airline (callsign prefix)** — the current callsign filter is
   exact match only; prefix filtering (e.g. all `AFR*`) needs client-side
   filtering
5. **Export simulation data** — dump each aircraft's trajectory to CSV/JSON
   after import
6. **End-of-simulation statistics** — total flights, average duration, max
   altitude/speed observed
7. **Config file** (YAML/TOML) as an alternative to CLI arguments
8. **Basic ATC** — give an in-flight instruction (heading/altitude change)
   that deviates an aircraft from its real imported trajectory
9. **Compare multiple days**
10. **Basic anomaly detection**
11. **Geographic filtering by area (bounding box)** — new selection mode via
    `Trino.history(bounds=...)`, pending validation of the input format
    (`--min-lat`/`--max-lat`/`--min-lon`/`--max-lon`)
12. **Conflict detection** (vertical/horizontal separation)
13. **Exclusion zones / simplified airspace**
14. **Fast-forward to a specific event**
15. **Local cache of Trino results**
16. **"Dry-run" mode** — preview before import
17. **Weather at flight time** (wind, temperature)
18. **Remaining distance / ETA**
19. **Interactive filtering/sorting in the display**
20. **Aircraft detail view on selection**
21. **Sound/visual notifications on events**
22. **Typed centralized config** (dataclass/Pydantic)
23. **"Replay" vs "live" mode**
24. **Synchronized multi-screen replay**
25. **"Replay bookmarks" system**
26. **Emergency squawk detection** (7500/7600/7700)
27. **Go-around detection**
28. **Diversion detection**
29. **Scheduled vs actual time comparison**
30. **Delay propagation analysis**
31. **Airport connection network graph**
32. **Traffic density heatmap**
33. **Seasonal traffic comparison**
34. **Terrain/elevation map overlay**
35. **Visual day/night cycle in the simulation**
36. **Airspace class overlay**
37. **Squawk code display per aircraft**
38. **Aircraft photo** (Planespotters-like API)
39. **Airline logo/livery**
40. **ML-based delay prediction**
41. **Fuel consumption estimation**
42. **Cross-validation** with FlightRadar24/ADS-B Exchange
43. **Multi-provider data system** (fallback if Trino is unavailable)
44. **Retry/backoff strategy** for Trino queries
45. **Diff between two simulation runs**
46. **REST API** to drive the simulation externally
47. **Mobile companion view**
48. **Voice announcements** (text-to-speech) for events
49. **Console display i18n**
50. **Docker packaging**
51. **One-click installer**
52. **Save/resume session** between two launches
53. **Speed change undo/redo**
54. **Plugin system** for custom renderers
55. **Automated versioning and changelog**
56. **Video/GIF generation** of a simulation
57. **Overview mini-map**

## Attribution

This is a personal, non-commercial research/learning project using flight
and aircraft data from [The OpenSky Network](https://opensky-network.org/).
See [NOTICE.md](NOTICE.md) for the required citation and license scope.
