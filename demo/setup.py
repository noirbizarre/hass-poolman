#!/usr/bin/env python3
"""Automated setup for the Home Assistant dev instance.

Onboards HA with a test user, creates a Fake Pool Sensor device,
and configures Pool Manager to use it. Fully idempotent.

Credentials: admin / admin
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HA_URL = "http://homeassistant:8123"
CLIENT_ID = f"{HA_URL}/"
USERNAME = "admin"
PASSWORD = "admin"  # noqa: S105

# Expected entity IDs created by the Fake Pool Sensor integration
# Chemistry sensors (used in step 1: pool & sensors)
FAKE_CHEMISTRY_SENSORS = {
    "ph_entity": "sensor.fake_pool_sensor_ph",
    "orp_entity": "sensor.fake_pool_sensor_orp",
    "tac_entity": "sensor.fake_pool_sensor_total_alkalinity",
    "cya_entity": "sensor.fake_pool_sensor_cyanuric_acid",
    "hardness_entity": "sensor.fake_pool_sensor_calcium_hardness",
}

# Filtration sensors (used in step 2: filtration settings)
FAKE_FILTRATION_SENSORS = {
    "temperature_entity": "sensor.fake_pool_sensor_water_temperature",
}


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only, no external dependencies)
# ---------------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    *,
    json_data: dict | None = None,
    form_data: dict | None = None,
    token: str | None = None,
) -> dict:
    """Send an HTTP request and return parsed JSON."""
    headers: dict[str, str] = {}
    body: bytes | None = None

    if json_data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(json_data).encode()
    elif form_data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urllib.parse.urlencode(form_data).encode()

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)  # noqa: S310
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        raw = resp.read()
        return json.loads(raw) if raw else {}


def get(url: str, *, token: str | None = None) -> dict | list:
    """HTTP GET, return parsed JSON."""
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return json.loads(resp.read())


def post(url: str, *, token: str | None = None, **kwargs: dict) -> dict:
    """HTTP POST, return parsed JSON."""
    return _request("POST", url, token=token, **kwargs)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    """Print a timestamped log message."""
    print(f"[setup] {msg}", flush=True)  # noqa: T201


# ---------------------------------------------------------------------------
# Wait for HA
# ---------------------------------------------------------------------------


def wait_for_ha(timeout: int = 120) -> None:
    """Block until HA is responding on its HTTP port."""
    deadline = time.monotonic() + timeout
    log("Waiting for Home Assistant to be ready...")
    last_err = ""
    while time.monotonic() < deadline:
        try:
            get(f"{HA_URL}/api/")
            # 200 means HA is fully ready (unlikely without auth, but fine)
            log("Home Assistant is ready.")
            return
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                log("Home Assistant is ready.")
                return
            last_err = f"HTTP {exc.code}"
            time.sleep(2)
        except (urllib.error.URLError, OSError) as exc:
            last_err = str(exc)
            time.sleep(2)
    log(f"ERROR: Home Assistant did not become ready in time. Last error: {last_err}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


def needs_onboarding() -> bool:
    """Return True if the user onboarding step is pending.

    Checks the /api/onboarding endpoint. Returns False if 404 (already
    onboarded — views are unregistered after completion).
    """
    try:
        steps = get(f"{HA_URL}/api/onboarding")
        return any(s["step"] == "user" and not s["done"] for s in steps)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


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
    log("Running onboarding (creating admin user)...")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = post(
                f"{HA_URL}/api/onboarding/users",
                json_data={
                    "client_id": CLIENT_ID,
                    "name": "Admin",
                    "username": USERNAME,
                    "password": PASSWORD,
                    "language": "en",
                },
            )
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                log("Onboarding views not ready yet, retrying...")
                time.sleep(2)
                continue
            raise
    else:
        log("ERROR: Onboarding endpoint never became available.")
        sys.exit(1)

    token = exchange_code(resp["auth_code"])

    # Step 2-4: complete remaining onboarding steps
    post(f"{HA_URL}/api/onboarding/core_config", token=token, json_data={})
    post(f"{HA_URL}/api/onboarding/analytics", token=token, json_data={})
    post(
        f"{HA_URL}/api/onboarding/integration",
        token=token,
        json_data={"client_id": CLIENT_ID, "redirect_uri": CLIENT_ID},
    )

    log("Onboarding complete.")
    return token


def login() -> str:
    """Login to an already-onboarded HA instance, return an access token."""
    log("Already onboarded, logging in...")

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
        log(f"ERROR: Login failed: {resp}")
        sys.exit(1)

    token = exchange_code(resp["result"])
    log("Logged in.")
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
        log(f"  Config flow for {handler} aborted: {resp.get('reason')}")
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
            log(f"  Created config entry: {resp['title']}")
            return resp

        if resp.get("type") == "abort":
            log(f"  Config flow for {handler} aborted at step: {resp.get('reason')}")
            return resp

    log(f"  Unexpected flow result for {handler}: {resp}")
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
    log(f"Waiting for {expected_count} entities matching '{prefix}*'...")
    matches = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        states = get(f"{HA_URL}/api/states", token=token)
        matches = [s["entity_id"] for s in states if s["entity_id"].startswith(prefix)]
        if len(matches) >= expected_count:
            log(f"  Found {len(matches)} entities: {', '.join(sorted(matches))}")
            return sorted(matches)
        time.sleep(2)
    log(
        f"ERROR: Only found {len(matches)} entities matching '{prefix}*'"
        f" (expected {expected_count}): {', '.join(sorted(matches))}"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the automated HA setup."""
    wait_for_ha()

    # Authenticate
    token = onboard() if needs_onboarding() else login()

    # Check existing integrations
    entries = get_config_entries(token)

    # Set up Fake Pool Sensor
    if has_integration(entries, "fake_pool_sensor"):
        log("Fake Pool Sensor already configured, skipping.")
    else:
        log("Setting up Fake Pool Sensor...")
        create_config_entry(
            token,
            "fake_pool_sensor",
            [{"device_name": "Fake Pool Sensor"}],
        )

    # Wait for fake sensor entities to appear
    wait_for_entities(token, "sensor.fake_pool_sensor_", expected_count=6)

    # Set up Pool Manager (two-step flow: pool & sensors, then filtration)
    if has_integration(entries, "poolman"):
        log("Pool Manager already configured, skipping.")
    else:
        log("Setting up Pool Manager...")
        create_config_entry(
            token,
            "poolman",
            [
                # Step 1: Pool basics + chemistry sensors
                {
                    "pool_name": "Demo Pool",
                    "volume_m3": 50.0,
                    "shape": "rectangular",
                    **FAKE_CHEMISTRY_SENSORS,
                },
                # Step 2: Filtration settings
                {
                    "filtration_kind": "sand",
                    "pump_flow_m3h": 10.0,
                    **FAKE_FILTRATION_SENSORS,
                },
            ],
        )

    log("All done! HA is ready at http://localhost:8123 (admin/admin)")


if __name__ == "__main__":
    main()
