# SATx — A Practical Guide to Detecting & Decoding "Forgotten" Satellites

This is my compact, zero-fluff plan for detecting every satellite that passes over my horizon, tracking them precisely, scanning for downlinks, and prioritizing candidates that appear "unused but transmitting." I've outlined the exact tools, quick commands, AI/automation ideas, and references I use. My focus is on legal, ethical, and repeatable steps. Transmission capabilities may be added as an optional module with proper authorization.

**My Core Resources:** I primarily use CelesTrak for TLEs, SatNOGS for crowdsourced observations and its API, Skyfield/SGP4 for pass predictions, GPredict for live tracking, and an RTL-SDR with `gr-satellites` or GNU Radio for decoding.

---

## 1 — Overall Architecture (High Level)

My approach follows these high-level steps:

1.  **Catalog Acquisition:** My first step is to pull the current catalog and TLEs for all known objects, primarily from CelesTrak or Space-Track.
2.  **Pass Prediction:** I then compute which objects will pass over my horizon using SGP4/Skyfield.
3.  **Scheduling & Observation:** For each predicted pass, I automatically record wideband I/Q data using my RTL-SDR (or other radio) and log essential metadata (time, azimuth/elevation, expected Doppler).
4.  **Signal Detection:** I analyze the recorded I/Q data with signal-detection machine learning to extract candidate narrowband signals.
5.  **Classification & Decoding:** I match these candidate signals against known protocols (e.g., AX.25, AFSK, GMSK, BPSK, QPSK, NOAA APT) using `gr-satellites`, `multimon-ng`, or custom GNU Radio flowgraphs.
6.  **Cross-referencing:** I consult SatNOGS and community logs. If others have observed the same NORAD ID with a matching signal, it provides strong evidence that the satellite is alive and transmitting. I use the SatNOGS API to retrieve these observations.
7.  **Prioritization:** Finally, I rank targets by the probability that they are: (a) powered, (b) low-importance/potentially re-usable (e.g., old science, amateur, CubeSats), and (c) transmitting unencrypted telemetry.

---

## 2 — Tools & Hardware (What I Actually Need)

For my setup, I've found the following minimum tools and hardware to be both cheap and powerful:

**Minimum (Cheap & Powerful):**

*   **Laptop:** Linux is highly recommended for its flexibility.
*   **SDR Dongle:** An RTL-SDR dongle (RTL2832U) is a great start, but I might upgrade to an Airspy or HackRF for better performance.
*   **Antenna:**
    *   For LEO satellites, I use a VHF/UHF dual-band antenna (QFH, Turnstile, or Yagi).
    *   For S-band, a small helical antenna works.
    *   Dishes for Ku/C-band are generally not required for most LEO observations.
    *   *Community Note:* A dual-band 2m/70cm Yagi is effective for many CubeSats.

**Optional Enhancements:**

*   **Az/El Rotator:** A small az/el rotator (Yaesu/ICOM/Arduino controllable) can significantly improve signal capture by precisely tracking satellites. GPredict can control these rotators.

**Software (My Installation List):**

*   `python3`, `pip`
*   `skyfield` (or `sgp4`) — essential for pass predictions.
*   `gpredict` — for live pass tracking and rotator control.
*   `rtl_sdr`, `rtl_tcp`, `GQRX` or `SDR#` / `gqrx` — for recording I/Q data.
*   `satnogs-client` (if I plan to submit/coordinate observations or use local station tooling).
*   `gr-satellites` (GNU Radio decoders) and `gnuradio`.
*   `ffmpeg` or `sox` for data conversion, and Python libraries like `librosa` / `matplotlib` for spectrogram generation.
*   **(Optional) Lightweight ML:** I'm exploring a small CNN for spectrogram classification (TensorFlow/PyTorch), as research indicates ML can help spot faint telemetry.

---

## 3 — Getting the Catalog & Predicting Passes (Concrete Steps)

To get started, I download TLEs and predict passes:

1.  **Download TLEs:**
    I use CelesTrak, which provides up-to-date files. My preferred endpoint is:
    `https://celestrak.org/NORAD/elements/` (or `tle-new.txt`).

2.  **Compute Passes with Python + Skyfield:**
    My Python script using Skyfield looks like this (I replace the coordinates with my own):

    ```python
    from skyfield.api import load, Topos
    stations = load.tle_file('https://celestrak.org/NORAD/elements/tle-new.txt')
    ts = load.timescale()
    observer = Topos('24.86 N', '67.01 E')  # Replace with your coordinates
    # I then choose specific satellites from 'stations' and predict their passes...
    ```
    The Skyfield documentation and Earth satellites examples are excellent resources.

3.  **Alternatively, Use GPredict:**
    I can also use GPredict (GUI) to load TLEs, get live azimuth/elevation data, and control my rotator for each pass. GPredict can be configured to auto-update TLEs and drive a rotator.

---

## 4 — Recording Passes & Accounting for Doppler (Practical)

**Doppler Correction:** I've learned that fast LEO passes require constant frequency correction due to Doppler shift. I calculate the expected Doppler shift from SGP4 (Skyfield provides velocity) or use GPredict's Doppler correction to tune `rtl_tcp`.

**Recording I/Q Data:** I start a wideband I/Q capture during the pass so I can search offline later. My typical `rtl_sdr` command for Linux is:

