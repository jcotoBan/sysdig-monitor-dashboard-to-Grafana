#!/usr/bin/env python3
"""
Sysdig Monitor to Grafana Dashboard Converter

Converts Sysdig Monitor dashboard JSON format to Grafana dashboard JSON format.
Supports conversion of dashboard layouts, panels, and metric queries.

Features:
- Pull dashboards directly from Sysdig Monitor API
- Interactive dashboard selection
- Batch convert multiple dashboards
- Local file conversion (fallback)
- Multi-region support (us4, eu1, etc.)
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import uuid
from datetime import datetime
import os
import requests
from urllib.parse import urljoin


class SysdigAPIClient:
    """Client for interacting with Sysdig Monitor API."""

    def __init__(self, api_token: str, api_url: str = "https://app.us4.sysdig.com"):
        """
        Initialize Sysdig Monitor API client.

        Args:
            api_token: Sysdig Monitor API token
            api_url: Base URL for Sysdig Monitor API (default: us4 region)
        """
        self.api_token = api_token
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })

    def get_dashboards(self) -> List[Dict[str, Any]]:
        """Fetch list of available dashboards from Sysdig Monitor (user + templates)."""
        try:
            all_dashboards = []

            # Fetch user-created dashboards
            url = f"{self.api_url}/api/v3/dashboards"
            params = {
                "content": "searchInfo",
                "includePermissions": "true",
                "light": "true"
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            user_dashboards = data.get("dashboards", [])
            all_dashboards.extend(user_dashboards)

            # Fetch OOTB/template dashboards
            template_url = f"{self.api_url}/api/v3/dashboards/templates"
            template_params = {
                "excludeMissing": "true",
                "light": "true",
                "content": "searchInfo"
            }
            response = self.session.get(template_url, params=template_params, timeout=10)
            response.raise_for_status()

            data = response.json()
            template_dashboards = data.get("dashboardTemplates", [])
            # Normalize template field names to match user dashboard structure
            for template in template_dashboards:
                # Use dashboardId as the id field
                if "dashboardId" in template and "id" not in template:
                    template["id"] = template["dashboardId"]
                # Mark templates so we know their type
                template["_isTemplate"] = True
            all_dashboards.extend(template_dashboards)

            return all_dashboards

        except requests.exceptions.ConnectionError:
            print("❌ Connection error: Cannot reach Sysdig Monitor API", file=sys.stderr)
            print(f"   URL: {self.api_url}", file=sys.stderr)
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("❌ Authentication failed: Invalid API token", file=sys.stderr)
            else:
                print(f"❌ API error: {e.response.status_code}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error fetching dashboards: {e}", file=sys.stderr)
            sys.exit(1)

    def get_dashboard(self, dashboard_id: str, is_template: bool = False) -> Dict[str, Any]:
        """Fetch a specific dashboard by ID from Sysdig Monitor."""
        try:
            # Determine which endpoint to use
            if is_template:
                url = f"{self.api_url}/api/v3/dashboards/templates/{dashboard_id}"
            else:
                url = f"{self.api_url}/api/v3/dashboards/{dashboard_id}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("dashboard", data)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ Dashboard not found: {dashboard_id}", file=sys.stderr)
            else:
                print(f"❌ API error: {e.response.status_code}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error fetching dashboard: {e}", file=sys.stderr)
            sys.exit(1)


class SysdigToGrafanaConverter:
    """Converts Sysdig dashboards to Grafana format."""

    def __init__(self, datasource_name: str = "Prometheus"):
        self.datasource_name = datasource_name
        self.uid = str(uuid.uuid4())[:12]

    def convert(self, sysdig_dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Sysdig dashboard to Grafana format."""

        grafana_dashboard = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                        "enable": True,
                        "hide": True,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": [],
            "refresh": "30s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["sysdig-converted"],
            "templating": {"list": []},
            "time": {"from": "now-6h", "to": "now"},
            "timepicker": {},
            "timezone": "browser",
            "title": sysdig_dashboard.get("name", "Converted Dashboard"),
            "uid": self.uid,
            "version": 1,
            "weekStart": ""
        }

        # Convert dashboard settings - use generated description if available
        description = sysdig_dashboard.get("dashboardDescription") or sysdig_dashboard.get("description", "")
        if not description:
            # Generate description from metadata
            description = self._generate_dashboard_description(sysdig_dashboard)
        grafana_dashboard["description"] = description

        # Convert panels
        panels = self._convert_panels(sysdig_dashboard.get("panels", []))
        grafana_dashboard["panels"] = panels

        # Convert variables/templating
        if "variables" in sysdig_dashboard:
            grafana_dashboard["templating"]["list"] = self._convert_variables(
                sysdig_dashboard["variables"]
            )

        return grafana_dashboard

    def _generate_dashboard_description(self, dashboard: Dict[str, Any]) -> str:
        """Generate a description from dashboard metadata if empty."""
        parts = []

        # Add category/group
        category = dashboard.get("category") or dashboard.get("group")
        if category:
            parts.append(f"{category}")

        # Add integration info
        integration = dashboard.get("integrationId")
        if integration and integration != category:
            parts.append(f"({integration})")

        # Add panel count
        panels = dashboard.get("panels", [])
        if panels:
            parts.append(f"• {len(panels)} panels")

        # Add deprecation notice
        if dashboard.get("deprecatedBy"):
            parts.append("⚠️ Deprecated")

        if parts:
            return " ".join(parts)
        return "Converted from Sysdig Monitor"

    def _convert_panels(self, sysdig_panels: List[Dict]) -> List[Dict]:
        """Convert Sysdig panels to Grafana panels."""
        grafana_panels = []

        for idx, sysdig_panel in enumerate(sysdig_panels):
            grafana_panel = self._convert_panel(sysdig_panel, idx)
            grafana_panels.append(grafana_panel)

        return grafana_panels

    def _convert_panel(self, sysdig_panel: Dict, index: int) -> Dict:
        """Convert a single Sysdig panel to Grafana format."""

        panel_type = sysdig_panel.get("panelType", "graph").lower()
        grafana_type = self._map_panel_type(panel_type)

        grafana_panel = {
            "datasource": {"type": "prometheus", "uid": "-100"},
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "barAlignment": 0,
                        "drawStyle": "line",
                        "fillOpacity": 0,
                        "gradientMode": "none",
                        "hideFrom": {
                            "tooltip": False,
                            "viz": False,
                            "legend": False
                        },
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "pointSize": 5,
                        "scaleDistribution": {"type": "linear"},
                        "showPoints": "auto",
                        "spanNulls": False,
                        "stacking": {"group": "A", "mode": "none"},
                        "thresholdsStyle": {"mode": "off"}
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "red", "value": 80}
                        ]
                    }
                },
                "overrides": []
            },
            "gridPos": {
                "h": sysdig_panel.get("height", 8),
                "w": sysdig_panel.get("width", 12),
                "x": sysdig_panel.get("x", index * 12 % 24),
                "y": sysdig_panel.get("y", (index // 2) * 8)
            },
            "id": index + 1,
            "options": {},
            "pluginVersion": "10.0.0",
            "targets": self._convert_targets(sysdig_panel.get("targets", [])),
            "title": sysdig_panel.get("name", f"Panel {index + 1}"),
            "type": grafana_type
        }

        return grafana_panel

    def _convert_targets(self, sysdig_targets: List[Dict]) -> List[Dict]:
        """Convert Sysdig metric queries to Prometheus queries."""
        grafana_targets = []

        for idx, sysdig_target in enumerate(sysdig_targets):
            grafana_target = {
                "datasource": {"type": "prometheus", "uid": "-100"},
                "expr": self._convert_metric_query(sysdig_target),
                "format": "time_series",
                "intervalFactor": 1,
                "legendFormat": sysdig_target.get("legendFormat", "{{metric}}"),
                "refId": chr(65 + idx),  # A, B, C, etc.
            }
            grafana_targets.append(grafana_target)

        return grafana_targets

    def _convert_metric_query(self, sysdig_target: Dict) -> str:
        """Convert Sysdig metric query to Prometheus PromQL."""

        # If it's already a query string, return it
        if isinstance(sysdig_target, str):
            return sysdig_target

        metric = sysdig_target.get("metric", "")
        filters = sysdig_target.get("filters", {})

        # Basic query construction
        if not metric:
            return 'up'

        # Build filter string
        filter_str = ""
        if filters:
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f'{key}="{value}"')
            filter_str = "{" + ",".join(filter_parts) + "}"

        return f"{metric}{filter_str}"

    def _map_panel_type(self, sysdig_type: str) -> str:
        """Map Sysdig panel types to Grafana panel types."""
        type_map = {
            "graph": "timeseries",
            "timeseries": "timeseries",
            "table": "table",
            "stat": "stat",
            "gauge": "gauge",
            "piechart": "piechart",
            "heatmap": "heatmap",
            "histogram": "histogram",
            "logs": "logs",
            "alert": "alertlist",
        }
        return type_map.get(sysdig_type, "timeseries")

    def _convert_variables(self, sysdig_variables: List[Dict]) -> List[Dict]:
        """Convert Sysdig variables to Grafana template variables."""
        grafana_variables = []

        for var in sysdig_variables:
            grafana_var = {
                "current": {
                    "selected": False,
                    "text": var.get("default", ""),
                    "value": var.get("default", "")
                },
                "hide": 0,
                "includeAll": True,
                "label": var.get("name", ""),
                "multi": var.get("multiSelect", False),
                "name": var.get("name", ""),
                "options": self._convert_variable_options(var.get("options", [])),
                "query": var.get("query", ""),
                "type": var.get("type", "query"),
                "useTags": False
            }
            grafana_variables.append(grafana_var)

        return grafana_variables

    def _convert_variable_options(self, sysdig_options: List) -> List[Dict]:
        """Convert variable options to Grafana format."""
        grafana_options = []

        for option in sysdig_options:
            grafana_option = {
                "selected": option.get("selected", False),
                "text": option if isinstance(option, str) else option.get("text", ""),
                "value": option if isinstance(option, str) else option.get("value", "")
            }
            grafana_options.append(grafana_option)

        return grafana_options


