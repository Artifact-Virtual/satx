# SATx Quick Start Guide

Get your satellite detection system up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- RTL-SDR dongle (optional for testing, required for actual recordings)
- Basic antenna (whip, dipole, or QFH)

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt
```

**Note:** If you run out of disk space during installation, the core dependencies (numpy, scipy, matplotlib, skyfield, pandas, flask, requests) should be sufficient to get started.

## Step 2: Configure Your Station

Edit `configs/station.ini` with your location:

```ini
[station]
name = My-Station
latitude = 40.7128    # Your latitude
longitude = -74.0060  # Your longitude
elevation = 10.0      # Meters above sea level
min_elevation = 10.0  # Minimum elevation for passes
```

## Step 3: Fetch Satellite Data

```bash
python3 scripts/fetch_tles.py
```

This downloads orbital data (TLEs) for thousands of satellites.

## Step 4: Predict Satellite Passes

```bash
python3 scripts/predict_passes.py
```

You'll see a list of upcoming satellite passes like:

```
1. NOAA 19 (NORAD 33591)
   Rise: 2026-01-01 16:34:44 UTC
   Max Elevation: 12.5°
   Duration: 4m 31s
```

## Step 5: Start the Web Dashboard

```bash
python3 web/app.py
```

Open your browser to: **http://localhost:8080**

You'll see:
- 📊 Real-time system statistics
- 🛰️ Active satellite tracking
- 📈 Analytics dashboard
- 📁 Recording library

## Step 6: Record Your First Pass (Optional)

If you have an RTL-SDR connected:

```bash
# Record a 5-minute pass
bash scripts/start_recording.sh 25544 437000000 2400000 300 recordings/test.iq
```

Parameters:
- `25544` - NORAD ID (ISS in this example)
- `437000000` - Frequency in Hz (437 MHz UHF)
- `2400000` - Sample rate (2.4 MHz)
- `300` - Duration in seconds (5 minutes)
- `recordings/test.iq` - Output filename

## Step 7: Process Recording

```bash
python3 scripts/process_recording.py recordings/test.iq
```

This generates:
- Spectrogram image (`.png`)
- Signal candidates (`.json`)
- CSV log entry

## Automated Operation

For hands-free operation, use the scheduler:

```bash
python3 scripts/scheduler.py
```

The scheduler will:
1. Update TLEs daily
2. Predict upcoming passes
3. Automatically record satellites
4. Process recordings
5. Log all detections

## Troubleshooting

### "No module named 'skyfield'"
```bash
pip3 install skyfield numpy scipy matplotlib pandas requests flask
```

### "No TLE file found"
```bash
python3 scripts/fetch_tles.py
```

### "RTL-SDR not found"
For testing without hardware, you can:
1. Use the web dashboard to explore the UI
2. Run pass predictions
3. Create dummy recordings for testing

### Web dashboard not loading
Check that port 8080 is available:
```bash
python3 web/app.py
# Access at http://localhost:8080
```

## Next Steps

1. **Hardware Setup**: Connect your RTL-SDR and antenna
2. **Antenna Optimization**: Position for best sky view
3. **Schedule Observations**: Set up automated recording
4. **Join Community**: Share observations on SatNOGS
5. **Decode Signals**: Use gr-satellites for protocol decoding

## Resources

- [Full Documentation](README.md)
- [Hardware Requirements](docs/critical_requirements.md)
- [Antenna Building Guide](docs/antenna_build.md)
- [SatNOGS Network](https://network.satnogs.org/)

---

**Happy satellite hunting! 🛰️**
