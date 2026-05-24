"""Tests for the Pool Manager Lovelace frontend resource registration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman import _async_register_frontend
from custom_components.poolman.const import (
    FRONTEND_DIR,
    FRONTEND_FILENAME,
    FRONTEND_URL_PATH,
)
from tests.conftest import setup_mock_states


def _bundle_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "custom_components"
        / "poolman"
        / FRONTEND_DIR
        / FRONTEND_FILENAME
    )


def _stub_http(hass: HomeAssistant) -> AsyncMock:
    """Attach a mock HTTP component with an async static-path registrar."""
    http = MagicMock()
    http.async_register_static_paths = AsyncMock()
    hass.http = http  # type: ignore[assignment]
    return http.async_register_static_paths


async def test_bundle_is_shipped() -> None:
    """The built JS bundle must be present in the integration package."""
    bundle = _bundle_path()
    assert bundle.is_file(), f"Missing card bundle at {bundle}"
    assert bundle.stat().st_size > 0


async def test_register_frontend_adds_static_path_and_extra_js(
    hass: HomeAssistant,
) -> None:
    """The helper should register the static path and add the JS URL once."""
    mock_register = _stub_http(hass)
    with patch("custom_components.poolman.add_extra_js_url") as mock_add_js:
        await _async_register_frontend(hass)
        await _async_register_frontend(hass)  # idempotent second call

    assert mock_register.call_count == 1
    static_paths = mock_register.call_args.args[0]
    assert len(static_paths) == 1
    assert static_paths[0].url_path == FRONTEND_URL_PATH

    assert mock_add_js.call_count == 1
    url = mock_add_js.call_args.args[1]
    assert url.startswith(f"{FRONTEND_URL_PATH}?v=")


async def test_setup_entry_registers_frontend_once(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Setting up an entry should register the frontend exactly once."""
    assert await async_setup_component(hass, "http", {})
    setup_mock_states(hass)
    mock_config_entry.add_to_hass(hass)

    with (
        patch("custom_components.poolman.add_extra_js_url") as mock_add_js,
        patch.object(
            hass.http,
            "async_register_static_paths",
            wraps=hass.http.async_register_static_paths,
        ) as mock_register,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        # A second explicit call must be a no-op (idempotency guard).
        await _async_register_frontend(hass)

    poolman_calls = [
        call
        for call in mock_register.call_args_list
        if any(getattr(p, "url_path", "") == FRONTEND_URL_PATH for p in call.args[0])
    ]
    assert len(poolman_calls) == 1
    assert mock_add_js.call_count == 1