def load_sysdig_dashboard(file_path: str) -> Dict:
    """Load a Sysdig dashboard from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_grafana_dashboard(dashboard: Dict, output_path: str) -> None:
    """Save Grafana dashboard to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(dashboard, f, indent=2)


def _generate_description(dashboard: Dict[str, Any]) -> str:
    """Generate a description from dashboard metadata if description is empty."""
    existing_desc = dashboard.get("description", "").strip()
    if existing_desc:
        return existing_desc

    # Build description from available metadata
    parts = []

    # Add category/group
    category = dashboard.get("category") or dashboard.get("group")
    if category:
        parts.append(f"{category} dashboard")

    # Add integration info
    integration = dashboard.get("integrationId")
    if integration and integration != category:
        parts.append(f"for {integration}")

    # Add panel count
    panels = dashboard.get("panels", [])
    if panels:
        panel_count = len(panels)
        parts.append(f"({panel_count} panels)")

    # Add deprecation notice
    if dashboard.get("deprecatedBy"):
        parts.append("⚠️ Deprecated")

    if parts:
        return " ".join(parts)
    return "No description available"


def print_dashboards_menu(dashboards: List[Dict[str, Any]]) -> None:
    """Print interactive dashboard selection menu."""
    print("\n" + "="*70)
    print("📊 Available Sysdig Dashboards")
    print("="*70)

    if not dashboards:
        print("❌ No dashboards found in Sysdig")
        sys.exit(1)

    # Sort by name
    dashboards_sorted = sorted(dashboards, key=lambda x: x.get("name", ""))

    for idx, dashboard in enumerate(dashboards_sorted, 1):
        name = dashboard.get("name", "Unknown")
        dashboard_id = dashboard.get("id", "N/A")
        description = _generate_description(dashboard)
        is_template = dashboard.get("_isTemplate", False)

        # Add template indicator
        template_badge = " [TEMPLATE]" if is_template else ""

        print(f"\n{idx}. {name}{template_badge}")
        print(f"   ID: {dashboard_id}")
        print(f"   Description: {description}")

    print("\n" + "-"*70)


