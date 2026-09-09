"""
Provider registry. Adding a real provider later = write a class implementing
SatelliteProvider, register it here. No other code changes.
"""
from app.satellite.base import SatelliteProvider
from app.satellite.demo_provider import DemoProvider

_PROVIDERS: dict[str, SatelliteProvider] = {
    "demo": DemoProvider(),
    # "sentinel2": Sentinel2Provider(),  # requires COPERNICUS_CLIENT_ID/SECRET env vars
}


def get_provider(name: str = "demo") -> SatelliteProvider:
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {list(_PROVIDERS.keys())}. "
            f"To add a real provider, implement SatelliteProvider and register it "
            f"in app/satellite/registry.py."
        )
    return _PROVIDERS[name]
