# ATM Simulation — Ideas & Roadmap

Local ATM (Air Traffic Management) simulation built from real historical
flight data (OpenSky Network / Trino). Started as a learning project to
understand ATM concepts, simulation engines, and 4D trajectories.

## Current state

- Python 3.14, src-layout package (`atm_sim`)
- Entities: `AircraftEntity`, `TrajectoryEntity`, `SimClockEntity`,
  `SimulationEngineEntity`, `AirportEntity`
- Data source: OpenSky Trino (`pyopensky`) — real position, speed,
  vertical rate, on_ground per point
- Import modes: by airport (departure OR arrival), by origin(s),
  by destination(s), or by precise routes (origin × destination)
- Quota system: flights distributed evenly across query specs, remainder
  assigned randomly
- Simulation: global timeline (aircraft can start already in flight or
  finish after the simulated window ends), rewind support, 7 fixed
  speed levels, pause/resume, live speed adjustment
- Console renderer: sorted table, colored status, origin/destination
  per aircraft, throttled refresh rate
- Config: `.env` for OpenSky Trino credentials, CLI via `argparse`

## Ideas for next steps

### 1. Visual interface
Still console-only. Original plan was a web map (Leaflet) fed by a
small FastAPI + WebSocket server exposing simulation state in real
time. Biggest remaining piece of the original project vision.

### 2. Persistence (SQLite)
Save an imported fleet to replay it later without re-querying Trino.
Useful for comparing runs or sharing a scenario.

### 3. Unit tests
Still zero tests. `NavigationService` and `TrajectoryEntity` are pure
logic (no I/O) and the easiest, most valuable candidates to cover first
now that their behavior (interpolation, binary search, bounds, rewind)
has stabilized.

### 4. Filter by callsign / airline
`trino.flightlist()` also accepts `callsign=`. Could become a 4th
search mode (e.g. all Air France flights in a period), reusing the
existing quota logic.

### 5. Export simulation data
Dump each aircraft's trajectory to CSV/JSON after import — useful for
offline analysis or reuse in another tool (spreadsheet, external
visualization).

### 6. End-of-simulation statistics
On COMPLETE, show a summary: total flights, average duration, max
altitude/speed observed, etc. Small addition that makes use of data
already collected.

### 7. Config file instead of CLI-only
If commands get long (multiple airports, routes, options), an optional
`config.yaml`/`config.toml` could replace part of the `--` arguments.

### 8. Basic ATC — first interactive brick
Give an in-flight instruction to an aircraft (heading/altitude change)
that deviates it from its real imported trajectory. Introduces active
control, closer to the original ATM goal of the project.

## Known limitations (by design, not bugs)

- ADS-B coverage gaps mean some aircraft appear already airborne or
  disappear before landing (data limitation, not a simulation bug)
- `estdepartureairport`/`estarrivalairport` (`departure`/`arrival` in
  the returned DataFrame) are OpenSky estimates and can be missing —
  flights without both are filtered out
- Ground speed / vertical rate are real measured values from Trino
  (not derived), but interpolated linearly between two ADS-B points
- No SID/STAR, no airway network, no real ATC procedures — trajectories
  are replayed as observed, not computed from a flight plan

## Other

1. Interface visuelle (carte web Leaflet)
2. Persistance (SQLite)
3. Tests unitaires
4. Filtre par callsign/compagnie
5. Export de la simulation (CSV/JSON)
6. Statistiques de fin de simulation
7. Configuration via fichier (YAML/TOML)
8. ATC basique — instructions en vol
9. Comparer plusieurs jours
10. Détection d'anomalies simples
11. Filtrage géographique par zone (bounding box)
12. Détection de conflit (séparation verticale/horizontale)
13. Zones d'exclusion / airspace simplifié
14. Avance rapide jusqu'à un événement précis
15. Cache local des résultats Trino
16. Mode "dry-run" / preview avant import
17. Journal de session (log fichier)
18. Météo au moment du vol (vent, température)
19. Type d'avion (base d'immatriculations)
20. Distance restante / ETA
21. Filtrage/tri interactif dans l'affichage
22. Détail d'un avion sur sélection
23. Notifications sonores/visuelles sur événement
24. Config centralisée typée (dataclass/Pydantic)
25. Mode "replay" vs "live"
26. CI basique (GitHub Actions)
27. Rejeu synchronisé multi-écran
28. Système de "replay bookmarks"
29. Détection squawk d'urgence (7500/7600/7700)
30. Détection de go-around
31. Détection de déroutement (diversion)
32. Comparaison horaire prévu vs réel
33. Analyse de propagation de retard
34. Graphe réseau des connexions entre aéroports
35. Heatmap de densité de trafic
36. Comparaison saisonnière du trafic
37. Overlay carte de terrain/élévation
38. Cycle jour/nuit visuel dans la simulation
39. Overlay classes d'espace aérien
40. Affichage code squawk par avion
41. Photo de l'avion (API type Planespotters)
42. Logo/livrée compagnie aérienne
43. Prédiction de retard par ML
44. Estimation de consommation carburant
45. Validation croisée avec FlightRadar24/ADS-B Exchange
46. Système multi-fournisseurs de données (fallback si Trino indisponible)
47. Stratégie de retry/backoff pour les requêtes Trino
48. Diff entre deux exécutions de simulation
49. API REST pour piloter la simulation depuis l'extérieur
50. Vue compagnon mobile
51. Annonces vocales (text-to-speech) des événements
52. Internationalisation (i18n) de l'affichage console
53. Packaging Docker
54. Installeur one-click
55. Sauvegarde/reprise de session entre deux lancements
56. Undo/redo des changements de vitesse
57. Système de plugins pour renderers custom
58. Versioning et changelog automatisés
59. Génération de vidéo/GIF d'une simulation
60. Mini-carte de vue d'ensemble (overview map)
