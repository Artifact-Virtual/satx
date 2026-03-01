# SATx Sovereignty Guide

> **Operational independence from the network. Every feature works offline.**

SATx is designed for sovereign, air-gapped operation. This document specifies exactly what works offline, what requires network access, and how to prepare for full disconnection.

---

## Architecture Philosophy

SATx follows a **"cache everything, compute locally"** model:
- All orbital math (SGP4 propagation) runs locally — zero network dependency
- TLE data is cached locally for offline use
- SatNOGS training data is cached for offline model training
- Ghost Mode can block all outbound connections and clean traces

---

## Feature Matrix: Offline Capability

### ✅ Fully Offline (Zero Network Dependency)

| Feature | Script | Notes |
|---------|--------|-------|
| **Pass Prediction** | `predict_passes.py` | SGP4 propagation is pure math. Uses local TLE files. |
| **Doppler Calculation** | `predict_passes.py` | Computed from orbital elements locally. |
| **Signal Recording** | `start_recording.sh` | Direct SDR hardware → local storage. |
| **Signal Processing** | `process_recording.py` | Local DSP — FFT, demodulation, decoding. |
| **Signal Decoding** | `decoders/*` | All decoders run locally. |
| **Spectrum Scanning** | `spectrum_scanner.py` | Direct SDR hardware scan. |
| **Training Data Prep** | `prepare_training_data.py` | Processes locally cached data. |
| **Ghost Mode** | `ghost_mode.py` | Privacy/stealth — designed to work without network. |
| **Pass Scheduling** | `scheduler.py` | Uses local pass predictions. |
| **Web Dashboard** | `web/` | Local web server, no external dependencies. |

### ⚠️ Network Required for Initial Setup (Then Offline)

| Feature | Script | Degradation Without Network |
|---------|--------|-----------------------------|
| **TLE Download** | `fetch_tles.py` | Uses cached TLEs. TLEs age ~2 weeks before accuracy degrades significantly. |
| **Bulk TLE Cache** | `cache_tles_bulk.py` | Must be run once with network to populate cache. |
| **SatNOGS Data** | `download_satnogs_data.py` | Uses cached observations. No new data, but existing data fully usable. |

### ❌ Network Required (Cannot Function Offline)

| Feature | What It Needs | Workaround |
|---------|---------------|------------|
| **Fresh TLE data** | CelesTrak API | Pre-cache with `cache_tles_bulk.py`. TLEs remain usable for ~2 weeks. |
| **New SatNOGS observations** | SatNOGS API | Pre-download with `download_satnogs_data.py --popular-only`. |
| **SatNOGS data upload** | SatNOGS API | Record locally, upload when network available. |

---

## Preparing for Air-Gapped Deployment

### Step 1: Populate TLE Cache (requires network)

```bash
# Download ALL major TLE catalogs (~40 catalogs, covers everything)
python scripts/cache_tles_bulk.py

# Verify the cache
python scripts/cache_tles_bulk.py --verify

# Check status
python scripts/cache_tles_bulk.py --status
```

This downloads TLEs for:
- Space stations, active satellites, weather, NOAA, GOES
- SARSAT (search & rescue), disaster monitoring
- Communications (Starlink, OneWeb, Iridium, Intelsat, Globalstar, etc.)
- Navigation (GPS, GLONASS, Galileo, BeiDou)
- Amateur radio, CubeSats, science, education
- Military, radar calibration
- Notable debris (Cosmos 2251, Iridium 33)
- Earth resources, Planet Labs, Spire

### Step 2: Cache SatNOGS Data (optional, requires network)

```bash
# Download observations for popular satellites
python scripts/download_satnogs_data.py --popular-only

# Or specific satellites
python scripts/download_satnogs_data.py --satellite 25544  # ISS
python scripts/download_satnogs_data.py --satellite 28654  # NOAA 18

# Check what's cached
python scripts/download_satnogs_data.py --cache-status
```

### Step 3: Verify Offline Readiness

```bash
# Check ghost mode status (includes sovereignty readiness)
python scripts/ghost_mode.py --status

# Test offline TLE loading
python scripts/fetch_tles.py --offline --cache-info

# Test offline pass prediction
python scripts/predict_passes.py --offline
```

