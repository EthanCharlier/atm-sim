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
  duration, airline (callsign prefix, e.g. `AFR`, `RYR`)
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
- **End-of-simulation summary**: on stop (natural end or `[ESC]`), choose to
  see a per-aircraft summary table (status, progress, time simulated, max
  altitude/speed observed so far) or quit directly
- **Config file**: a YAML or TOML file (`--config`) can provide defaults for
  any CLI option; explicit CLI arguments always take precedence
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
OPENSKY_USERNAME=...
OPENSKY_PASSWORD=...
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

# From a config file (YAML or TOML), CLI flags override individual values
atm-sim --config config.yaml
atm-sim --config config.yaml --max-flights 5
```

Example `config.yaml`:

```yaml
airport: [LFPG, LFBO]
airline: [AFR]
min_altitude: 1000
max_altitude: 35000
max_flights: 15
speed_factor: 3600
start: "2026-09-01T06:00:00"
end: "2026-09-01T08:00:00"
```

Controls while running: `[SPACE]` pause/resume, `[+/-]` speed, `[ESC]` quit.

On stop, press `[ENTER]` for the simulation summary, or `[ESC]` again to exit
directly.

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
- [x] End-of-simulation statistics
- [x] Config file (YAML/TOML)
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
5. **Basic ATC** — give an in-flight instruction (heading/altitude change)
   that deviates an aircraft from its real imported trajectory
6. **Compare multiple days**
7. **Basic anomaly detection**
8. **Geographic filtering by area (bounding box)** — new selection mode via
   `Trino.history(bounds=...)`, pending validation of the input format
   (`--min-lat`/`--max-lat`/`--min-lon`/`--max-lon`)
9. **Conflict detection** (vertical/horizontal separation)
10. **Exclusion zones / simplified airspace**
11. **Fast-forward to a specific event**
12. **Local cache of Trino results**
13. **"Dry-run" mode** — preview before import
14. **Weather at flight time** (wind, temperature)
15. **Remaining distance / ETA**
16. **Interactive filtering/sorting in the display**
17. **Aircraft detail view on selection**
18. **Sound/visual notifications on events**
19. **Typed centralized config** (dataclass/Pydantic)
20. **"Replay" vs "live" mode**
21. **Synchronized multi-screen replay**
22. **"Replay bookmarks" system**
23. **Emergency squawk detection** (7500/7600/7700)
24. **Go-around detection**
25. **Diversion detection**
26. **Scheduled vs actual time comparison**
27. **Delay propagation analysis**
28. **Airport connection network graph**
29. **Traffic density heatmap**
30. **Seasonal traffic comparison**
31. **Terrain/elevation map overlay**
32. **Visual day/night cycle in the simulation**
33. **Airspace class overlay**
34. **Squawk code display per aircraft**
35. **Aircraft photo** (Planespotters-like API)
36. **Airline logo/livery**
37. **ML-based delay prediction**
38. **Fuel consumption estimation**
39. **Cross-validation** with FlightRadar24/ADS-B Exchange
40. **Multi-provider data system** (fallback if Trino is unavailable)
41. **Retry/backoff strategy** for Trino queries
42. **Diff between two simulation runs**
43. **REST API** to drive the simulation externally
44. **Mobile companion view**
45. **Voice announcements** (text-to-speech) for events
46. **Console display i18n**
47. **Docker packaging**
48. **One-click installer**
49. **Save/resume session** between two launches
50. **Speed change undo/redo**
51. **Plugin system** for custom renderers
52. **Automated versioning and changelog**
53. **Video/GIF generation** of a simulation
54. **Overview mini-map**
