# Setup Guide: From Zero to Satellite Detection Station

A _linear_ 0→100% playbook to go from zero to a full, repeatable satellite detection + tracking + decoding station using only inexpensive home gear:
laptop ± 
RTL-SDR ± 
simple antenna 
plus optional upgrades:
rotator
better SDR
dish

### Config for an Ubuntu/Debian Linux host, and short notes for Windows/macOS where commands differ.

### Overview
RTL-SDR + antenna 
→ install SDR + tracking + decode software → pull TLEs & predict passes 
→ record I/Q with Doppler correction 
→ run detection/decoding pipeline 
→ validate via SatNOGS & crowdsourcing 
→ iterate & scale with ML and better hardware.

---

# HARDWARE 

0. Decide your budget & site:

- Minimum: laptop (any modern laptop), RTL-SDR $25–$40, simple antenna (VHF/UHF whip or DIY QFH) ~$20–$60.
- Nice-to-have: Airspy or SDRplay ($150–$300), small az/el rotator (~~$300+), 70cm/2m Yagi (~~$60–$150), helix for S/S-band or a small dish for Ku (~$200+).

0. Requirements
- RTL-SDR dongle (RTL2832U + R820T2).
- SMA adapter + short USB extension cable.
- Antenna: a dual-band 2m/70cm Yagi or a QFH/Turnstile for LEO; whip antenna for initial testing.
- Optional: cheap USB hub, small external HDD for recordings.

1. Site & mounts:
- Put antenna outside if possible (roof/balcony) clear of obstructions. Secure mount; use coax (RG-58 or better) with SMA to F-type or BNC adapters as needed.

---

# SOFTWARE ENVIRONMENT

Target: Ubuntu 22.04 / Debian or WSL2. Commands below are for Ubuntu.