```bash
rtl_sdr -s 2.4e6 -f 435000000 -g 49 pass_iq.bin
```

I record multiple bands by changing the center frequency across common satellite bands (e.g., 137 MHz, 400–450 MHz, 900–950 MHz). For continuous Doppler tracking, I use `rtl_tcp` with GNU Radio.

**Metadata:** It's crucial to log the NORAD ID, UTC start/end times, predicted azimuth/elevation, and the center frequency for each recording.

---

## 5 — Signal Detection Pipeline (AI + DSP)

My signal detection pipeline involves these steps:

1.  **Preprocessing:** I convert the raw I/Q data into spectrograms using a short-time FFT.
2.  **Anomaly Detection / Classification:** I run a small CNN or a classical energy detector to find narrowband, structured signals (e.g., repeated frames, telemetry bursts). I've found that ML models trained on labeled satellite spectrograms can detect very weak transmissions that humans might miss.
3.  **Protocol Matching:** I feed candidate signal slices to `gr-satellites`, `multimon-ng`, `direwolf` (for AX.25 / AFSK), or custom demodulation flowgraphs to identify known modes. `gr-satellites` already contains decoders for many amateur satellites, and I integrate it with SatNOGS flowgraphs for automation.

**My High-Level Flow:**

I/Q data → spectrogram → CNN → candidate timestamps/frequencies → try demodulation chain (e.g., AFSK → AX.25; GMSK → CSP; BPSK/QPSK → custom frames) → if decoded, save data.

---

## 6 — Using SatNOGS to Amplify Reach & Validate

I leverage SatNOGS to amplify my reach and validate findings. I search their database for observations of a given NORAD ID. If other stations have recently recorded a matching signal, it's strong evidence I've found a legitimately transmitting (though perhaps forgotten) satellite. SatNOGS provides an API and a scheduling system, allowing me to request observations from high-sensitivity stations.

I can install `satnogs-client` to integrate my local station and upload observations automatically.

---

## 7 — Prioritization Heuristics (Who's Worth Chasing)

When prioritizing targets, I rank objects based on these heuristics:

1.  **History of Transmissions:** Recent SatNOGS or other community observations indicate a "hot" target.
2.  **Orbit Type:** LEO CubeSats are generally the easiest and most likely to be intermittently transmitting. GEO objects are often expensive to probe and frequently silent.
3.  **Launch Age & Mission:** Older amateur or CubeSat missions that had brief uplink windows are often good targets.
4.  **Power Likelihood:** If a satellite has solar panels and is in sunlight during its pass, there's a higher chance it's powered. Skyfield can provide sunlit status.

---

## 8 — What Real Outcomes to Expect

Based on my experience, here's what I've found to be the likely outcomes:

*   **Likely:** Detecting telemetry or beacons from amateur satellites or CubeSats (often intermittent). These are common discoveries for hobbyists.
*   **Possible but Rare:** Detecting structured telemetry from a government/commercial spacecraft (if it's still transmitting and unencrypted). If this occurs, I would report it to the operator or authorities.
*   **Impossible / Illegal from Home:** Safely and legally commanding an unrelated satellite to perform new actions without authorization. Transmission requires proper authorization and coordination with operators.

---

## 9 — Example Quick Start Checklist (Do This Tonight)

If you're looking to get started quickly, here's my quick start checklist:

1.  **Install Skyfield & SGP4:** `pip install skyfield sgp4` and grab a TLE from CelesTrak.
2.  **Install `rtl_sdr` tools:** Try `rtl_test` to confirm your hardware. Record a short sample on 137 MHz (e.g., NOAA beacon) to verify your setup.
3.  **Sign up on SatNOGS:** Browse recent "unknown" observations and consider requesting a station observation of an object of interest.
4.  **Install `gr-satellites`:** Try decoding a known CubeSat pass (many tutorials are available online).

---

## 10 — Important Ethical & Reporting Rules

I adhere to important ethical and reporting rules. If I find a live transmitter from a "forgotten" satellite, I notify the appropriate operator or a recognized body (Space-Track, AMSAT, national authority). I never attempt to command or interfere. SatNOGS and AMSAT are excellent intermediaries for this.

---

## Quick Reference Links (To Save You Time)

Here are some quick reference links I use:

*   [CelesTrak TLEs & Docs](https://celestrak.org/NORAD/elements/)
*   [SatNOGS API & Docs](https://network.satnogs.org/api/)
*   [gr-satellites (GNU Radio Decoders)](https://gr-satellites.readthedocs.io/en/latest/)
*   [Skyfield / SGP4 Examples](https://rhodesmill.org/skyfield/earth-satellites.html)

---

## Applying This Research

To apply this research, I often consider these next steps:

*   **Option A:** Pull TLEs and produce a ranked list of 25 objects that will pass over my location (e.g., Karachi) in the next 48 hours and are likely candidates (CubeSats + old communications satellites).
*   **Option B:** Query SatNOGS for recent "unknown" detections and return 10 NORAD IDs with matching observation links I can listen to.
*   **Option C:** Set up an exact, copy-paste SDR + GNU Radio + `gr-satellites` flowgraph and integrate a small ML model repository to run automatic detection on recorded I/Q.
