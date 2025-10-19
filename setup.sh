#!/usr/bin/env bash
# setup.sh - Complete automated setup for SATx satellite detection system
# This script handles the entire installation and configuration process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (for some operations)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            OS="ubuntu"
        elif command -v yum &> /dev/null; then
            OS="centos"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    log_info "Detected OS: $OS"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python $PYTHON_VERSION ✓"
    else
        log_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi

    # Check available disk space (need at least 5GB)
    DISK_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ "$DISK_SPACE" -lt 5242880 ]; then  # 5GB in KB
        log_warning "Low disk space detected. At least 5GB recommended."
    fi

    # Check internet connection
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_error "No internet connection detected"
        exit 1
    fi
    log_success "Internet connection ✓"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."

    case $OS in
        ubuntu)
            sudo apt update
            sudo apt install -y git build-essential cmake python3-pip python3-venv \
                               librtlsdr0 rtl-sdr librtlsdr-dev libusb-1.0-0-dev \
                               pkg-config libfftw3-dev sox ffmpeg libsox-dev \
                               gnuradio gqrx-sdr gr-osmosdr gpredict
            ;;
        centos)
            sudo yum update -y
            sudo yum install -y git gcc gcc-c++ cmake python3-pip python3-devel \
                               rtl-sdr rtl-sdr-devel libusb1-devel pkgconfig \
                               fftw-devel sox ffmpeg sox-devel \
                               gnuradio gnuradio-devel gqrx gpredict
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                log_error "Homebrew is required for macOS. Install from https://brew.sh/"
                exit 1
            fi
            brew install git cmake python3 rtl-sdr sox ffmpeg gnuradio gqrx gpredict
            ;;
        windows)
            log_warning "For Windows, please run SETUP_WINDOWS.ps1 instead"
            exit 1
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac

    log_success "System dependencies installed"
}

# Install gr-satellites
install_gr_satellites() {
    log_info "Installing gr-satellites..."

    cd /tmp
    if [ ! -d "gr-satellites" ]; then
        git clone https://github.com/daniestevez/gr-satellites.git
    fi
    cd gr-satellites

    if [ ! -d "build" ]; then
        mkdir build
        cd build
        cmake ..
        make -j$(nproc)
        sudo make install
        sudo ldconfig
    fi

    log_success "gr-satellites installed"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python environment..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install Python dependencies
    pip install -r requirements.txt

    log_success "Python environment ready"
}

# Configure RTL-SDR
configure_rtl_sdr() {
    log_info "Configuring RTL-SDR..."

    case $OS in
        ubuntu|centos)
            # Blacklist kernel driver
            if ! grep -q "blacklist dvb_usb_rtl28xxu" /etc/modprobe.d/blacklist-rtl.conf 2>/dev/null; then
                echo "blacklist dvb_usb_rtl28xxu" | sudo tee /etc/modprobe.d/blacklist-rtl.conf > /dev/null
                log_info "RTL-SDR kernel driver blacklisted (reboot may be required)"
            fi

            # Create udev rules for RTL-SDR
            if [ ! -f "/etc/udev/rules.d/20-rtlsdr.rules" ]; then
                echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE="0666"' | sudo tee /etc/udev/rules.d/20-rtlsdr.rules > /dev/null
                sudo udevadm control --reload-rules
                sudo udevadm trigger
            fi
            ;;
    esac

    # Test RTL-SDR
    if rtl_test -t 2>&1 | grep -q "Found"; then
        log_success "RTL-SDR detected ✓"
    else
        log_warning "RTL-SDR not detected. Please check USB connection and reboot if necessary."
    fi
}

# Initialize configuration
init_config() {
    log_info "Initializing configuration..."

    # Create necessary directories
    mkdir -p data/tles logs recordings models/training_data

    # Check if station.ini exists
    if [ ! -f "configs/station.ini" ]; then
        log_warning "configs/station.ini not found. Please configure your station location."
        log_info "Run: nano configs/station.ini"
    else
        log_success "Configuration file found"
    fi
}

# Setup ML components
setup_ml() {
    log_info "Setting up ML components..."

    source venv/bin/activate

    # Check if training data exists
    if [ ! -d "models/training_data" ] || [ -z "$(ls -A models/training_data 2>/dev/null)" ]; then
        log_warning "No training data found. Run data preparation scripts:"
        log_info "  python scripts/prepare_training_data.py"
        log_info "  python scripts/download_satnogs_data.py"
    fi

    # Check if model weights exist
    if [ ! -f "models/model_v1/model.pth" ]; then
        log_warning "Model weights not found. Run training:"
        log_info "  python models/model_v1/train.py"
    fi

    log_success "ML setup complete"
}

# Test installation
test_installation() {
    log_info "Testing installation..."

    source venv/bin/activate

    # Test Python imports
    python3 -c "import skyfield, scipy, numpy, matplotlib; print('Core dependencies OK')" || {
        log_error "Python dependencies test failed"
        exit 1
    }

    # Test TLE fetching
    if python3 scripts/fetch_tles.py --test; then
        log_success "TLE fetching test passed"
    else
        log_warning "TLE fetching test failed (may be due to network)"
    fi

    log_success "Installation tests completed"
}

# Main setup function
main() {
    echo "=========================================="
    echo "SATx Automated Setup"
    echo "=========================================="
    echo ""

    check_root
    detect_os
    check_requirements

    echo ""
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Setup cancelled"
        exit 0
    fi

    install_system_deps
    install_gr_satellites
    setup_python_env
    configure_rtl_sdr
    init_config
    setup_ml
    test_installation

    echo ""
    echo "=========================================="
    log_success "SATx Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Configure your station: nano configs/station.ini"
    echo "2. Fetch TLE data: python scripts/fetch_tles.py"
    echo "3. Predict passes: python scripts/predict_passes.py"
    echo "4. Start monitoring: python scripts/scheduler.py"
    echo ""
    echo "For ML training:"
    echo "1. Prepare data: python scripts/prepare_training_data.py"
    echo "2. Train model: python models/model_v1/train.py"
    echo ""
    echo "Web dashboard: docker-compose up dashboard"
    echo ""
}

# Run main function
main "$@"
