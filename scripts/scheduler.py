#!/usr/bin/env python3
"""
Automated scheduler for satellite observations.
Predicts passes, schedules recordings, and processes data automatically.
"""

import logging
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import configparser
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SatelliteScheduler:
    def __init__(self, config_file='configs/station.ini'):
        """Initialize scheduler with configuration."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.station_name = self.config['station']['name']
        self.min_elevation = float(self.config['station']['min_elevation'])
        self.recording_path = Path(self.config['station']['recording_path'])
        
        logger.info(f"Scheduler initialized for {self.station_name}")
        
    def update_tles(self):
        """Update TLE data."""
        logger.info("Updating TLEs...")
        try:
            subprocess.run(['python3', 'scripts/fetch_tles.py'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update TLEs: {e}")
            return False
    
    def predict_passes(self, hours=24):
        """Generate pass predictions."""
        logger.info(f"Predicting passes for next {hours} hours...")
        try:
            subprocess.run(['python3', 'scripts/predict_passes.py'], check=True)
            
            # Load predictions
            predictions_file = Path('logs/predicted_passes.json')
            if predictions_file.exists():
                with open(predictions_file, 'r') as f:
                    passes = json.load(f)
                return passes
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to predict passes: {e}")
            return []
    
    def schedule_recording(self, pass_info):
        """Schedule and execute recording for a pass."""
        norad_id = pass_info['norad_id']
        satellite = pass_info['satellite']
        rise_time = datetime.fromisoformat(pass_info['rise_time'])
        set_time = datetime.fromisoformat(pass_info['set_time'])
        duration = int(pass_info['duration'])
        max_elevation = pass_info.get('max_elevation', 0)
        
        # Wait until pass starts
        now = datetime.utcnow()
        wait_seconds = (rise_time - now).total_seconds()
        
        if wait_seconds > 0:
            logger.info(f"Waiting {int(wait_seconds)}s until pass of {satellite}...")
            time.sleep(wait_seconds)
        
        # Determine recording frequency based on bands
        # Default to UHF amateur band
        center_freq = 437000000
        sample_rate = 2400000
        
        # Generate output filename
        timestamp = rise_time.strftime('%Y%m%d_%H%M%S')
        output_file = self.recording_path / f"{timestamp}_NORAD{norad_id}_{satellite.replace(' ', '_')}.iq"
        
        logger.info("="*60)
        logger.info(f"RECORDING PASS")
        logger.info(f"Satellite: {satellite} (NORAD {norad_id})")
        logger.info(f"Max Elevation: {max_elevation:.1f}°")
        logger.info(f"Duration: {duration}s")
        logger.info("="*60)
        
        # Execute recording
        try:
            subprocess.run([
                'bash', 'scripts/start_recording.sh',
                str(norad_id),
                str(center_freq),
                str(sample_rate),
                str(duration),
                str(output_file)
            ], check=True)
            
            logger.info(f"Recording complete: {output_file}")
            
            # Process recording
            self.process_recording(output_file)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Recording failed: {e}")
            return False
    
    def process_recording(self, recording_file):
        """Process recorded file."""
        logger.info(f"Processing recording: {recording_file}")
        try:
            subprocess.run([
                'python3', 'scripts/process_recording.py',
                str(recording_file)
            ], check=True)
            logger.info("Processing complete")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Processing failed: {e}")
            return False
    
    def run(self):
        """Main scheduler loop."""
        logger.info("="*60)
        logger.info("SATx Automated Scheduler Started")
        logger.info("="*60)
        
        # Update TLEs on startup
        self.update_tles()
        
        while True:
            try:
                # Get upcoming passes
                passes = self.predict_passes(hours=24)
                
                if not passes:
                    logger.warning("No passes predicted. Waiting 1 hour...")
                    time.sleep(3600)
                    continue
                
                # Filter passes in the next 2 hours
                now = datetime.utcnow()
                upcoming = [
                    p for p in passes
                    if datetime.fromisoformat(p['rise_time']) < now + timedelta(hours=2)
                    and datetime.fromisoformat(p['set_time']) > now
                ]
                
                if upcoming:
                    # Take the next pass
                    next_pass = upcoming[0]
                    self.schedule_recording(next_pass)
                else:
                    logger.info("No passes in next 2 hours. Waiting...")
                    time.sleep(600)  # Check every 10 minutes
                
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

def main():
    """Main execution function."""
    scheduler = SatelliteScheduler()
    scheduler.run()
    return 0

if __name__ == '__main__':
    exit(main())
