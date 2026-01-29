# PyPI Release Package Guide

## Release Files

Successfully generated PyPI distribution packages in `dist/` directory:

1. **Source Distribution**: `agent_android-1.1.0.tar.gz` (33KB)
2. **Wheel Distribution**: `agent_android-1.1.0-py3-none-any.whl` (27KB)

## Package Contents

### Core Modules
- `core/__init__.py` - Package initialization
- `core/android.py` - Main Android device management implementation
- `core/adb_config.py` - ADB configuration
- `core/icon_helper.py` - Icon helper utilities
- `core/multi_device.py` - Multi-device management
- `core/nlp_icon_helper.py` - NLP icon helper
- `core/cli.py` - CLI entry point

### Additional Files
- `README.md` - Project documentation
- `LICENSE` - Apache 2.0 license
- `requirements.txt` - Python dependencies
- `agent-android` - Unix/Linux/macOS standalone CLI script
- `agent-android.bat` - Windows batch script
- `MANIFEST.in` - Package manifest
- `pyproject.toml` - Modern Python project configuration
- `setup.py` - Traditional installation configuration

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install agent-android
```

### Method 2: Install from local wheel package

```bash
pip install dist/agent_android-1.1.0-py3-none-any.whl
```

### Method 3: Install from source package

```bash
pip install dist/agent_android-1.1.0.tar.gz
```

## Usage

### Python API

```python
from core.android import create_android_device

# Create device connection
device = create_android_device()

# Start app
device.start_app("com.example.app")

# Take screenshot
device.screenshot("screen.png")

# Close connection
device.close()
```

### CLI Command Line

After installation, you can use the following commands:

```bash
# List devices
agent-android devices

# Connect to device
agent-android connect

# Get UI snapshot
agent-android snapshot -i

# Tap element
agent-android tap @e1

# Take screenshot
agent-android screenshot screen.png
```

**Note**: CLI functionality requires access to the `agent-android` script in the project source. If only the wheel package is installed, it's recommended to use the Python API.

## System Requirements

- Python 3.7+
- ADB (Android Debug Bridge)
- Android device or emulator

## Dependencies

- `python-dotenv>=0.19.0` - Environment variable management

## Publishing to PyPI

### 1. Create PyPI Account

Visit https://pypi.org/account/register/

### 2. Test Release (TestPyPI)

```bash
# Install twine
pip install twine

# Publish to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ agent-android
```

### 3. Official Release to PyPI

```bash
# Upload to PyPI
python3 -m twine upload dist/*

# Verify
pip install agent-android
```

### API Token Configuration (Recommended)

1. Visit https://pypi.org/manage/account/token/
2. Create a new API token
3. Save token to `~/.pypirc` file:

```
[pypi]
username = __token__
password = <your-token-here>

[testpypi]
username = __token__
password = <your-test-token-here>
```

## Version Information

- **Version**: 1.1.0
- **Status**: Production/Stable ✅ (Published)
- **License**: Apache-2.0
- **Author**: Fast2x
- **Homepage**: https://github.com/Fast2x/agent-android
- **PyPI**: https://pypi.org/project/agent-android/
- **Documentation**: https://github.com/Fast2x/agent-android/blob/main/README.md
- **Issues**: https://github.com/Fast2x/agent-android/issues

## Verify Release Package

```bash
# Check with twine
twine check dist/*

# Test installation
pip install --force-reinstall dist/agent_android-1.1.0-py3-none-any.whl

# Test import
python3 -c "import core; print(core.__file__)"

# Check CLI
which agent-android
```

## Next Steps

1. Confirm all tests pass
2. Test installation on TestPyPI
3. Official release to PyPI
4. Update GitHub releases page
5. Announce new version release

## Release Checklist

- [x] Version number updated
- [x] README.md is up to date
- [x] LICENSE file included
- [x] All dependencies in requirements.txt
- [x] setup.py configured correctly
- [x] pyproject.toml configured correctly
- [x] MANIFEST.in includes all necessary files
- [x] Build successful without errors
- [x] twine check passed
- [x] Published to PyPI ✅
- [x] GitHub documentation updated ✅
- [x] README.md PyPI badges added ✅

## Troubleshooting

### CLI Command Not Available

If the `agent-android` command is not available after installation:

1. Confirm pip installation path is in PATH
2. Or use Python module method: `python3 -m core.cli --help`
3. Or use the `agent-android` script directly from source

### Import Errors

If you encounter import errors, confirm:

1. Python version >= 3.7
2. All dependencies installed: `pip install -r requirements.txt`
3. Package installed correctly: `pip show agent-android`

## Package Statistics

- **Release Date**: 2026-01-14
- **Package Version**: 1.1.0
- **Python Versions**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Supported Platforms**: Windows, Linux, macOS

## Links

- **GitHub Repository**: https://github.com/Fast2x/agent-android
- **PyPI Package**: https://pypi.org/project/agent-android/1.1.0/
- **Documentation**: https://github.com/Fast2x/agent-android/blob/main/README.md
- **Issue Tracker**: https://github.com/Fast2x/agent-android/issues
- **Release Notes**: https://github.com/Fast2x/agent-android/releases

---

Generated: 2026-01-14
Package Version: 1.1.0
Status: Published on PyPI ✅
