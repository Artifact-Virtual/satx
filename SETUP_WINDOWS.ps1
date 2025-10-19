# SETUP_WINDOWS.ps1
# PowerShell setup script for Windows users

Write-Host "======================================"
Write-Host "SATx Windows Setup"
Write-Host "======================================"
Write-Host ""

# Check Python installation
Write-Host "[1/5] Checking Python installation..."
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion"
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ from python.org"
    exit 1
}

# Check Git installation
Write-Host "[2/5] Checking Git installation..."
try {
    $gitVersion = git --version
    Write-Host "✓ Git found: $gitVersion"
} catch {
    Write-Host "✗ Git not found. Please install Git from git-scm.com"
    exit 1
}

# Install Python dependencies
Write-Host "[3/5] Installing Python packages..."
Write-Host "This may take several minutes..."
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python packages installed"
} else {
    Write-Host "⚠ Some packages failed to install. See errors above."
}

# Create necessary directories
Write-Host "[4/5] Creating directories..."
$dirs = @(
    "recordings",
    "logs",
    "data\tles",
    "models\training_data"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created: $dir"
    }
}

# Check RTL-SDR availability
Write-Host "[5/5] Checking for RTL-SDR..."
try {
    $rtlTest = rtl_test -t 2>&1
    if ($rtlTest -match "Found") {
        Write-Host "✓ RTL-SDR detected!"
    } else {
        Write-Host "⚠ RTL-SDR not detected. Please check USB connection."
    }
} catch {
    Write-Host "⚠ rtl_test not found. Please install RTL-SDR drivers with Zadig."
    Write-Host "  See docs\windows_setup.md for instructions."
}

Write-Host ""
Write-Host "======================================"
Write-Host "Setup Complete!"
Write-Host "======================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit configs\station.ini with your location"
Write-Host "2. Run: python scripts\fetch_tles.py"
Write-Host "3. Run: python scripts\predict_passes.py"
Write-Host ""
Write-Host "For detailed instructions, see:"
Write-Host "  - docs\quick_start.md"
Write-Host "  - docs\windows_setup.md"
Write-Host "  - PROJECT_STATUS.md"
Write-Host ""
