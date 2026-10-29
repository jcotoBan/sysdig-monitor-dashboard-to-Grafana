# Sysdig Monitor to Grafana Dashboard Converter

Convert Sysdig Monitor dashboards to Grafana dashboard JSON format, with support for interactive dashboard selection from your Sysdig Monitor instance.

## Features

- ✅ Pull dashboards directly from Sysdig Monitor API
- ✅ **Multi-region support** — easily switch between all Sysdig Monitor regions
- ✅ Interactive dashboard selection — choose single, multiple, or all dashboards
- ✅ Converts Sysdig dashboard JSON to Grafana dashboard JSON
- ✅ Supports multiple panel types (graph, table, stat, gauge, etc.)
- ✅ Converts metric queries to Prometheus PromQL format
- ✅ Preserves dashboard layout and panel positioning
- ✅ Handles variables and templating
- ✅ Automatic datasource mapping

## Installation

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: System-wide Installation

```bash
pip install requests>=2.25.0
```

## Quick Setup

1. **Install dependencies** (see Installation above)

2. **Set your Sysdig Monitor credentials:**
   ```bash
   # Quick method
   export SYSDIG_MONITOR_TOKEN="your-api-token-here"
   
   # Or copy the .env.example template
   cp .env.example .env
   # Then edit .env with your token and region
   source .env
   ```

