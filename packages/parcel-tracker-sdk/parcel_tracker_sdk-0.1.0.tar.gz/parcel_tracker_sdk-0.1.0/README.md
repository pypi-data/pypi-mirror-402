# ParcelTracker BE Python SDK - Setup Guide

This guide will help you set up and start using the ParcelTracker BE Python SDK.

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/parceltracker-be-python-sdk.git
cd parceltracker-be-python-sdk
```

### 2. Set Up Development Environment

Run the setup script to create a virtual environment and install dependencies:

```bash
./setup_dev.sh
```

This will:
- Create a virtual environment (`.venv`)
- Install all dependencies
- Set up pre-commit hooks
- Create necessary directories

### 3. Activate Virtual Environment

```bash
source .venv/bin/activate
```



## 🛠️ Development Commands

### Run Tests

```bash
pytest tests/ -v
```

### Run Type Checking

```bash
mypy src/parcel_tracker_sdk/
```

### Format Code

```bash
black src/parcel_tracker_sdk/
isort src/parcel_tracker_sdk/
```

### Lint Code

```bash
flake8 src/parcel_tracker_sdk/
```

### Run Pre-commit Hooks

```bash
pre-commit run --all-files
```

## 📦 Building and Packaging

### Install in Development Mode

```bash
pip install -e ".[dev]"
```

### Build Distribution Packages

```bash
python -m build
```

This will create `dist/` directory with `wheel` and `sdist` packages.

### Install from Built Package

```bash
pip install dist/parceltracker_be_python_sdk-0.1.0-py3-none-any.whl
```
