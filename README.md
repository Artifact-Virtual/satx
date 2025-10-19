# SATx - Satellite Detection, Tracking, and Transmission System

A complete automated system for detecting, tracking, decoding transmissions from satellites passing overhead. SATx leverages SDR hardware, GNU Radio, and machine learning to provide end-to-end satellite observation capabilities.

## Features

- **Automatic TLE fetching and pass prediction** - Real-time orbital data and pass scheduling
- **Doppler-corrected SDR recording** - High-quality I/Q data capture with frequency correction
- **ML-based signal detection** - CNN-powered signal identification and classification
- **Multi-protocol decoding** - Support for AX.25, AFSK, GMSK, BPSK, QPSK, and more
- **SatNOGS integration** - Community network validation and data sharing
- **Automated scheduling and processing pipeline** - End-to-end observation automation
- **Web dashboard** - Real-time monitoring and control interface
- **Optional transmission capabilities** - Authorized transmission with safety protocols
- **Docker containerization** - Easy deployment and scaling
- **Comprehensive testing suite** - Automated validation of all components

## ML and AI Capabilities

SATx uses deep learning for advanced signal processing:

- **Signal Detection**: CNN-based spectrogram analysis for automatic signal identification
- **Protocol Classification**: Multi-class classification for different modulation schemes
- **Noise Reduction**: AI-powered filtering and enhancement
- **Training Pipeline**: Automated data preparation and model training
- **SatNOGS Integration**: Community data for improved model accuracy

Models are trained on both synthetic and real satellite signals, achieving high accuracy in various conditions.

## Quick Start

### Automated Setup (Recommended)

For a complete turnkey installation with ML training:

```bash
# Clone and setup everything automatically
git clone <repository-url>
cd SATx
./setup.sh
```

The setup script will:
- Detect your OS and install dependencies
- Set up Python virtual environment
- Install SDR drivers and GNU Radio
- Download and train ML models
- Configure your station
- Test the complete pipeline

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your station:**
   Edit `configs/station.ini` with your location coordinates

3. **Fetch latest TLEs:**
   ```bash
   python scripts/fetch_tles.py
   ```

4. **Predict upcoming passes:**
   ```bash
   python scripts/predict_passes.py
   ```

5. **Run automated observation:**
   ```bash
   python scripts/scheduler.py
   ```

### ML Training Setup

To train or retrain the signal detection models:

```bash
# Prepare training data
python scripts/prepare_training_data.py

# Download additional data from SatNOGS
python scripts/download_satnogs_data.py

# Train the model
python models/model_v1/train.py
```

### Testing

Run comprehensive system tests:

```bash
python scripts/test_system.py
```

## Hardware Requirements

### Minimum Setup (~$50)
- RTL-SDR dongle (RTL2832U + R820T2)
- DIY QFH or Turnstile antenna
- USB extension cable
- Coax cable + SMA adapters

### Recommended Upgrades
- Airspy or SDRplay (~$150-$300)
- Az/El rotator (~$300+)
- Dual-band Yagi antenna (~$60-$150)

## Software Requirements

- Python 3.8+
- GNU Radio 3.8+
- RTL-SDR drivers
- GPredict
- gr-satellites

See `scripts/install_tools.sh` for automated installation.

## Project Structure

```
SATx/
├─ scripts/                    # Core automation scripts
│  ├─ fetch_tles.py           # TLE data fetching
│  ├─ predict_passes.py       # Orbital pass prediction
│  ├─ process_recording.py    # Signal processing with ML
│  ├─ scheduler.py            # Automated observation scheduler
│  ├─ prepare_training_data.py # ML training data preparation
│  ├─ download_satnogs_data.py # SatNOGS data acquisition
│  ├─ test_system.py          # Comprehensive system testing
│  ├─ install_tools.sh        # Legacy installation script
│  ├─ start_recording.sh      # Recording startup script
│  └─ ...
├─ configs/                    # Station and service configurations
│  └─ station.ini             # Station location and settings
├─ data/                       # Data storage
│  └─ tles/                   # TLE orbital data
├─ decoders/                   # Signal decoders and flowgraphs
│  └─ grc_flowgraphs/         # GNU Radio flowgraphs
├─ models/                     # ML models for signal detection
│  └─ model_v1/               # Current model version
│     ├─ model.py             # CNN architecture
│     ├─ train.py             # Training script
│     └─ README.md            # Model documentation
├─ services/                   # Docker services
│  ├─ ml/                     # ML processing service
│  └─ sdr/                    # SDR processing service
├─ transmit/                   # Transmission capabilities
├─ web/                       # Dashboard UI
├─ recordings/                 # Recorded I/Q data (gitignored)
├─ logs/                      # Operation logs and candidates
├─ setup.sh                   # Automated setup script
├─ requirements.txt           # Python dependencies
├─ docker-compose.yml         # Docker orchestration
└─ README.md                  # This file
```

## Resources

- [CelesTrak](https://celestrak.org/NORAD/elements/) - TLE data
- [SatNOGS](https://network.satnogs.org/) - Community network
- [gr-satellites](https://gr-satellites.readthedocs.io/) - Decoders
- [Skyfield](https://rhodesmill.org/skyfield/) - Orbital calculations

## Contributing

Contributions welcome

## License

MIT License - See LICENSE file
