# Installation Testing Guide

## ✅ Installation Verification

### 1. Check Package Installation

```bash
pip show agent-android
```

Expected output:
```
Name: agent-android
Version: 1.1.0
...
```

### 2. Test Python API

**IMPORTANT**: Test outside the project directory to avoid importing local source files.

```bash
# Change to a temporary directory
cd /tmp

# Test import
python3 -c "from core.android import create_android_device; print('✅ Import successful')"

# Test module location
python3 -c "import core; print('Core location:', core.__file__)"
```

Expected output:
```
✅ Import successful
Core location: /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/core/__init__.py
```

### 3. Test Python API Usage

Create a test script outside the project directory:

```python
# test_agent_android.py
from core.android import create_android_device

# Create device
device = create_android_device()

# List devices
devices = device.list_devices()
print(f"Found {len(devices)} device(s)")

# Close connection
device.close()
```

Run it:
```bash
cd /tmp
python3 test_agent_android.py
```

## 🔧 Common Issues

### Issue: ModuleNotFoundError

**Problem**: If you're in the project directory, Python imports the local `core/` folder instead of the installed package.

**Solution**: Test in a different directory:
```bash
cd /tmp
python3 -c "from core.android import create_android_device; print('OK')"
```

### Issue: CLI not working

**Current Status**: The CLI entry point `agent-android` is installed but has limited functionality. It's recommended to use the Python API instead.

**Alternative**: Use the standalone script from source:
```bash
git clone https://github.com/Fast2x/agent-android.git
cd agent-android
./agent-android devices
```

## 📦 What Gets Installed

When you install `agent-android` via pip, the following are installed:

1. **Python Package**: `core` module
   - `core.android` - Main Android device management
   - `core.adb_config` - ADB configuration
   - `core.multi_device` - Multi-device support
   - `core.nlp_icon_helper` - NLP icon helper
   - `core.icon_helper` - Icon utilities
   - `core.cli` - CLI entry point

2. **Console Script**: `agent-android` command (limited functionality)

3. **Dependencies**: `python-dotenv`

## 🎯 Recommended Usage

### Python API (Recommended)

```python
from core.android import create_android_device

device = create_android_device()
device.start_app("com.example.app")
device.screenshot("screen.png")
device.close()
```

### CLI from Source

For full CLI functionality, use the source repository:

```bash
git clone https://github.com/Fast2x/agent-android.git
cd agent-android
./agent-android devices
./agent-android connect
```

## 🧪 Complete Test Script

```bash
#!/bin/bash
# test_installation.sh

echo "Testing agent-android installation..."
echo ""

# Check package
echo "1. Checking package installation..."
pip show agent-android > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Package installed"
else
    echo "   ❌ Package not found"
    exit 1
fi

# Test import (outside project dir)
echo ""
echo "2. Testing Python import..."
cd /tmp
python3 -c "from core.android import create_android_device; print('   ✅ Import successful')" 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ API import works"
else
    echo "   ❌ Import failed"
    exit 1
fi

# Return to original dir
cd - > /dev/null

echo ""
echo "All tests passed! ✅"
```

Run tests:
```bash
bash test_installation.sh
```

## 📚 Documentation

- **PyPI**: https://pypi.org/project/agent-android/
- **GitHub**: https://github.com/Fast2x/agent-android
- **Full Docs**: https://github.com/Fast2x/agent-android/blob/main/README.md

---

**Note**: The package installs the `core` Python module, not `agent_android`. Use `from core.android import ...` not `import agent_android`.
