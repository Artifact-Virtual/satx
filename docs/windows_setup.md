# Windows Setup Guide for SATx

Complete setup instructions for Windows 10/11 users.

---

## Prerequisites

- Windows 10 or Windows 11 (64-bit)
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space
- Administrator access

---

## Option 1: WSL2 (Recommended)

Windows Subsystem for Linux provides the best compatibility with Linux tools.

### 1. Install WSL2

Open PowerShell as Administrator:

```powershell
wsl --install
```

This installs Ubuntu by default. Reboot when prompted.

### 2. Launch Ubuntu

Open "Ubuntu" from Start menu. Create username and password.

### 3. Follow Linux Installation

Now follow the main installation guide:

```bash
cd ~
git clone https://github.com/yourusername/SATx.git
cd SATx
chmod +x scripts/install_tools.sh
./scripts/install_tools.sh
```

### 4. USB Device Access in WSL2

WSL2 requires USB/IP to access RTL-SDR:

**On Windows (PowerShell as Administrator):**

```powershell
# Install usbipd
winget install --interactive --exact dorssel.usbipd-win
```

**List USB devices:**

```powershell
usbipd list
```

**Bind RTL-SDR device (replace BUSID with your device):**

```powershell
usbipd bind --busid 1-1
usbipd attach --wsl --busid 1-1
```

**In WSL2 Ubuntu:**

```bash
lsusb
# Should show: Realtek RTL2838
```

---

## Option 2: Native Windows

Run SDR tools directly on Windows without WSL.

### 1. Install Python

Download Python 3.11 from [python.org](https://www.python.org/downloads/)

☑ Check "Add Python to PATH" during installation

### 2. Install Git

Download from [git-scm.com](https://git-scm.com/download/win)

### 3. Install RTL-SDR Drivers

**Using Zadig:**

1. Download [Zadig](https://zadig.akeo.ie/)
2. Plug in RTL-SDR
3. Run Zadig as Administrator
4. Options → List All Devices
5. Select "Bulk-In, Interface (Interface 0)"
6. Select "WinUSB" driver
7. Click "Replace Driver"

### 4. Install SDR#

1. Download from [airspy.com](https://airspy.com/download/)
2. Extract to `C:\SDRSharp`
3. Run `install-rtlsdr.bat`
4. Test with `SDRSharp.exe`

### 5. Clone SATx Repository

Open PowerShell:

```powershell
cd C:\
git clone https://github.com/yourusername/SATx.git
cd SATx
```

### 6. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

**Note:** Some packages may fail on Windows. Install precompiled versions:

```powershell
# Install numpy, scipy from wheels
pip install numpy scipy --only-binary :all:

# Install PyTorch (CPU version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 7. Install rtl_sdr Command-Line Tools

Download from [RTL-SDR Blog](https://www.rtl-sdr.com/rtl-sdr-quick-start-guide/)

Extract to `C:\rtl-sdr` and add to PATH:

```powershell
$env:Path += ";C:\rtl-sdr"
```

Test:

```powershell
rtl_test -t
```

---

## GPredict Installation

### Download GPredict for Windows

1. Get from [sourceforge.net/projects/gpredict](https://sourceforge.net/projects/gpredict/)
2. Install to default location
3. Launch GPredict
4. File → Update TLEs

---

## Running SATx on Windows

### Configuration

Edit `configs\station.ini` with your location.

### Fetch TLEs

```powershell
python scripts\fetch_tles.py
```

### Predict Passes

```powershell
python scripts\predict_passes.py
```

### Record Pass (Manually)

Windows doesn't support bash scripts directly. Use Python wrapper:

```python
# record_pass.py
import subprocess
import sys

norad_id = sys.argv[1]
freq = sys.argv[2]
sample_rate = sys.argv[3]
duration = sys.argv[4]
output = sys.argv[5]

num_samples = int(duration) * int(sample_rate)

subprocess.run([
    'rtl_sdr',
    '-f', freq,
    '-s', sample_rate,
    '-g', '49',
    '-n', str(num_samples),
    output
])
```

Usage:

```powershell
python record_pass.py 25544 437800000 2400000 500 recordings\iss.iq
```

### Process Recording

```powershell
python scripts\process_recording.py recordings\iss.iq
```

---

## GNU Radio on Windows

### Option 1: Conda (Recommended)

```powershell
# Install Miniconda
# Download from: https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda create -n gnuradio
conda activate gnuradio
conda install -c conda-forge gnuradio
```

### Option 2: Radioconda

Prebuilt GNU Radio + SDR tools:

Download from [github.com/ryanvolz/radioconda](https://github.com/ryanvolz/radioconda)

---

## Troubleshooting

### "RTL-SDR not found"

- Check USB connection
- Verify driver installation with Zadig
- Try different USB port
- Disable kernel driver: Device Manager → RTL28xxU → Disable

### "pip install fails"

- Use precompiled wheels: [www.lfd.uci.edu/~gohlke/pythonlibs/](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
- Install Visual Studio Build Tools
- Use conda instead of pip

### "Permission denied"

- Run PowerShell as Administrator
- Check antivirus isn't blocking

### "Module not found"

- Verify Python version: `python --version` (should be 3.8+)
- Check PATH: `where python`
- Reinstall package: `pip install --force-reinstall PACKAGE`

---

## Alternative Software (Windows-specific)

### SDR Console

Full-featured SDR software:
- Download: [sdr-radio.com](https://www.sdr-radio.com/)
- Supports RTL-SDR, recording, decoding

### WXtoImg

NOAA image decoding:
- Download: [wxtoimgrestored.xyz](https://wxtoimgrestored.xyz/)
- Decode NOAA APT images

### Orbitron

Satellite tracking:
- Download: [www.stoff.pl](http://www.stoff.pl/)
- Alternative to GPredict

---

## Performance Tips

### Increase USB Buffer

Add to `C:\rtl-sdr\rtl_sdr.bat`:

```batch
set RTLSDR_BUFFER_SIZE=2097152
```

### Use Fast Storage

- Record to SSD, not HDD
- Use dedicated disk for recordings

### Close Background Apps

- Disable Windows Search indexing on recording drive
- Close unnecessary programs during recording

---

## Next Steps

Once setup is complete, continue with [Quick Start Guide](quick_start.md).

---

## Resources

- [RTL-SDR Blog Windows Guide](https://www.rtl-sdr.com/rtl-sdr-quick-start-guide/)
- [GNU Radio Windows Installation](https://wiki.gnuradio.org/index.php/WindowsInstall)
- [WSL2 USB Guide](https://github.com/dorssel/usbipd-win)

---

**Windows users can achieve 90% of Linux functionality with WSL2!**
