# Quick Start Guide for SATx

Get up and running in 30 minutes or less.

---

## Prerequisites

- **Hardware:**
  - RTL-SDR dongle (RTL2832U + R820T2)
  - USB extension cable (recommended)
  - Antenna (VHF/UHF whip, QFH, or Turnstile)
  - Laptop/Desktop (Linux recommended, Windows/macOS with WSL)

- **Software:**
  - Python 3.8 or higher
  - Git
  - 5GB free disk space (for recordings and software)

---

## Installation (Linux/Ubuntu)

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/SATx.git
cd SATx
```

### 2. Run Installation Script

```bash
chmod +x scripts/install_tools.sh
./scripts/install_tools.sh
```

This will install:
- RTL-SDR drivers
- GNU Radio + GQRX
- GPredict
- gr-satellites
- Python dependencies

**Note:** Reboot may be required after driver installation.

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### 4. Configure Your Station

Edit `configs/station.ini`:

```ini
[station]
name = My-Station
location = Your City, Country

# YOUR coordinates (decimal degrees)
latitude = 24.8607
longitude = 67.0011
elevation = 8.0
```

**How to find your coordinates:**
- Google Maps: Right-click → "What's here?"
- GPS app on smartphone
- [latlong.net](https://www.latlong.net/)

---

## First Test

### 5. Test RTL-SDR Hardware

```bash
rtl_test -t
```

**Expected output:**
```
Found 1 device(s):
  0:  Realtek, RTL2838UHIDIR, SN: 00000001
```

If you see "No supported devices found", check:
- USB connection
- Driver installation
- USB permissions: `sudo usermod -a -G plugdev $USER` (then logout/login)

### 6. Test Reception with GQRX

```bash
gqrx
```

1. Set device to "Realtek RTL2838"
2. Set frequency to 137.5 MHz (NOAA weather satellites)
3. Set mode to "WFM" (Wide FM)
4. Click "Play" button

You should see the waterfall display. If a NOAA satellite is overhead, you'll see strong signal around 137.1, 137.5, or 137.9 MHz.

---

## First Satellite Pass

### 7. Fetch TLE Data

```bash
python scripts/fetch_tles.py
```

This downloads current satellite orbital data (~10,000 satellites).

### 8. Predict Passes

```bash
python scripts/predict_passes.py
```

**Output:** List of upcoming passes in next 48 hours.

Example:
```
1. ISS (ZARYA) (NORAD 25544)
   Rise: 2025-10-19 14:32:15 UTC
   Max Elevation: 45.2°
   Duration: 8m 23s
```

### 9. Record a Pass Manually

For the ISS example above, record it:

```bash
bash scripts/start_recording.sh 25544 437800000 2400000 500 recordings/iss_test.iq
```

**Parameters:**
- `25544` = NORAD ID (ISS)
- `437800000` = 437.8 MHz (ISS packet radio frequency)
- `2400000` = 2.4 MSPS sample rate
- `500` = 500 seconds duration
- `recordings/iss_test.iq` = output file

**Tip:** Start recording 1-2 minutes before predicted rise time.

### 10. Process Recording

```bash
python scripts/process_recording.py recordings/iss_test.iq
```

**Output:**
- Spectrogram image: `recordings/iss_test.png`
- Detected candidates: `recordings/iss_test.candidates.json`
- Log entry in `logs/candidates.csv`

---

## Automated Operation

### 11. Run Automated Scheduler

For hands-free operation:

```bash
python scripts/scheduler.py
```

This will:
1. Update TLEs daily
2. Predict passes continuously
3. Automatically record passes
4. Process recordings
5. Log all detections

**Press Ctrl+C to stop.**

---

## Next Steps

### Improve Your Setup

1. **Better Antenna:**
   - Build QFH for 137 MHz NOAA: [Guide](https://www.rtl-sdr.com/simple-noaa-weather-satellite-antenna-137-mhz-v-dipole/)
   - Build Turnstile for 435 MHz: [Guide](https://www.amsat.org/two-element-turnstile/)

2. **Upgrade SDR:**
   - Airspy Mini ($99) for better sensitivity
   - SDRplay RSPdx ($200) for wider bandwidth

3. **Add Rotator:**
   - Track satellites for better SNR
   - GPredict can control Az/El rotators

### Decode Signals

**NOAA Weather Images:**
```bash
# Install WXtoImg
sudo apt install wxtoimg

# Decode NOAA APT
wxtoimg -e HVC recordings/noaa_pass.wav output.png
```

**Amateur Satellite Packets (gr-satellites):**
```bash
# Decode telemetry
gr_satellites recordings/cubesat.iq --norad 12345 --samp_rate 2.4e6
```

### Join SatNOGS Network

1. Create account: [network.satnogs.org](https://network.satnogs.org/)
2. Register your station
3. Schedule observations
4. Share your data globally

---

## Troubleshooting

### "No devices found"
- Check USB connection
- Verify drivers: `lsusb` should show Realtek device
- Check permissions: `sudo usermod -a -G plugdev $USER`

### "Sample dropped"
- Reduce sample rate to 1.8 MSPS
- Use faster USB port (USB 3.0)
- Reduce gain to prevent overload

### "No signals detected"
- Verify antenna connection
- Check frequency (try NOAA 137.5 MHz)
- Increase gain (try 40-49 dB)
- Confirm satellite is actually overhead

### Recordings are large
- 2.4 MSPS × 8 bits × 2 (I+Q) = ~5 MB/second
- 10-minute pass = ~3 GB
- Use external HDD or compress old recordings

---

## Learning Resources

- **RTL-SDR Blog:** [rtl-sdr.com](https://www.rtl-sdr.com/)
- **SatNOGS Wiki:** [wiki.satnogs.org](https://wiki.satnogs.org/)
- **gr-satellites Docs:** [gr-satellites.readthedocs.io](https://gr-satellites.readthedocs.io/)
- **Skyfield Docs:** [rhodesmill.org/skyfield](https://rhodesmill.org/skyfield/)

---

## Success Checklist

- [ ] RTL-SDR detected by `rtl_test`
- [ ] GQRX shows waterfall
- [ ] TLEs downloaded successfully
- [ ] Pass predictions show upcoming satellites
- [ ] Recorded a test pass
- [ ] Generated spectrogram
- [ ] Automated scheduler runs

**Once all checked, you're operational! 🛰️**

---

## Support

- **Issues:** GitHub Issues
- **Community:** SatNOGS Forums, r/RTLSDR
- **Email:** support@example.com (replace with actual)

---

**Happy satellite hunting!**
