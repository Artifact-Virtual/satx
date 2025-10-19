#!/usr/bin/env bash
# start_recording.sh - Record satellite pass with RTL-SDR
# Usage: ./start_recording.sh NORAD_ID CENTER_FREQ SAMPLE_RATE DURATION_SEC OUTFILE

set -e

# Parse arguments
NORAD_ID=$1
CENTER_FREQ=$2
SAMPLE_RATE=$3
DURATION_SEC=$4
OUTFILE=$5

if [ -z "$NORAD_ID" ] || [ -z "$CENTER_FREQ" ] || [ -z "$SAMPLE_RATE" ] || [ -z "$DURATION_SEC" ] || [ -z "$OUTFILE" ]; then
    echo "Usage: $0 NORAD_ID CENTER_FREQ SAMPLE_RATE DURATION_SEC OUTFILE"
    echo "Example: $0 25544 437800000 2400000 600 recordings/iss_pass.iq"
    exit 1
fi

# Configuration
GAIN=${GAIN:-49}
PPM=${PPM:-0}
DEVICE=${DEVICE:-0}

# Calculate number of samples
NUM_SAMPLES=$((DURATION_SEC * SAMPLE_RATE))

# Create output directory
mkdir -p "$(dirname "$OUTFILE")"

# Log metadata
METADATA_FILE="${OUTFILE}.json"
UTC_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=========================================="
echo "Recording Satellite Pass"
echo "=========================================="
echo "NORAD ID: $NORAD_ID"
echo "Center Frequency: $CENTER_FREQ Hz"
echo "Sample Rate: $SAMPLE_RATE S/s"
echo "Duration: $DURATION_SEC seconds"
echo "Gain: $GAIN dB"
echo "Output: $OUTFILE"
echo "Started: $UTC_TIME"
echo "=========================================="

# Create metadata file
cat > "$METADATA_FILE" <<EOF
{
  "norad_id": $NORAD_ID,
  "center_frequency": $CENTER_FREQ,
  "sample_rate": $SAMPLE_RATE,
  "duration_seconds": $DURATION_SEC,
  "gain": $GAIN,
  "ppm": $PPM,
  "device": $DEVICE,
  "start_time": "$UTC_TIME",
  "filename": "$OUTFILE"
}
EOF

# Start recording
echo "Recording..."
rtl_sdr -d $DEVICE -f $CENTER_FREQ -s $SAMPLE_RATE -g $GAIN -p $PPM -n $NUM_SAMPLES "$OUTFILE"

# Update metadata with completion time
UTC_END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
FILESIZE=$(stat -f%z "$OUTFILE" 2>/dev/null || stat -c%s "$OUTFILE")

# Update metadata
python3 -c "
import json
with open('$METADATA_FILE', 'r') as f:
    data = json.load(f)
data['end_time'] = '$UTC_END'
data['file_size_bytes'] = $FILESIZE
with open('$METADATA_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"

echo "Recording complete!"
echo "File size: $(numfmt --to=iec-i --suffix=B $FILESIZE)"
echo "Metadata saved to: $METADATA_FILE"

# Log to pipeline log
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
echo "$UTC_TIME | NORAD $NORAD_ID | $CENTER_FREQ Hz | ${DURATION_SEC}s | $OUTFILE" >> "$LOG_DIR/recordings.log"

echo "=========================================="