### Step 4: Disconnect and Operate

```bash
# Option A: Enable sovereign ghost mode (blocks network + cleans traces)
sudo python scripts/ghost_mode.py --enable --level sovereign

# Option B: Use network namespace isolation (no sudo needed)
./scripts/run_airgapped.sh python scripts/predict_passes.py

# Option C: Physical disconnection
# Just unplug ethernet / disable WiFi. Everything works.
```

---

## TLE Freshness & Accuracy

TLE (Two-Line Element) data degrades over time because orbital elements change:

| TLE Age | Accuracy | Recommendation |
|---------|----------|----------------|
| < 24 hours | Excellent | Ideal for precise tracking |
| 1–3 days | Very Good | Fine for most operations |
| 3–7 days | Good | Adequate for pass prediction |
| 1–2 weeks | Fair | Passes predicted but timing may be off by minutes |
| 2–4 weeks | Poor | Rough predictions only, high-elevation passes still detectable |
| > 1 month | Unreliable | Re-download when network available |

**Best practice:** Refresh TLE cache every few days when network is available. Before going air-gapped, download the freshest set possible.

---

## Offline Cache Locations

```
data/
├── tles/                    # Active TLE files (used by predict_passes.py)
│   ├── all-satellites.tle   # Merged master file
│   ├── active.tle           # Individual catalogs
│   ├── noaa.tle
│   └── ...
├── tle_cache/               # Offline TLE cache (sovereignty backup)
│   ├── all-satellites.tle   # Merged from all cached catalogs
│   ├── active.tle           # Cached individual catalogs
│   ├── stations.tle
│   ├── military.tle
│   ├── starlink.tle
│   ├── cache_meta.txt       # Cache metadata & timestamp
│   └── ...
└── satnogs_cache/           # Cached SatNOGS data
    ├── observations/        # Cached API query results
    └── satellites/          # Cached observation metadata
```

---

## Ghost Mode Levels

| Level | What It Does |
|-------|-------------|
| `standard` | Disables external services, anonymizes station name |
| `high` | + Minimizes logging, clears metadata, removes identifying info |
| `maximum` | + Encryption, anonymous IDs, disables telemetry, memory-only mode |
| `sovereign` | + Blocks outbound connections, cleans network traces, enforces air-gap |

```bash
# Full sovereignty
sudo python scripts/ghost_mode.py --enable --level sovereign

# Clean all traces after operation
python scripts/ghost_mode.py --clean
```

---

## Offline CLI Flags Reference

| Script | Flag | Effect |
|--------|------|--------|
| `fetch_tles.py` | `--offline` | Use only cached TLEs, no network |
| `fetch_tles.py` | `--cache-info` | Show cache age and contents |
| `download_satnogs_data.py` | `--offline` | Use only cached SatNOGS data |
| `download_satnogs_data.py` | `--cache-status` | Show SatNOGS cache status |
| `predict_passes.py` | `--offline` | Use cached TLEs (prediction is always local) |
| `predict_passes.py` | `--tle-file PATH` | Use specific TLE file |
| `cache_tles_bulk.py` | `--status` | Show bulk cache status |
| `cache_tles_bulk.py` | `--verify` | Verify cache integrity |
| `ghost_mode.py` | `--level sovereign` | Full air-gap with network blocking |

---

## Quick Start: 60-Second Air-Gap Prep

```bash
# 1. Cache everything (with network)
python scripts/cache_tles_bulk.py

# 2. Disconnect network

# 3. Predict passes (offline)
python scripts/predict_passes.py --offline

# Done. Full satellite tracking, zero network.
```

---

## Security Notes

- **No phone-home:** SATx never contacts any server unless you explicitly run a download script
- **No analytics:** Zero telemetry, zero tracking, zero external dependencies at runtime
- **Cache is local:** All cached data stays on your machine in `data/`
- **Ghost mode cleans traces:** DNS cache, ARP cache, connection tracking, shell history, Python caches
- **Secure delete:** Ghost mode uses 3-pass overwrite before deletion

---

*SATx sovereignty is not a feature — it's a design principle. The network is a convenience, not a dependency.*
