#!/usr/bin/env python3
"""
Predict satellite passes for configured station location.
Uses Skyfield for accurate orbital calculations and Doppler prediction.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import configparser

from skyfield.api import load, wgs84, EarthSatellite
from skyfield import almanac

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PassPredictor:
    def __init__(self, config_file='configs/station.ini'):
        """Initialize pass predictor with station configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Load station location
        self.latitude = float(self.config['station']['latitude'])
        self.longitude = float(self.config['station']['longitude'])
        self.elevation = float(self.config['station']['elevation'])
        self.min_elevation = float(self.config['station']['min_elevation'])
        
        # Create observer location
        self.observer = wgs84.latlon(self.latitude, self.longitude, self.elevation)
        
        # Load timescale
        self.ts = load.timescale()
        
        logger.info(f"Station: {self.config['station']['name']}")
        logger.info(f"Location: {self.latitude}°N, {self.longitude}°E, {self.elevation}m")
        logger.info(f"Minimum elevation: {self.min_elevation}°")
    
    def load_satellites(self, tle_file='data/tles/all-satellites.tle'):
        """Load satellites from TLE file."""
        tle_path = Path(__file__).parent.parent / tle_file
        
        if not tle_path.exists():
            logger.error(f"TLE file not found: {tle_path}")
            logger.error("Run 'python scripts/fetch_tles.py' first!")
            return []
        
        logger.info(f"Loading satellites from {tle_path}...")
        
        satellites = []
        with open(tle_path, 'r') as f:
            lines = f.readlines()
        
        # Parse TLE sets
        for i in range(0, len(lines) - 2, 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                if line1.startswith('1 ') and line2.startswith('2 '):
                    try:
                        sat = EarthSatellite(line1, line2, name, self.ts)
                        satellites.append(sat)
                    except Exception as e:
                        logger.warning(f"Failed to parse satellite {name}: {e}")
        
        logger.info(f"Loaded {len(satellites)} satellites")
        return satellites
    
    def predict_passes(self, satellite, start_time, end_time):
        """Predict passes for a single satellite."""
        passes = []
        
        # Find events (rise/culminate/set)
        t, events = satellite.find_events(
            self.observer, 
            start_time, 
            end_time, 
            altitude_degrees=self.min_elevation
        )
        
        # Group events into passes
        current_pass = {}
        for ti, event in zip(t, events):
            if event == 0:  # Rise
                current_pass = {
                    'satellite': satellite.name,
                    'norad_id': satellite.model.satnum,
                    'rise_time': ti.utc_datetime(),
                }
            elif event == 1:  # Culminate
                if current_pass:
                    difference = satellite - self.observer
                    topocentric = difference.at(ti)
                    alt, az, distance = topocentric.altaz()
                    
                    current_pass['max_elevation'] = alt.degrees
                    current_pass['max_elevation_time'] = ti.utc_datetime()
                    current_pass['azimuth'] = az.degrees
                    current_pass['distance_km'] = distance.km
            elif event == 2:  # Set
                if current_pass:
                    current_pass['set_time'] = ti.utc_datetime()
                    current_pass['duration'] = (
                        current_pass['set_time'] - current_pass['rise_time']
                    ).total_seconds()
                    passes.append(current_pass)
                    current_pass = {}
        
        return passes
    
    def calculate_doppler(self, satellite, t):
        """Calculate Doppler shift at given time."""
        difference = satellite - self.observer
        topocentric = difference.at(t)
        
        # Calculate radial velocity (positive = moving away)
        velocity = topocentric.velocity.km_per_s
        radial_velocity = velocity[2] if len(velocity) > 2 else 0
        
        return radial_velocity
    
    def generate_pass_predictions(self, hours=48, output_file='logs/predicted_passes.json'):
        """Generate pass predictions for all satellites."""
        satellites = self.load_satellites()
        
        if not satellites:
            logger.error("No satellites loaded")
            return
        
        # Time window
        t_start = self.ts.now()
        t_end = self.ts.from_datetime(datetime.now(timezone.utc) + timedelta(hours=hours))
        
        logger.info(f"Predicting passes for next {hours} hours...")
        logger.info(f"From: {t_start.utc_datetime()} UTC")
        logger.info(f"To: {t_end.utc_datetime()} UTC")
        
        all_passes = []
        
        for sat in satellites:
            try:
                passes = self.predict_passes(sat, t_start, t_end)
                all_passes.extend(passes)
            except Exception as e:
                logger.debug(f"Error predicting passes for {sat.name}: {e}")
        
        # Sort by rise time
        all_passes.sort(key=lambda x: x['rise_time'])
        
        logger.info(f"Found {len(all_passes)} passes")
        
        # Convert datetime objects to ISO format for JSON
        for p in all_passes:
            p['rise_time'] = p['rise_time'].isoformat()
            if 'max_elevation_time' in p:
                p['max_elevation_time'] = p['max_elevation_time'].isoformat()
            if 'set_time' in p:
                p['set_time'] = p['set_time'].isoformat()
        
        # Save to file
        output_path = Path(__file__).parent.parent / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(all_passes, f, indent=2)
        
        logger.info(f"Saved predictions to {output_path}")
        
        # Print top 25 passes
        print("\n" + "="*80)
        print("TOP 25 UPCOMING PASSES")
        print("="*80)
        
        for i, p in enumerate(all_passes[:25], 1):
            rise = datetime.fromisoformat(p['rise_time'])
            max_el = p.get('max_elevation', 0)
            duration = p.get('duration', 0)
            
            print(f"\n{i}. {p['satellite']} (NORAD {p['norad_id']})")
            print(f"   Rise: {rise.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   Max Elevation: {max_el:.1f}°")
            print(f"   Duration: {int(duration/60)}m {int(duration%60)}s")
        
        print("\n" + "="*80)
        
        return all_passes

def main():
    """Main execution function."""
    predictor = PassPredictor()
    predictor.generate_pass_predictions(hours=48)
    return 0

if __name__ == '__main__':
    exit(main())
