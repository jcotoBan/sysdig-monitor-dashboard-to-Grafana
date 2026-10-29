# Quick Start Guide

## 5-Minute Setup

### Step 1: Install dependencies
```bash
cd ~/Desktop/sysdig-to-grafana-converter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set credentials
```bash
# Set your Sysdig Monitor token
export SYSDIG_MONITOR_TOKEN="your-monitor-token-here"

# Optional: set region (default is US4)
export SYSDIG_MONITOR_URL="https://app.us4.sysdig.com"
```

### Step 3: Pull dashboards from Sysdig Monitor
```bash
python3 convert.py
```

This will:
1. Connect to your Sysdig Monitor instance
2. Display available dashboards
3. Let you select which ones to convert
4. Convert and save them as Grafana dashboards

### Step 4: Import into Grafana

For each converted dashboard:

1. Open Grafana → **Home**
2. Click **Dashboards**
3. Click **New** → **Import**
4. Click **Upload JSON file**
5. Select the converted dashboard (e.g., `my-dashboard_grafana.json`)
6. Select Datasource: **Prometheus** (or your configured datasource)
7. Click **Import**

Done! ✅

## Convert Local File

If you have a local Sysdig Monitor dashboard export:

```bash
python3 convert.py my_dashboard.json -o converted_dashboards/
```

This converts `my_dashboard.json` and saves it to the `converted_dashboards/` directory.

## For Different Regions

If your Sysdig Monitor instance is in a different region than us4:

```bash
# EU Frankfurt
export SYSDIG_MONITOR_TOKEN="your-token"
export SYSDIG_MONITOR_URL="https://eu1.app.sysdig.com"
python3 convert.py

# Or use the --url flag
python3 convert.py --url https://eu1.app.sysdig.com
```

**Regions available:**
- `https://app.sysdig.com` (US1)
- `https://us2.app.sysdig.com` (US2)
- `https://app.us3.sysdig.com` (US3)
- `https://app.us4.sysdig.com` (US4, default)
- `https://eu1.app.sysdig.com` (EU1)
- `https://app.eu2.sysdig.com` (EU2)
- `https://app.au1.sysdig.com` (AU1)
- `https://app.in1.sysdig.com` (IN1)
- `https://app.jp1.sysdig.com` (JP1)

See README.md for complete region reference.

## Troubleshooting

### "Cannot reach Sysdig API" or "Authentication failed"
- Verify token is correct: `echo $SYSDIG_MONITOR_TOKEN`
- Verify region URL is correct for your Sysdig instance
- Check your internet connection

### Command not found
```bash
# Make sure you're in the right directory
cd ~/Desktop/sysdig-to-grafana-converter

# Try with full Python path
/usr/bin/python3 convert.py my_dashboard.json
```

### Queries failing after import to Grafana
- Adjust metric names in Grafana to match your Prometheus setup
- Sysdig metrics often use dots (`.`), Prometheus uses underscores (`_`)
- Example: `container.cpu.usage_percent` → `container_cpu_usage_percent`

### Missing panels
- Check input JSON is valid (use `jq . my_dashboard.json`)
- Verify panel type is supported (see README.md)

## Next Steps

- 📖 Read full [README.md](README.md) for advanced options
- 🔧 Customize metric conversions in `convert.py`
- 📊 Add more panels to your dashboard
- 🚀 Share dashboards between teams

## Support

For issues or feature requests, check:
1. README.md troubleshooting section
2. Grafana documentation
3. Sysdig dashboard JSON format
