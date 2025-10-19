# SatNOGS Integration

Instructions for integrating your station with the SatNOGS network.

## What is SatNOGS?

SatNOGS (Satellite Networked Open Ground Station) is a global network of satellite ground stations. By joining, you can:

- **Schedule observations** from any station in the network
- **Share your recordings** with the community
- **Access thousands** of existing observations
- **Validate your detections** against community data
- **Discover** new satellites collaboratively

Website: [https://network.satnogs.org/](https://network.satnogs.org/)

---

## Registration

### 1. Create Account

1. Go to [https://network.satnogs.org/](https://network.satnogs.org/)
2. Click "Sign Up"
3. Complete registration
4. Verify email

### 2. Generate API Key

1. Log in to SatNOGS
2. Go to Settings → API Keys
3. Click "Generate New Token"
4. Copy token (you'll need this)

---

## Station Setup

### 3. Register Your Station

1. Go to "Stations" → "Add Station"
2. Fill in details:
   - **Name:** Your station identifier
   - **Latitude/Longitude:** From `configs/station.ini`
   - **Altitude:** Elevation in meters
   - **Antenna:** Type (QFH, Yagi, etc.)
   - **Description:** Brief overview

3. Save station (note Station ID)

### 4. Configure SATx

Edit `configs/station.ini`:

```ini
[station]
# ... existing config ...

# SatNOGS integration
satnogs_enabled = true
satnogs_station_id = YOUR_STATION_ID
satnogs_api_key = YOUR_API_KEY
```

Create `configs/satnogs-api.json`:

```json
{
  "api_key": "YOUR_API_KEY",
  "station_id": 1234,
  "base_url": "https://network.satnogs.org/api/",
  "network_base_url": "https://network.satnogs.org/",
  "db_base_url": "https://db.satnogs.org/api/"
}
```

---

## Install SatNOGS Client

### 5. Install Software

```bash
# Install satnogs-client
pip install satnogs-client

# Or using apt (Ubuntu)
sudo apt install satnogs-client
```

### 6. Configure Client

```bash
# Initialize configuration
satnogs-client setup

# Follow prompts:
# - API Key: [paste your key]
# - Station ID: [your station ID]
# - Latitude: 24.8607
# - Longitude: 67.0011
# - Altitude: 8
```

Configuration file: `~/.satnogs/settings.py`

---

## Using SatNOGS

### Query Observations

```python
#!/usr/bin/env python3
"""Query SatNOGS for satellite observations."""

import requests
import json

API_KEY = "YOUR_API_KEY"
HEADERS = {"Authorization": f"Token {API_KEY}"}

def query_observations(norad_id, days=7):
    """Get recent observations for a satellite."""
    url = f"https://network.satnogs.org/api/observations/"
    params = {
        "satellite__norad_cat_id": norad_id,
        "start": f"-{days}d",  # Last N days
    }
    
    response = requests.get(url, params=params, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return []

# Example: Query ISS observations
observations = query_observations(25544, days=7)
print(f"Found {len(observations)} observations of ISS")

for obs in observations[:5]:
    print(f"  {obs['start']} - Station {obs['ground_station']}")
```

### Schedule Observation

```python
def schedule_observation(norad_id, start_time, end_time):
    """Schedule observation on your station."""
    url = "https://network.satnogs.org/api/jobs/"
    
    data = {
        "satellite": norad_id,
        "start": start_time,  # ISO format
        "end": end_time,
        "ground_station": YOUR_STATION_ID,
        "frequency": 437800000,  # Hz
        "mode": "FM",
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    return response.json()
```

### Upload Observation

```python
def upload_observation(norad_id, recording_file, metadata):
    """Upload recording to SatNOGS."""
    url = "https://network.satnogs.org/api/observations/"
    
    files = {
        'waterfall': open(recording_file, 'rb'),
    }
    
    data = {
        'satellite': norad_id,
        'start': metadata['start_time'],
        'end': metadata['end_time'],
        'ground_station': YOUR_STATION_ID,
        'observation': metadata.get('observation_id'),
    }
    
    response = requests.post(url, files=files, data=data, headers=HEADERS)
    return response.json()
```

---

## Automatic Integration

### 7. SATx Scheduler with SatNOGS

Modify `scripts/scheduler.py` to query SatNOGS for scheduled observations:

```python
def check_satnogs_schedule(self):
    """Check SatNOGS for scheduled observations."""
    if not self.config.getboolean('station', 'satnogs_enabled'):
        return []
    
    api_key = self.config['station']['satnogs_api_key']
    station_id = self.config['station']['satnogs_station_id']
    
    headers = {"Authorization": f"Token {api_key}"}
    url = f"https://network.satnogs.org/api/jobs/"
    params = {"ground_station": station_id}
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []
```

---

## Community Features

### Validating Your Detections

1. Record a satellite pass
2. Process with `process_recording.py`
3. Search SatNOGS for observations of same satellite
4. Compare:
   - Frequency match
   - Signal characteristics
   - Decoded telemetry

### Discovering Unknown Satellites

1. Filter SatNOGS observations by "Unknown" transmitter
2. Download I/Q or audio samples
3. Process with your decoders
4. Report findings to community

### Contributing Decoders

If you decode a new satellite:
1. Document the protocol
2. Create GNU Radio flowgraph
3. Submit to [gr-satellites](https://github.com/daniestevez/gr-satellites)
4. Update SatNOGS database

---

## SatNOGS API Reference

### Base URLs

- **Network API:** `https://network.satnogs.org/api/`
- **DB API:** `https://db.satnogs.org/api/`

### Key Endpoints

#### Get Satellite Info
```
GET /satellites/{id}/
```

#### List Observations
```
GET /observations/?satellite__norad_cat_id={norad}
```

#### List Transmitters
```
GET /transmitters/?satellite__norad_cat_id={norad}
```

#### Get Station Info
```
GET /stations/{id}/
```

### Rate Limits

- 100 requests per minute (unauthenticated)
- 1000 requests per minute (authenticated)

---

## Troubleshooting

### API Authentication Errors

- Verify API key is correct
- Check key hasn't expired
- Ensure token format: `Authorization: Token YOUR_KEY`

### Upload Failures

- Check file size limits (< 50 MB)
- Verify audio/waterfall format
- Ensure observation ID is valid

### Scheduling Issues

- Confirm station is online
- Check for conflicting observations
- Verify pass prediction accuracy

---

## Resources

- [SatNOGS Documentation](https://wiki.satnogs.org/)
- [SatNOGS API Docs](https://network.satnogs.org/api/)
- [SatNOGS Forum](https://community.libre.space/)
- [SatNOGS Client Docs](https://gitlab.com/librespacefoundation/satnogs/satnogs-client)

---

**Join the global satellite tracking community!**