def select_dashboards(dashboards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Interactive menu to select dashboard(s) to convert."""
    dashboards_sorted = sorted(dashboards, key=lambda x: x.get("name", ""))

    print_dashboards_menu(dashboards)

    while True:
        try:
            selection = input(
                "\nSelect dashboard(s) to convert (e.g., '1' or '1,3,5' or 'all'): "
            ).strip().lower()

            if selection == "all":
                return dashboards_sorted

            if selection == "":
                print("❌ Please enter at least one number")
                continue

            # Parse comma-separated numbers
            selected_indices = []
            for part in selection.split(","):
                part = part.strip()
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(dashboards_sorted):
                        selected_indices.append(idx)
                    else:
                        print(f"⚠️  Invalid index: {part}")
                except ValueError:
                    print(f"⚠️  Invalid input: {part}")

            if selected_indices:
                selected = [dashboards_sorted[i] for i in selected_indices]
                print(f"\n✅ Selected {len(selected)} dashboard(s)")
                return selected
            else:
                print("❌ No valid selections. Try again.")

        except KeyboardInterrupt:
            print("\n\n👋 Cancelled")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Sysdig Monitor dashboards to Grafana format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
REGIONS & URLS:
  US East (us1)     → https://app.sysdig.com
  US West 2 (us2)   → https://us2.app.sysdig.com
  US West 3 (us3)   → https://app.us3.sysdig.com
  US West 4 (us4)   → https://app.us4.sysdig.com (default)
  EU Frankfurt (eu1)     → https://eu1.app.sysdig.com
  EU Stockholm (eu2)     → https://app.eu2.sysdig.com
  AU Sydney (au1)   → https://app.au1.sysdig.com
  IN Mumbai (in1)   → https://app.in1.sysdig.com
  JP Tokyo (jp1)    → https://app.jp1.sysdig.com

EXAMPLES:
  # Interactive mode (US4, default)
  python3 convert.py

  # EU region
  python3 convert.py --url https://eu1.app.sysdig.com

  # US2 region
  python3 convert.py --url https://us2.app.sysdig.com

  # Convert local file
  python3 convert.py my_dashboard.json

  # Specify token and region via CLI
  python3 convert.py -t "your-token" --url https://eu1.app.sysdig.com

ENVIRONMENT VARIABLES:
  SYSDIG_MONITOR_TOKEN  Sysdig Monitor API token (required for API mode)
  SYSDIG_MONITOR_URL    Sysdig Monitor API URL (default: https://app.us4.sysdig.com)
        """
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to Sysdig dashboard JSON file (optional, uses API if not provided)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for Grafana dashboards (default: current directory)",
        default="."
    )
    parser.add_argument(
        "-d", "--datasource",
        help="Datasource name in Grafana (default: Prometheus)",
        default="Prometheus"
    )
    parser.add_argument(
        "-t", "--token",
        help="Sysdig Monitor API token (or use SYSDIG_MONITOR_TOKEN env var)",
        default=None
    )
    parser.add_argument(
        "--url",
        help="Sysdig Monitor API URL (default: https://app.us4.sysdig.com)",
        default="https://app.us4.sysdig.com"
    )

    args = parser.parse_args()

    try:
        # Determine mode: API or file-based
        if args.input:
            # File mode: convert local Sysdig dashboard
            _convert_from_file(args.input, args.output, args.datasource)
        else:
            # API mode: fetch dashboards from Sysdig and select interactively
            _convert_from_api(args.token, args.url, args.output, args.datasource)

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def _convert_from_file(input_path: str, output_dir: str, datasource: str) -> None:
    """Convert a local Sysdig dashboard file."""
    # Validate input file
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Determine output path
    output_file = Path(output_dir) / f"{input_file.stem}_grafana.json"

    try:
        # Load Sysdig dashboard
        print(f"📂 Loading dashboard from: {input_path}")
        sysdig_dashboard = load_sysdig_dashboard(input_path)

        # Convert and save
        _convert_and_save(sysdig_dashboard, output_file, datasource)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)


