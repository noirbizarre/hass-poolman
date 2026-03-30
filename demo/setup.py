#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "niquests[ws]",
#     "pyyaml",
# ]
# ///
"""Automated setup for the Home Assistant dev instance.

Downloads custom card JS bundles, waits for HA to start, onboards a
test user, creates storage-mode dashboards via WebSocket API, and
configures Pool Manager.  Fully idempotent.

Run with ``uv run /demo/setup.py`` (dependencies are declared inline
via PEP 723).

Credentials: admin / admin
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time

import niquests
import yaml

HA_URL = "http://homeassistant:8123"
CLIENT_ID = f"{HA_URL}/"
USERNAME = "admin"
PASSWORD = "admin"  # noqa: S105

# Expected entity IDs created by the Fake Pool Sensor integration
# Chemistry sensors (used in step 2: chemistry)
FAKE_CHEMISTRY_SENSORS = {
    "ph_entity": "sensor.fake_pool_sensor_ph",
    "orp_entity": "sensor.fake_pool_sensor_orp",
    "tac_entity": "sensor.fake_pool_sensor_total_alkalinity",
    "cya_entity": "sensor.fake_pool_sensor_cyanuric_acid",
    "hardness_entity": "sensor.fake_pool_sensor_calcium_hardness",
}

# Filtration sensors (used in step 3: filtration settings)
FAKE_FILTRATION_SENSORS = {
    "temperature_entity": "sensor.fake_pool_sensor_water_temperature",
    "outdoor_temperature_entity": "sensor.fake_pool_sensor_outdoor_temperature",
}

# Custom card JS bundles to download for the custom dashboard.
# Each entry maps a local JS filename to the GitHub repository
# (owner/repo) that publishes it.  The latest release is resolved
# dynamically via the GitHub API at startup.
CUSTOM_CARDS: dict[str, str] = {
    "bubble-card.js": "Clooos/Bubble-Card",
    "button-card.js": "custom-cards/button-card",
    "mini-graph-card-bundle.js": "kalkih/mini-graph-card",
    "pool-monitor-card.js": "wilsto/pool-monitor-card",
    "mushroom.js": "piitaya/lovelace-mushroom",
}


# ---------------------------------------------------------------------------
# HTTP helpers (using niquests)
# ---------------------------------------------------------------------------


def get(url: str, *, token: str | None = None) -> dict | list:
    """HTTP GET, return parsed JSON.  Raises on non-2xx status."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = niquests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def post(
    url: str,
    *,
    token: str | None = None,
    json_data: dict | None = None,
    form_data: dict | None = None,
) -> dict:
    """HTTP POST, return parsed JSON.  Raises on non-2xx status."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = niquests.post(
        url,
        headers=headers,
        json=json_data,
        data=form_data,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]  %(message)s")
log = logging.getLogger("setup")


# ---------------------------------------------------------------------------
# Wait for HA
# ---------------------------------------------------------------------------


def wait_for_ha(timeout: int = 120) -> None:
    """Block until HA is responding on its HTTP port."""
    deadline = time.monotonic() + timeout
    log.info("Waiting for Home Assistant to be ready...")
    last_err = ""
    while time.monotonic() < deadline:
        try:
            resp = niquests.get(f"{HA_URL}/api/", timeout=5)
            if resp.status_code in (200, 401):
                log.info("Home Assistant is ready.")
                return
            last_err = f"HTTP {resp.status_code}"
        except niquests.RequestException as exc:
            last_err = str(exc)
        time.sleep(2)
    log.fatal("Home Assistant did not become ready in time. Last error: %s", last_err)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


def needs_onboarding() -> bool:
    """Return True if the user onboarding step is pending.

    Checks the /api/onboarding endpoint. Returns False if 404 (already
    onboarded -- views are unregistered after completion).
    """
    resp = niquests.get(f"{HA_URL}/api/onboarding", timeout=10)
    if resp.status_code == 404:
        return False
    resp.raise_for_status()
    steps = resp.json()
    return any(s["step"] == "user" and not s["done"] for s in steps)


def exchange_code(auth_code: str) -> str:
    """Exchange an auth code for an access token."""
    resp = post(
        f"{HA_URL}/auth/token",
        form_data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": auth_code,
        },
    )
    return resp["access_token"]


def onboard(timeout: int = 60) -> str:
    """Run the full onboarding flow, return an access token.

    Retries if the onboarding views are not yet registered (404).
    """
    log.info("Running onboarding (creating admin user)...")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = niquests.post(
            f"{HA_URL}/api/onboarding/users",
            json={
                "client_id": CLIENT_ID,
                "name": "Admin",
                "username": USERNAME,
                "password": PASSWORD,
                "language": "en",
            },
            timeout=10,
        )
        if resp.status_code == 404:
            log.info("Onboarding views not ready yet, retrying...")
            time.sleep(2)
            continue
        resp.raise_for_status()
        data = resp.json()
        break
    else:
        log.fatal("Onboarding endpoint never became available.")
        sys.exit(1)

    token = exchange_code(data["auth_code"])

    # Step 2-4: complete remaining onboarding steps
    post(f"{HA_URL}/api/onboarding/core_config", token=token, json_data={})
    post(f"{HA_URL}/api/onboarding/analytics", token=token, json_data={})
    post(
        f"{HA_URL}/api/onboarding/integration",
        token=token,
        json_data={"client_id": CLIENT_ID, "redirect_uri": CLIENT_ID},
    )

    log.info("Onboarding complete.")
    return token


def login() -> str:
    """Login to an already-onboarded HA instance, return an access token."""
    log.info("Already onboarded, logging in...")

    # Start login flow
    resp = post(
        f"{HA_URL}/auth/login_flow",
        json_data={
            "client_id": CLIENT_ID,
            "handler": ["homeassistant", None],
            "redirect_uri": CLIENT_ID,
        },
    )
    flow_id = resp["flow_id"]

    # Submit credentials
    resp = post(
        f"{HA_URL}/auth/login_flow/{flow_id}",
        json_data={
            "client_id": CLIENT_ID,
            "username": USERNAME,
            "password": PASSWORD,
        },
    )

    if resp.get("type") != "create_entry":
        log.fatal("Login failed: %s", resp)
        sys.exit(1)

    token = exchange_code(resp["result"])
    log.info("Logged in.")
    return token


# ---------------------------------------------------------------------------
# Config entries
# ---------------------------------------------------------------------------


def get_config_entries(token: str) -> list[dict]:
    """Return the list of existing config entries."""
    result = get(f"{HA_URL}/api/config/config_entries/entry", token=token)
    assert isinstance(result, list)  # noqa: S101
    return result


def has_integration(entries: list[dict], domain: str) -> bool:
    """Check if a config entry already exists for the given domain."""
    return any(e["domain"] == domain for e in entries)


def create_config_entry(token: str, handler: str, steps: list[dict]) -> dict:
    """Create a config entry via the config flow API.

    Supports multi-step flows by submitting each step's data sequentially.
    """
    # Start flow
    resp = post(
        f"{HA_URL}/api/config/config_entries/flow",
        token=token,
        json_data={"handler": handler},
    )

    if resp.get("type") == "abort":
        log.info("Config flow for %s aborted: %s", handler, resp.get("reason"))
        return resp

    flow_id = resp["flow_id"]

    # Submit each step
    for step_data in steps:
        resp = post(
            f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
            token=token,
            json_data=step_data,
        )

        if resp.get("type") == "create_entry":
            log.info("Created config entry: %s", resp["title"])
            return resp

        if resp.get("type") == "abort":
            log.info("Config flow for %s aborted at step: %s", handler, resp.get("reason"))
            return resp

    log.warning("Unexpected flow result for %s: %s", handler, resp)
    return resp


# ---------------------------------------------------------------------------
# Entity discovery
# ---------------------------------------------------------------------------


def wait_for_entities(
    token: str,
    prefix: str,
    expected_count: int,
    timeout: int = 60,
) -> list[str]:
    """Wait until at least `expected_count` entities with the given prefix exist."""
    log.info("Waiting for %d entities matching '%s*'...", expected_count, prefix)
    matches = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        states = get(f"{HA_URL}/api/states", token=token)
        matches = [s["entity_id"] for s in states if s["entity_id"].startswith(prefix)]
        if len(matches) >= expected_count:
            log.info("Found %d entities: %s", len(matches), ", ".join(sorted(matches)))
            return sorted(matches)
        time.sleep(2)
    log.fatal(
        "Only found %d entities matching '%s*' (expected %d): %s",
        len(matches),
        prefix,
        expected_count,
        ", ".join(sorted(matches)),
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Custom card installation
# ---------------------------------------------------------------------------

GITHUB_API = "https://api.github.com"


def resolve_card_url(filename: str, repo: str) -> str | None:
    """Resolve the download URL for a custom card JS bundle.

    Queries the GitHub API for the latest release of *repo*
    (``owner/repo``) and returns the ``browser_download_url`` of the
    asset whose name matches *filename*.

    Some projects (e.g. Bubble Card) ship their JS bundle in the
    repository ``dist/`` directory instead of as release assets.  When
    no matching asset is found the function falls back to the raw
    ``dist/<filename>`` URL for the tagged release.

    Returns ``None`` when the release or file cannot be found.
    """
    url = f"{GITHUB_API}/repos/{repo}/releases/latest"
    try:
        resp = niquests.get(url, timeout=15)
        resp.raise_for_status()
        release = resp.json()
    except niquests.RequestException as exc:
        log.warning("GitHub API request failed for %s: %s", repo, exc)
        return None

    tag = release.get("tag_name", "")

    # Try release assets first
    for asset in release.get("assets", []):
        if asset.get("name") == filename:
            download_url: str = asset["browser_download_url"]
            log.info("Resolved %s → %s (%s)", filename, tag, download_url)
            return download_url

    # Fallback: try dist/ directory for the tagged version
    if tag:
        dist_url = f"https://raw.githubusercontent.com/{repo}/refs/tags/{tag}/dist/{filename}"
        try:
            head = niquests.head(dist_url, timeout=10)
            if head.status_code == 200:
                log.info("Resolved %s → %s (dist/, %s)", filename, tag, dist_url)
                return dist_url
        except niquests.RequestException:
            pass

    log.warning(
        "Asset %s not found in latest release of %s (%s)",
        filename,
        repo,
        tag or "unknown",
    )
    return None


def download_custom_cards(dest_dir: str = "/config/www") -> None:
    """Download custom card JS bundles to the HA www directory.

    Resolves the latest release for each card from GitHub and downloads
    the matching JS asset.  Files are served by HA at
    ``/local/<filename>``.  Skips files that already exist so the step
    is idempotent.
    """
    os.makedirs(dest_dir, exist_ok=True)
    for filename, repo in CUSTOM_CARDS.items():
        path = os.path.join(dest_dir, filename)
        if os.path.exists(path):
            log.info("%s already downloaded, skipping.", filename)
            continue
        url = resolve_card_url(filename, repo)
        if url is None:
            log.warning("Skipping %s (could not resolve download URL).", filename)
            continue
        log.info("Downloading %s...", filename)
        try:
            resp = niquests.get(url, timeout=30)
            resp.raise_for_status()
            with open(path, "wb") as fh:
                fh.write(resp.content)
            log.info("%s OK (%d bytes)", filename, len(resp.content))
        except niquests.RequestException as exc:
            log.warning("Failed to download %s: %s", filename, exc)


# ---------------------------------------------------------------------------
# Dashboard seeding (storage mode via WebSocket API)
# ---------------------------------------------------------------------------

# Dashboards to create.  The YAML file is resolved relative to the
# ``yaml_dir`` argument of :func:`seed_dashboards`.
DASHBOARDS = [
    {
        "url_path": "pool-builtin",
        "title": "Pool (Built-in)",
        "icon": "mdi:pool",
        "yaml_file": "pool-builtin.yaml",
    },
    {
        "url_path": "pool-custom",
        "title": "Pool (Custom Cards)",
        "icon": "mdi:pool-thermometer",
        "yaml_file": "pool-custom.yaml",
    },
]


def seed_dashboards(token: str, yaml_dir: str = "/demo/dashboards") -> None:
    """Create storage-mode dashboards via the HA WebSocket API.

    For each entry in :data:`DASHBOARDS`, creates a new dashboard and
    populates its configuration from the corresponding YAML file.

    Also registers custom card JS bundles as Lovelace resources so that
    storage-mode dashboards can load them.

    Idempotent: dashboards and resources that already exist are skipped
    so that edits made via the HA UI survive container restarts.  Reset
    with ``docker compose up -V``.
    """
    ws_url = HA_URL.replace("http://", "ws://") + "/api/websocket"
    msg_id = 0

    with niquests.Session() as session:
        resp = session.get(ws_url, timeout=10)
        if resp.status_code != 101 or resp.extension is None:
            log.error("WebSocket connection failed: HTTP %d", resp.status_code)
            return

        ws = resp.extension

        def ws_command(cmd_type: str, **kwargs: object) -> dict:
            """Send a WebSocket command and return the response."""
            nonlocal msg_id
            msg_id += 1
            ws.send_payload(json.dumps({"id": msg_id, "type": cmd_type, **kwargs}))
            raw = ws.next_payload()
            if raw is None:
                return {"success": False, "error": "connection closed"}
            return json.loads(raw)

        try:
            # Authenticate
            ws.next_payload()  # auth_required
            ws.send_payload(json.dumps({"type": "auth", "access_token": token}))
            raw = ws.next_payload()
            auth_resp = json.loads(raw) if raw else {}
            if auth_resp.get("type") != "auth_ok":
                log.error("WebSocket auth failed: %s", auth_resp)
                return

            # Register custom card JS bundles as Lovelace resources
            result = ws_command("lovelace/resources/list")
            existing_resources = {r["url"] for r in result.get("result", [])}
            for filename in CUSTOM_CARDS:
                resource_url = f"/local/{filename}"
                if resource_url in existing_resources:
                    log.info("Resource %s already registered, skipping.", resource_url)
                    continue
                result = ws_command(
                    "lovelace/resources/create",
                    url=resource_url,
                    res_type="module",
                )
                if result.get("success"):
                    log.info("Registered resource: %s", resource_url)
                else:
                    log.warning("Failed to register %s: %s", resource_url, result)

            # List existing dashboards to skip duplicates
            result = ws_command("lovelace/dashboards/list")
            existing = {d["url_path"] for d in result.get("result", [])}

            for dash in DASHBOARDS:
                url_path = dash["url_path"]
                if url_path in existing:
                    log.info("Dashboard %s already exists, skipping.", url_path)
                    continue

                # Create the dashboard
                result = ws_command(
                    "lovelace/dashboards/create",
                    url_path=url_path,
                    title=dash["title"],
                    icon=dash["icon"],
                    require_admin=False,
                    show_in_sidebar=True,
                )
                if not result.get("success"):
                    log.warning("Failed to create dashboard %s: %s", url_path, result)
                    continue
                log.info("Created dashboard: %s", dash["title"])

                # Load YAML config and push it
                yaml_path = os.path.join(yaml_dir, dash["yaml_file"])
                if not os.path.exists(yaml_path):
                    log.warning("%s not found, skipping config.", yaml_path)
                    continue

                with open(yaml_path) as fh:
                    config = yaml.safe_load(fh)

                result = ws_command(
                    "lovelace/config/save",
                    url_path=url_path,
                    config=config,
                )
                if result.get("success"):
                    log.info("Saved config for %s.", url_path)
                else:
                    log.warning("Failed to save config for %s: %s", url_path, result)
        finally:
            ws.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the automated HA setup."""
    # Download custom card JS bundles (runs while HA is still booting)
    log.info("Installing custom dashboard cards...")
    download_custom_cards()

    # Wait for HA to be ready
    wait_for_ha()

    # Authenticate
    token = onboard() if needs_onboarding() else login()

    # Check existing integrations
    entries = get_config_entries(token)

    # Set up Fake Pool Sensor
    if has_integration(entries, "fake_pool_sensor"):
        log.info("Fake Pool Sensor already configured, skipping.")
    else:
        log.info("Setting up Fake Pool Sensor...")
        create_config_entry(
            token,
            "fake_pool_sensor",
            [{"device_name": "Fake Pool Sensor"}],
        )

    # Wait for fake sensor entities to appear
    wait_for_entities(token, "sensor.fake_pool_sensor_", expected_count=7)
    wait_for_entities(token, "switch.fake_pool_sensor_", expected_count=1)

    # Set up Pool Manager (three-step flow: pool basics, chemistry, filtration)
    if has_integration(entries, "poolman"):
        log.info("Pool Manager already configured, skipping.")
    else:
        log.info("Setting up Pool Manager...")
        create_config_entry(
            token,
            "poolman",
            [
                # Step 1: Pool basics (name, volume, shape)
                {
                    "pool_name": "Demo Pool",
                    "volume_m3": 50.0,
                    "shape": "rectangular",
                },
                # Step 2: Chemistry (treatment type + sensors)
                {
                    "treatment": "chlorine",
                    **FAKE_CHEMISTRY_SENSORS,
                },
                # Step 3: Filtration settings
                {
                    "filtration_kind": "sand",
                    "pump_flow_m3h": 10.0,
                    "pump_entity": "switch.fake_pool_sensor_pump",
                    **FAKE_FILTRATION_SENSORS,
                },
            ],
        )

    # Create storage-mode dashboards (editable from the HA UI)
    log.info("Seeding dashboards...")
    seed_dashboards(token)

    log.info("All done! HA is ready at http://localhost:8123 (admin/admin)")
    log.info("  Built-in dashboard: http://localhost:8123/pool-builtin/0")
    log.info("  Custom dashboard:   http://localhost:8123/pool-custom/0")


if __name__ == "__main__":
    main()