3. Update system

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git build-essential cmake python3-pip python3-venv
```

4. Install RTL-SDR drivers/tools

```bash
sudo apt install -y librtlsdr0 rtl-sdr rtl-test
# Blacklist kernel driver if needed (some distros): follow rtl-sdr docs
```

Test:

```bash
rtl_test
```

You should see device recognized.

5. Install GNU Radio and GQRX

```bash
sudo apt install -y gnuradio gqrx-sdr gr-osmosdr
```

(If package older, consider PyBOMBS or building from source; for starter, distro packages are fine.)

6. Install GPredict (tracking + Doppler)

```bash
sudo apt install -y gpredict
```

7. Install Python libs for satellite math (Skyfield) and TLE handling

```bash
python3 -m pip install --user skyfield sgp4 numpy scipy matplotlib pyproj
```

8. Install gr-satellites (decoders for many cubesats)

```bash
git clone https://github.com/zerfleddert/gr-satellites.git
cd gr-satellites
# follow README: usually requires grc blocks; if using distro gnuradio, try:
sudo python3 -m pip install --user -r requirements.txt
# Then run decoders via GNU Radio or the provided scripts
```

9. Install SatNOGS client (optional but recommended)

```bash
python3 -m pip install --user satnogs-client
```

Create an account at satnogs.org (do this via web) and follow their station setup docs if you plan to join the network.

10. Other utilities

```bash
sudo apt install -y sox ffmpeg python3-pandas python3-matplotlib
python3 -m pip install --user librosa tensorflow torch torchvision scikit-learn
```

(Install TensorFlow/PyTorch only if you plan to run ML locally; can be skipped initially.)

Windows/macOS notes:

- Use Zadig to install RTL-SDR drivers on Windows; use SDR# for quick tests. GPredict has Windows builds. For heavy lifting, Linux is recommended.

---

# SATELLITE CATALOG & PASS PREDICTION

11. Acquire TLEs (Two-Line Elements)

- Use CelesTrak TLE feeds (download tle files). Manually: [https://celestrak.org/NORAD/elements/](https://celestrak.org/NORAD/elements/) (use tle-new.txt or specific groups: cubesat.txt, stations.txt). (In practice open the site and download the file.)

12. Basic Skyfield pass script (save as `passes.py`)

```python
from skyfield.api import load, wgs84, EarthSatellite, Topos
ts = load.timescale()
lines = open('tle-new.txt').read().splitlines()
# parse first sat for example: adjust to parse many
sat = EarthSatellite(lines[0], lines[1], lines[2], ts)  # use proper indices
# build observer:
observer = wgs84.latlon(24.86, 67.01)  # replace with your lat,lon
t0 = ts.utc(2025, 10, 19)
t1 = ts.utc(2025, 10, 20)
# use skyfield to find rise/set/transit etc (see Skyfield examples)
```

(Use Skyfield docs for full pass computations; GPredict can do it live if you prefer GUI.)

13. Install Space-Track account (optional): if you want official catalog via API, sign up at spacetrack.org (this may require credentials). CelesTrak is enough for hobby use.

---

# SDR RECORDING & DOPPLER

14. Confirm reception: tune to NOAA weather (137.1 MHz LEO) or a known amateur satellite and verify you hear a signal:

- Use GQRX or `rtl_fm`:

```bash
rtl_fm -f 137912500 -s 60k -g 49 - | sox -t raw -r 60k -e signed -b 16 -c 1 - -t wav -
# or open in GQRX and visualize waterfall
```

15. Prepare to record I/Q during a pass. Example `rtl_sdr` command:

```bash
# center 435 MHz, sample rate 2.4 Msps, record 2 minutes
rtl_sdr -f 435000000 -s 2400000 -g 49 -n $((120*2400000)) pass_iq.iq
```

Better: run `rtl_tcp` and connect via GNU Radio so you can do doppler correction in real time.

16. Doppler correction: use GPredict to compute Doppler and feed to `rtl_fm` or `rtl_tcp`.

- GPredict can be configured to output frequency updates to `rtl_tcp` or to a script; configure GPredict’s audio/doppler control settings (see GPredict docs). For a simple approach, compute predicted frequency offset from Skyfield and adjust `rtl_sdr` center frequency manually before recording.

---

# SIGNAL DETECTION & DECODING 

17. Offline workflow (I/Q → spectrogram → candidates)

- Convert raw I/Q to WAV/spectrogram using Python (librosa/matplotlib) or `sox`/`ffmpeg`. Example approach:
    - Use GNU Radio to make a short bandpass around expected carrier → save audio.
    - Use Python to compute STFT and visualize.

18. Try existing decoders first:

- `gr-satellites` has a set of decoders for cubesats (AO-7 style, Funky FM, various AX.25 beacons). Feed your recorded I/Q or live TCP stream into the appropriate GNU Radio flowgraph and see if the decoder locks on.
- `multimon-ng` or `direwolf` can decode AFSK/AX.25 or APRS.

19. Manual signal analysis steps:

- Look for narrow, repeated carrier lines in spectrogram → these often indicate telemetry frames.
- If you find narrowband bursts, try standard demod: BPSK/QPSK for telemetry; AFSK/GMSK for amateur. Use `grc` flowgraphs: frequency translation → lowpass → demod → decoder.

20. Validate & log:

- For each candidate detection, note: UTC time, NORAD ID, center frequency, az/el, SNR estimate, sample file. Upload to SatNOGS or your private log.

---

# CROWD & VALIDATION

21. SatNOGS integration:

- Create account at satnogs.org. Use the API to query observations for a given NORAD ID. If the object has recent observations with RF detections, good sign.
- Optionally register a station (satnogs-client) so you can automate recordings and upload them to the network.

22. Community reporting:

- Use AMSAT forums, r/RTLSDR, and SatNOGS community to post unknown detections. Provide sample I/Q and spectrograms. The community can often identify modulation & satellite quickly.

---

# ML PIPELINE

23. Build a small detection model:

- Corpus: gather labeled spectrograms (NOAA, AX.25, known cubesats, noise). SatNOGS exports observations you can use as training data.
- Small CNN: input 256×256 spectrogram snippets; binary classify "signal vs noise" or multi-class for known modes.
- Training: use TensorFlow or PyTorch; train on laptop or Google Colab for quicker iterations.
- Use model to scan recorded I/Q spectrograms and output candidate timestamps/freqs.

24. Automation:

- Build a scheduler that:
    - pulls TLEs,
    - predicts passes,
    - schedules SatNOGS or local observations,
    - runs recording,
    - runs ML detector,
    - attempts demod with known decoders,
    - creates reports & notifies you (email/Discord).

---

# MAINTENANCE, ETHICS & TROUBLESHOOTING

25. Troubleshooting tips:

- No signal: check antenna orientation, connectors, gain, and sample rate. Try NOAA pass to confirm basic setup.
- Bad samples: lower sample rate, increase gain carefully (avoid clipping).
- Decoders fail: try finer frequency offsets; many modulations need exact center freq. Try demod with narrower filters.

26. Scaling & upgrades:

- Add a rotator + GPredict integration for better SNR.
- Upgrade to Airspy/SDRplay for better dynamic range.
- Add a small dish for GEO/C-band/KU if you plan to listen to geostationary satellites (requires dish + LNB + LNAs).

---

# Quick-testing checklist

- [ ] `rtl_test` shows device detected.
- [ ] GQRX shows waterfall on NOAA freq; you can record audio.
- [ ] GPredict loaded with TLEs and shows a visible pass for ISS or NOAA.
- [ ] Record a 2-minute I/Q file during a pass.
- [ ] Run `gr-satellites` decoder against the recording and try known decoders.
- [ ] Upload a sample to SatNOGS/AMSAT or a forum for identification.

---

# Commands Summary

Install essentials:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git build-essential cmake python3-pip librtlsdr0 rtl-sdr rtl-test gnuradio gqrx-sdr gr-osmosdr gpredict sox ffmpeg
python3 -m pip install --user skyfield sgp4 numpy scipy matplotlib librosa satnogs-client
```

