"""
CLI entry point for agent-android package

This module provides the console script entry point for PyPI installation.
It wraps the standalone agent-android script.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for the CLI"""
    # Get the location of the installed agent-android script
    # When installed via pip, the script should be in the same directory as this module
    package_dir = Path(__file__).parent.parent

    # Look for the agent-android script in the package directory
    script_path = package_dir / "agent-android"

    if not script_path.exists():
        # Fallback: try to use the module directly
        # Import and run the main function from the package
        try:
            from core.android import AndroidDeviceManager, create_android_device
            from core.multi_device import MultiDeviceManager, create_multi_device_manager
            print("agent-android CLI is not fully configured.")
            print("Please use the Python API instead:")
            print("  from core.android import create_android_device")
            print("  device = create_android_device()")
            sys.exit(1)
        except ImportError as e:
            print(f"Error importing agent-android: {e}", file=sys.stderr)
            sys.exit(1)

    # Execute the script
    try:
        result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error executing agent-android: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