3. **Run** (uses us4 region by default):
   ```bash
   python3 convert.py
   ```

   Or specify a different region (see [Regions](#regions) below).

## Regions

Sysdig Monitor has multiple regional endpoints. Choose the one that matches your instance:

| Region Name | Region Code | URL |
|---|---|---|
| US East (Virginia) | `us1` | `https://app.sysdig.com` |
| US West - Oregon | `us2` | `https://us2.app.sysdig.com` |
| US West - GCP | `us3` | `https://app.us3.sysdig.com` |
| **US West - Dallas** | `us4` | `https://app.us4.sysdig.com` ← Default |
| EU - Frankfurt | `eu1` | `https://eu1.app.sysdig.com` |
| EU - Stockholm | `eu2` | `https://app.eu2.sysdig.com` |
| AU - Sydney | `au1` | `https://app.au1.sysdig.com` |
| IN - Mumbai | `in1` | `https://app.in1.sysdig.com` |
| JP - Tokyo | `jp1` | `https://app.jp1.sysdig.com` |

**To find your region:** Log into your Sysdig Monitor instance and check the URL in your browser.

## Usage

### Interactive Mode (Recommended)

Fetch and convert dashboards directly from your Sysdig Monitor instance:

```bash
export SYSDIG_MONITOR_TOKEN="your-api-token-here"
python3 convert.py
```

The script will:
1. Connect to Sysdig Monitor (us4 region by default)
2. Display **all available dashboards** (user-created + OOTB templates)
   - User dashboards appear as: `my_dashboard`
   - Template dashboards appear as: `System Overview [TEMPLATE]`
3. Let you select which to convert (single, multiple, or all)
4. Convert and save them as Grafana JSON files

#### Using a Different Region

Simply add `--url` with your region's endpoint:

```bash
# EU region
export SYSDIG_MONITOR_TOKEN="your-api-token-here"
python3 convert.py --url https://eu1.app.sysdig.com

# US2 region  
python3 convert.py --url https://us2.app.sysdig.com

# AU region
python3 convert.py --url https://app.au1.sysdig.com
```

### File Mode

Convert a locally saved Sysdig Monitor dashboard export:

```bash
python3 convert.py my_dashboard.json -o converted_dashboards/
```

### Advanced Options

```bash
# Set both region and token via CLI
python3 convert.py -t "your-token" --url https://eu1.app.sysdig.com

# Specify custom datasource name in Grafana
python3 convert.py my_dashboard.json -d "MyPrometheus-prod"

# Specify output directory
python3 convert.py -o ./grafana_dashboards/
```

### Help

```bash
python3 convert.py --help
```

## Example Workflows

### Workflow A: API Mode (Recommended) - US4 Region

1. **Set credentials**
   ```bash
   export SYSDIG_MONITOR_TOKEN="your-monitor-api-token"
   ```

2. **Fetch and convert dashboards** (defaults to us4)
   ```bash
   python3 convert.py
   ```
   Then select which dashboards to convert from the interactive menu.

3. **Import into Grafana**
   - Go to Grafana: Home → Dashboards → New → Import
   - Upload each converted dashboard JSON file
   - Select Prometheus datasource
   - Click Import

### Workflow B: API Mode - Different Region (EU)

For teams in other regions, use the `--url` parameter:

```bash
export SYSDIG_MONITOR_TOKEN="your-monitor-api-token"
python3 convert.py --url https://eu1.app.sysdig.com
```

Then select dashboards from the interactive menu and import to Grafana (same as Workflow A step 3).

**Sharing with teammates:** Give them this command (replace token and region):
```bash
SYSDIG_MONITOR_TOKEN="token-here" python3 convert.py --url https://eu1.app.sysdig.com
```

### Workflow C: File Mode

1. **Export dashboard from Sysdig Monitor UI**
   - Open dashboard in Sysdig Monitor
   - Click menu → Export as JSON
   - Save as `my_dashboard.json`

2. **Convert to Grafana**
   ```bash
   python3 convert.py my_dashboard.json
   ```

3. **Import into Grafana**
   - Go to Grafana: Home → Dashboards → New → Import
   - Upload `my_dashboard_grafana.json`
   - Select Prometheus datasource
   - Click Import

## Supported Panel Types

| Sysdig Type | Grafana Type |
|---|---|
| graph | timeseries |
| timeseries | timeseries |
| table | table |
| stat | stat |
| gauge | gauge |
| piechart | piechart |
| heatmap | heatmap |
| histogram | histogram |
| logs | logs |
| alert | alertlist |

## Metric Query Conversion

The converter attempts to convert Sysdig metrics to Prometheus PromQL:

- **Sysdig**: `container.cpu.usage_percent`
- **Grafana**: `container_cpu_usage_percent` (with filters)

### Manual Query Adjustment

If queries don't convert perfectly, you can manually edit them in Grafana UI:

1. Open dashboard in Grafana
2. Edit panel → Edit Query
3. Adjust PromQL as needed
4. Save

## Supported Features

✅ Dashboard metadata (title, description)
✅ Panel layout and positioning
✅ Metric targets and queries
✅ Template variables
✅ Dashboard tags
✅ Time ranges

⚠️ Partial support:
- Complex aggregations (may need manual adjustment)
- Custom drill-down behaviors
- Some Sysdig-specific features

❌ Not supported:
- Real-time alerts (convert separately)
- Sysdig-specific event queries
- Custom JavaScript panels

## Example Sysdig Dashboard Format

```json
{
  "name": "My Dashboard",
  "dashboardDescription": "Production metrics",
  "panels": [
    {
      "name": "CPU Usage",
      "panelType": "graph",
      "width": 12,
      "height": 8,
      "x": 0,
      "y": 0,
      "targets": [
        {
          "metric": "container.cpu.usage_percent",
          "legendFormat": "{{container.name}}",
          "filters": {
            "container.name": "web"
          }
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Queries Not Working
- Ensure Prometheus datasource is available
- Adjust metric names to match your Prometheus setup
- Use Grafana's Query Editor to debug PromQL

### Missing Panels
- Check that input JSON is valid
- Verify all panel types are supported
- Some complex panels may need manual conversion

### Datasource Issues
- Grafana defaults to Prometheus datasource
- Use `-d` flag to specify different datasource
- Manually change in Grafana UI if needed

## Contributing

To add support for more panel types or features, edit the `_map_panel_type()` and `_convert_targets()` methods.

## License

MIT