Record I/Q (example):

```bash
rtl_sdr -f 137912500 -s 2400000 -g 49 -n $((120*2400000)) noaa_pass.iq
```

Convert I/Q to WAV (example using GNU Radio or custom script) — see gr-satellites example flows for best path.

---

This plan gets us from nothing to an automated station that:

- finds every passing satellite above your horizon,
- records I/Q with doppler correction,
- detects narrowband/transmission candidates,
- decodes with community decoders or ML,
- validates via SatNOGS/AMSAT.

#### Next Steps

- produce the exact `passes.py` Skyfield script that lists the next 48 hours of passes for Karachi coordinates, OR
- give you a ready-to-run starter GNURadio flowgraph for a popular cubesat beacon, OR
- produce a minimal CNN training script + dataset download plan to run detection on your laptop.

---
# 2 Part Hardware & Software Setup
---

# PART 1 — HARDWARE

**Philosophy:** Start with _what you already have for free_, then add the single cheapest radio front-end and a DIY antenna. That setup will let you detect and record most LEO satellites (cubesats, weather sats, many beacons).

## Free / already-available items

- **Laptop / Desktop** — any modern laptop (Windows/macOS/Linux). This is your SDR host and AI/processing machine.
- **Smartphone** — for quick visual tracking, remote control, logging photos, and running GPredict remote GUIs or web dashboards.
- **Existing home network / Wi-Fi** — to serve data, run `rtl_tcp`, and upload to SatNOGS if you join the network.  
    _(No cost; you already have these.)_

## Cheapest add-on items (buy these; total ≈ **$20–$50**)

1. **RTL-SDR dongle (RTL2832U + R820T2)** — the canonical cheap SDR for hobbyists.
    
    - Cheapest sources: eBay listings can be as low as **~$18**; reliable sellers / RTL-SDR Blog or NooElec bundles ~**$34–$44**. Pick one with SMA connector (or adapt).
    - Why: covers ~100 kHz → ~1.7 GHz; perfectly fine for LEO downlinks (VHF/UHF) and many beacon bands.
2. **Antenna — DIY cheapest workable option**
    
    - **Turnstile** or **QFH (Quadrifilar Helix)** DIY build for LEO (137–450 MHz range). Materials (wire, PVC tubes, coax) ≈ **$10–$30** if you build it yourself. Plenty of free step-by-step guides online.
    - Alternative cheapest: a telescopic dual-band whip included in many RTL-SDR bundles will work for initial testing (often bundled).
