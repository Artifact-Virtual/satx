#!/usr/bin/env bash
# install_tools.sh - Automated installation of SATx dependencies
# For Ubuntu/Debian Linux systems

set -e

echo "=========================================="
echo "SATx System Installation Script"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "WARNING: This script is designed for Linux (Ubuntu/Debian)"
    echo "For Windows, please see docs/windows_setup.md"
    echo "For macOS, please see docs/macos_setup.md"
    exit 1
fi

# Update system
echo "[1/10] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install build essentials
echo "[2/10] Installing build tools..."
sudo apt install -y git build-essential cmake python3-pip python3-venv python3-dev

# Install RTL-SDR drivers
echo "[3/10] Installing RTL-SDR drivers..."
sudo apt install -y librtlsdr0 rtl-sdr rtl-test librtlsdr-dev

# Blacklist kernel driver if needed
if ! grep -q "blacklist dvb_usb_rtl28xxu" /etc/modprobe.d/blacklist-rtl.conf 2>/dev/null; then
    echo "blacklist dvb_usb_rtl28xxu" | sudo tee /etc/modprobe.d/blacklist-rtl.conf
    echo "Kernel driver blacklisted (reboot may be required)"
fi

# Install GNU Radio and GQRX
echo "[4/10] Installing GNU Radio and GQRX..."
sudo apt install -y gnuradio gqrx-sdr gr-osmosdr

# Install GPredict
echo "[5/10] Installing GPredict..."
sudo apt install -y gpredict

# Install audio/video tools
echo "[6/10] Installing audio/video processing tools..."
sudo apt install -y sox ffmpeg libsox-dev

# Install additional libraries
echo "[7/10] Installing additional system libraries..."
sudo apt install -y libusb-1.0-0-dev pkg-config libfftw3-dev

# Install gr-satellites
echo "[8/10] Installing gr-satellites..."
cd /tmp
if [ ! -d "gr-satellites" ]; then
    git clone https://github.com/daniestevez/gr-satellites.git
fi
cd gr-satellites
mkdir -p build
cd build
cmake ..
make
sudo make install
sudo ldconfig

# Install Python dependencies
echo "[9/10] Installing Python packages..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Test RTL-SDR
echo "[10/10] Testing RTL-SDR installation..."
if rtl_test -t 2>&1 | grep -q "Found"; then
    echo "✓ RTL-SDR detected successfully!"
else
    echo "⚠ RTL-SDR not detected. Please check USB connection."
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure your station in configs/station.ini"
echo "2. Run: python scripts/fetch_tles.py"
echo "3. Run: python scripts/predict_passes.py"
echo ""
echo "If RTL-SDR was not detected, try:"
echo "  - Reconnecting the USB device"
echo "  - Rebooting the system"
echo "  - Running: sudo rmmod dvb_usb_rtl28xxu (if still loaded)"
echo ""
