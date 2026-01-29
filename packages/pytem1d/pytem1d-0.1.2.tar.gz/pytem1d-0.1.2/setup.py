"""
Custom setup.py to build Fortran library during pip install
"""
import os
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithMake(build_py):
    """Custom build command that runs 'make' before building Python package"""

    def run(self):
        # Determine if we need to build (not on Windows if .dll exists)
        lib_dir = Path("src/pytem1d/lib")
        lib_dir.mkdir(parents=True, exist_ok=True)

        # Check if library already exists (e.g., pre-compiled for Windows)
        has_lib = any(
            lib_dir.glob(ext) for ext in ["*.so", "*.dll", "*.dylib"]
        )

        if not has_lib:
            print("=" * 70)
            print("Building Fortran shared library...")
            print("=" * 70)

            # Check if make is available
            try:
                subprocess.run(
                    ["make", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    "ERROR: 'make' not found. Please install build tools:",
                    file=sys.stderr,
                )
                print("  Linux: sudo apt-get install build-essential gfortran")
                print("  macOS: brew install gcc make")
                print("  Windows: Use pre-built binaries or compile manually")
                sys.exit(1)

            # Check if gfortran is available
            try:
                subprocess.run(
                    ["gfortran", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    "ERROR: 'gfortran' not found. Please install:",
                    file=sys.stderr,
                )
                print("  Linux: sudo apt-get install gfortran")
                print("  macOS: brew install gcc")
                sys.exit(1)

            # Run make
            try:
                subprocess.run(["make"], check=True, cwd=".")
                print("✓ Fortran library built successfully")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to build Fortran library: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("✓ Pre-compiled library found, skipping build")

        # Continue with standard build
        super().run()


# Run the setup
if __name__ == "__main__":
    setup(
        cmdclass={
            "build_py": BuildWithMake,
        }
    )