3. **Coax cable + adapters** — cheap RG-58 / SMA/F-type adapters to connect dongle to antenna; ~**$5–$15**.
    
4. **Optional (but cheap & very helpful):**
    
    - **USB extension cable** (to place SDR outdoors / away from noise) — $3–$8.
    - **Small external HDD or big USB stick** for recordings — $20+ (optional).

**Total cheapest-outlay:** _From practically $20 (used eBay dongle + whip) to ~$60 (new RTL-SDR bundle + simple DIY antenna)_ depending on whether you buy used/new and how minimal you go. (Sources: RTL-SDR blog / Amazon / eBay product pages).

## If you want one-step upgrades later 

- **Airspy / SDRplay** — better dynamic range (~$150–$300). Useful if you upgrade.
- **Az/El rotator + small Yagi** — for better SNR on passes (~$300+).

---

# PART 2 — SOFTWARE / REPO STRUCTURE

**Philosophy:** create a single Git repo that holds code, orchestrates recordings, runs detection/decoding, stores recordings and metadata, and provides a simple pipeline you can run locally or on a small server. I give a concrete tree, key files, and the minimal contents (commands, snippets). Use Docker for reproducibility where helpful.

## Top-level repo name

`sat-finder` (you can rename)

## Command to create repo

```bash
git init sat-finder
cd sat-finder
```

---

## Full repo tree

```
sat-finder/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ docker-compose.yml
├─ requirements.txt
├─ scripts/
│  ├─ install_tools.sh
│  ├─ fetch_tles.py
│  ├─ predict_passes.py
│  ├─ start_recording.sh
│  └─ process_recording.py
├─ services/
│  ├─ sdr/
│  │  └─ Dockerfile        # optional: rtl_tcp + gnuradio container
│  └─ ml/
│     └─ Dockerfile        # optional: model inference container
├─ configs/
│  ├─ station.ini          # lat/lon, antenna gain, RTL device id
│  ├─ gpredict.conf
│  └─ satnogs-api.json     # keys if you use SatNOGS (optional)
├─ decoders/
│  ├─ grc_flowgraphs/      # optional: saved GNU Radio .grc files
│  ├─ gr-satellites/       # submodule or pointer to the decoder collection
│  └─ multimon-ng-configs/
├─ models/
│  ├─ model_v1/            # saved ML model files (TF/PyTorch)
│  └─ training_data/       # (not checked in) pointers/manifest
├─ recordings/
│  └─ YYYYMMDD/            # place recorded IQ/WAV files here (gitignored)
├─ logs/
│  └─ pipeline.log
├─ web/
│  └─ dashboard/           # optional simple UI to view candidates
└─ docs/
   ├─ quick_start.md
   ├─ antenna_build.md     # DIY turnstile/QFH instructions (links)
   └─ satnogs_integration.md
```

**Notes:** `recordings/` and `models/training_data/` should be in `.gitignore` (large binaries).

---

## Key files & minimal content

### `requirements.txt`

```
numpy
scipy
matplotlib
skyfield
sgp4
python-dateutil
pandas
pydantic
librosa
soxbindings
grpcio
# optional for ML:
torch
tensorflow
scikit-learn
satnogs-client
```

(Use `pip install -r requirements.txt`.)

Cite core libs: **Skyfield** for orbital math (install docs).

### `scripts/fetch_tles.py`

```python
# fetch_tles.py
import requests
open('tle-new.txt','wb').write(requests.get('https://celestrak.org/NORAD/elements/tle-new.txt').content)
print('TLEs updated')
```

### `scripts/predict_passes.py` (skyfield)

```python
# predict_passes.py
from skyfield.api import load, wgs84, EarthSatellite
# loads and basic pass listing for Karachi coords
ts = load.timescale()
lines = open('tle-new.txt').read().splitlines()
# parse every 3 lines (name,line1,line2)
# compute next passes for each sat and print ones with upcoming passes
# (detailed script in repo; use Skyfield docs)
```

(Reference Skyfield docs for exact usage.)

### `scripts/start_recording.sh`