def _convert_from_api(token: Optional[str], api_url: str, output_dir: str, datasource: str) -> None:
    """Fetch dashboards from Sysdig Monitor API and convert selected ones."""
    # Get API token
    if not token:
        token = os.environ.get("SYSDIG_MONITOR_TOKEN")
        if not token:
            print("❌ No API token provided", file=sys.stderr)
            print("   Set SYSDIG_MONITOR_TOKEN environment variable or use -t/--token option")
            sys.exit(1)

    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Connect to Sysdig Monitor API
    print("🔗 Connecting to Sysdig Monitor API...")
    client = SysdigAPIClient(api_token=token, api_url=api_url)

    # Fetch dashboards
    print("📊 Fetching available dashboards from Sysdig Monitor...")
    dashboards = client.get_dashboards()

    if not dashboards:
        print("❌ No dashboards found", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Found {len(dashboards)} dashboard(s)")

    # Interactive selection
    selected = select_dashboards(dashboards)

    # Convert each selected dashboard
    for idx, dashboard_info in enumerate(selected, 1):
        dashboard_id = dashboard_info.get("id")
        dashboard_name = dashboard_info.get("name", f"Dashboard {dashboard_id}")
        is_template = dashboard_info.get("_isTemplate", False)

        dashboard_type = "template" if is_template else "dashboard"
        print(f"\n[{idx}/{len(selected)}] 📥 Fetching {dashboard_type}: {dashboard_name}...")

        # Fetch full dashboard details
        full_dashboard = client.get_dashboard(dashboard_id, is_template=is_template)

        # Prepare output file
        sanitized_name = "".join(c for c in dashboard_name if c.isalnum() or c in "-_")
        output_file = Path(output_dir) / f"{sanitized_name}_grafana.json"

        # Convert and save
        _convert_and_save(full_dashboard, output_file, datasource)


def _convert_and_save(sysdig_dashboard: Dict, output_file: Path, datasource: str) -> None:
    """Convert Sysdig dashboard and save to file."""
    print(f"🔄 Converting to Grafana format...")
    converter = SysdigToGrafanaConverter(datasource_name=datasource)
    grafana_dashboard = converter.convert(sysdig_dashboard)

    # Save Grafana dashboard
    print(f"💾 Saving to: {output_file}")
    save_grafana_dashboard(grafana_dashboard, str(output_file))

    print("✅ Conversion completed!")
    print(f"   Dashboard UID: {converter.uid}")
    print(f"   Title: {grafana_dashboard['title']}")
    print(f"   Panels: {len(grafana_dashboard['panels'])}")
    print(f"   Output: {output_file.absolute()}")


if __name__ == "__main__":
    main()
