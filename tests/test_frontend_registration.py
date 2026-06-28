"""Tests for the Pool Manager Lovelace frontend resource registration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.poolman import (
    _async_register_frontend,
    _async_register_lovelace_resource,
)
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
    """The helper should register the bundle (and its source map) and the JS URL once."""
    mock_register = _stub_http(hass)
    with patch("custom_components.poolman.add_extra_js_url") as mock_add_js:
        await _async_register_frontend(hass)
        await _async_register_frontend(hass)  # idempotent second call

    assert mock_register.call_count == 1
    static_paths = mock_register.call_args.args[0]
    url_paths = {p.url_path for p in static_paths}
    assert FRONTEND_URL_PATH in url_paths
    # The shipped bundle includes a source map, served to avoid a console 404.
    assert f"{FRONTEND_URL_PATH}.map" in url_paths

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


def _stub_lovelace(hass: HomeAssistant, mode: str, items: list[dict] | None = None) -> MagicMock:
    """Attach a mock Lovelace data object with a resource collection.

    In ``storage`` mode the resource collection is spec'd as a
    ``ResourceStorageCollection`` so the production ``isinstance`` narrowing
    accepts it; in ``yaml`` mode a plain collection (without the mutation API)
    is used to mimic ``ResourceYAMLCollection``.
    """
    from homeassistant.components.lovelace.resources import ResourceStorageCollection

    if mode == "storage":
        resources = MagicMock(spec=ResourceStorageCollection)
        resources.loaded = True
        resources.async_load = AsyncMock()
        resources.async_items = MagicMock(return_value=list(items or []))
        resources.async_create_item = AsyncMock()
    else:
        # No mutation API — mirrors ResourceYAMLCollection.
        resources = MagicMock()
        resources.async_create_item = MagicMock()

    lovelace_data = MagicMock()
    lovelace_data.resource_mode = mode
    lovelace_data.resources = resources

    from custom_components.poolman import LOVELACE_DATA

    hass.data[LOVELACE_DATA] = lovelace_data
    return resources


async def test_register_lovelace_resource_in_storage_mode(hass: HomeAssistant) -> None:
    """In storage mode the bundle is registered as a module resource."""
    resources = _stub_lovelace(hass, "storage")
    url = f"{FRONTEND_URL_PATH}?v=1.2.3"

    await _async_register_lovelace_resource(hass, url)

    resources.async_create_item.assert_awaited_once_with({"res_type": "module", "url": url})


async def test_register_lovelace_resource_skipped_in_yaml_mode(hass: HomeAssistant) -> None:
    """In YAML resource mode nothing is registered (resources are user-managed)."""
    resources = _stub_lovelace(hass, "yaml")

    await _async_register_lovelace_resource(hass, f"{FRONTEND_URL_PATH}?v=1.2.3")

    resources.async_create_item.assert_not_called()


async def test_register_lovelace_resource_is_idempotent(hass: HomeAssistant) -> None:
    """An already-registered module (ignoring the version query) is not duplicated."""
    existing = [{"id": "abc", "type": "module", "url": f"{FRONTEND_URL_PATH}?v=0.0.1"}]
    resources = _stub_lovelace(hass, "storage", items=existing)

    await _async_register_lovelace_resource(hass, f"{FRONTEND_URL_PATH}?v=9.9.9")

    resources.async_create_item.assert_not_called()