```bash
#!/usr/bin/env bash
# start_recording.sh NORAD_ID CENTER_FREQ SAMPLE_RATE DURATION_SEC OUTFILE
NORAD=$1; FREQ=$2; SR=$3; DUR=$4; OUT=$5
# Example with rtl_sdr
rtl_sdr -f "$FREQ" -s "$SR" -g 49 -n $((DUR*SR)) "$OUT"
# Add metadata log
echo "$(date -u) $NORAD $FREQ $SR $OUT" >> ../logs/pipeline.log
```

(For Doppler-corrected live tuning, run rtl_tcp and feed frequency updates from GPredict or a doppler-calc script.)

### `scripts/process_recording.py`

- Converts IQ → spectrogram (librosa / matplotlib)
- Runs ML detector on spectrogram tiles (if model present)
- If candidate found, runs demod attempts using `gr-satellites` CLI or `multimon-ng` wrappers
- Outputs `logs/candidates.csv` with fields: norad,utc,freq,snr,mode,decoded_text,path_to_raw

(You’ll put a real implementation here; structure is the contract.)

---

## Integration with external projects (use as git submodules or point to them)

- **gr-satellites** — GNU Radio decoders for many amateur satellites (add as submodule or install separately).
- **SatNOGS client** — integration to schedule/submit observations or query their DB. Add install/config snippet in `scripts/install_tools.sh`.
- **GPredict** — run locally (not in repo) for live tracking; repo includes `configs/gpredict.conf`. (GPredict download page referenced.)

---

## Optional Docker Compose

`docker-compose.yml` to run `rtl_tcp` container + `processor` container:

```yaml
version: "3.8"
services:
  rtl:
    build: ./services/sdr
    devices:
      - "/dev/bus/usb:/dev/bus/usb"
    ports:
      - "1234:1234"
  processor:
    build: ./services/ml
    volumes:
      - ./recordings:/app/recordings
      - ./logs:/app/logs
    depends_on:
      - rtl
```

(Use this if you want reproducible containers; otherwise run natively.)

---

## Minimal README.md

- Purpose: detect + identify transmitting satellites overhead.
- Quick start:
    1. `pip install -r requirements.txt`
    2. Plug RTL-SDR, run `scripts/fetch_tles.py`
    3. Use `scripts/predict_passes.py` to list near passes for your location
    4. Run `scripts/start_recording.sh <NORAD> <FREQ> <SR> <DUR> recordings/yyy.iq`
    5. Run `scripts/process_recording.py recordings/yyy.iq`
- Links: Skyfield, GPredict, gr-satellites, SatNOGS.

---

## Notes on ML detector

- **Input:** spectrogram tiles (e.g., 256×256 px) made from IQ recordings.
- **Model:** small CNN (binary signal/noise) or multi-class (AX.25, AFSK, BPSK, etc.). Start with pre-labeled SatNOGS audio/spectrograms as training data (SatNOGS DB is public). Process done in `models/` and inference in `scripts/process_recording.py`. (Research shows ML helps find faint beacons.)

---

# Quick mapping to the tools

- **RTL-SDR dongle** — buy from RTL-SDR Blog / NooElec / eBay (cheap variants).
- **GPredict** — download and configure for Doppler + rotator control.
- **gr-satellites & satnogs-client** — install or add as submodule (decoders and network interaction).
- **Skyfield** — for accurate pass predictions and sunlight/visibility checks.

---

# Final checklist

1. Buy a cheap **RTL-SDR** (or use existing USB TV tuner).
2. Build a **turnstile/QFH** from free online guides and connect it.
3. `git clone` the `sat-finder` repo skeleton (create locally from tree above).
4. `pip install -r requirements.txt` and run `scripts/fetch_tles.py`.
5. Use `gpredict` + `start_recording.sh` to capture a test NOAA / ISS pass and run `process_recording.py`.
6. Post any unknown detection to SatNOGS/AMSAT for rapid community identification.

---


## Next

- Create the **actual skeleton repo** (fill README, requirements.txt, empty scripts) and give you a ZIP / git bundle to download; **or**
- Provide ready-to-run `predict_passes.py` tailored to Karachi (latitude/longitude) so you can immediately predict upcoming passes.

