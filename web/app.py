#!/usr/bin/env python3
"""
SATx Web Dashboard
Flask-based web interface for monitoring satellite observations.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / 'logs'
RECORDINGS_DIR = BASE_DIR / 'recordings'

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status."""
    status = {
        'timestamp': datetime.utcnow().isoformat(),
        'recordings_count': len(list(RECORDINGS_DIR.glob('*.iq'))),
        'logs_count': len(list(LOGS_DIR.glob('*.log'))),
        'candidates_count': 0
    }

    # Count candidates
    candidates_file = LOGS_DIR / 'candidates.csv'
    if candidates_file.exists():
        with open(candidates_file, 'r') as f:
            status['candidates_count'] = sum(1 for line in f) - 1  # Subtract header

    return jsonify(status)

@app.route('/api/candidates')
def get_candidates():
    """Get recent signal candidates."""
    candidates = []
    candidates_file = LOGS_DIR / 'candidates.csv'

    if candidates_file.exists():
        with open(candidates_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:  # Has header + data
                for line in lines[1:][-50:]:  # Last 50 candidates
                    parts = line.strip().split(',')
                    if len(parts) >= 7:
                        candidates.append({
                            'timestamp': parts[0],
                            'norad_id': parts[1],
                            'center_freq': float(parts[2]),
                            'freq_offset': float(parts[3]),
                            'snr_db': float(parts[4]),
                            'peak_time': float(parts[5]),
                            'recording_file': parts[6]
                        })

    return jsonify(candidates)

@app.route('/api/recordings')
def get_recordings():
    """Get list of recordings."""
    recordings = []
    if RECORDINGS_DIR.exists():
        for iq_file in RECORDINGS_DIR.glob('*.iq'):
            metadata_file = iq_file.with_suffix('.iq.json')
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass

            recordings.append({
                'filename': iq_file.name,
                'size_mb': round(iq_file.stat().st_size / 1024 / 1024, 2),
                'metadata': metadata
            })

    return jsonify(recordings)

@app.route('/api/spectrogram/<filename>')
def get_spectrogram(filename):
    """Get spectrogram image for a recording."""
    png_file = RECORDINGS_DIR / filename.replace('.iq', '.png')
    if png_file.exists():
        return {'url': f'/recordings/{png_file.name}'}
    return {'error': 'Spectrogram not found'}, 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
