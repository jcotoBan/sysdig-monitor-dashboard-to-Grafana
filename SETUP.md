# Setup Guide

## Prerequisites

- Python 3.7+
- Sysdig Monitor account
- Sysdig Monitor API token
- Grafana instance (for importing converted dashboards)

## 1. Clone/Download the Project

```bash
cd ~/Desktop/sysdig-to-grafana-converter
```

## 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Your Credentials

### Option A: Using Environment Variables

```bash
export SYSDIG_MONITOR_TOKEN="your-api-token-here"
```

### Option B: Using .env File

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
nano .env  # or your preferred editor

# Load environment
source .env
```

## 5. Find Your Region

Log into your Sysdig Monitor instance and check the URL:

- `https://app.sysdig.com` → US1
- `https://us2.app.sysdig.com` → US2
- `https://app.us3.sysdig.com` → US3
- `https://app.us4.sysdig.com` → US4 (default)
- `https://eu1.app.sysdig.com` → EU1
- `https://app.eu2.sysdig.com` → EU2
- `https://app.au1.sysdig.com` → AU1
- `https://app.in1.sysdig.com` → IN1
- `https://app.jp1.sysdig.com` → JP1

## 6. Run the Script

### Interactive Mode (Recommended)

```bash
python3 convert.py
```

The script will:
1. Connect to your Sysdig Monitor instance (uses us4 by default)
2. Display all available dashboards
3. Prompt you to select which ones to convert
4. Convert and save them as Grafana JSON files

### For Different Regions

```bash
python3 convert.py --url https://eu1.app.sysdig.com
```

### Local File Mode

```bash
python3 convert.py my_dashboard.json
```

## 7. Import into Grafana

For each converted dashboard:

1. Open Grafana → **Home** → **Dashboards** → **New** → **Import**
2. Click **Upload JSON file**
3. Select the converted dashboard (e.g., `my-dashboard_grafana.json`)
4. Select Datasource: **Prometheus** (or your configured datasource)
5. Click **Import**

## Sharing with Teammates

Give your teammates the command with their region and token:

```bash
cd ~/Desktop/sysdig-to-grafana-converter

# Activate venv
source venv/bin/activate

# Set their token
export SYSDIG_MONITOR_TOKEN="their-token-here"

# Use their region
python3 convert.py --url https://eu1.app.sysdig.com
```

Or as a one-liner:

```bash
SYSDIG_MONITOR_TOKEN="token" python3 convert.py --url https://eu1.app.sysdig.com
```

## Troubleshooting

### "Cannot reach Sysdig API"
- Verify the URL is correct for your region
- Check your internet connection
- Verify you're using the Monitor URL, not Secure URL

### "Authentication failed: Invalid API token"
- Verify your API token is correct
- Check that `SYSDIG_MONITOR_TOKEN` is set correctly
- Try passing token via CLI: `python3 convert.py -t "your-token"`

### "No dashboards found"
- Verify you have at least one dashboard in Sysdig Monitor
- Check that your API token has access to dashboards

### venv activation doesn't work
```bash
# Ensure you're in the project directory
cd ~/Desktop/sysdig-to-grafana-converter

# Try with absolute path
source /Users/juancarlos.coto/Desktop/sysdig-to-grafana-converter/venv/bin/activate
```

## Getting Help

- See README.md for feature details
- See QUICKSTART.md for quick start
- Run `python3 convert.py --help` for command-line options
