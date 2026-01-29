from .module_imports import get_key
from uplink.retry.when import status_5xx
from uplink import (
    Consumer,
    headers,
    retry,
)

# Module configuration
USE_SERVICES_API = True
key = get_key(use_services_api=USE_SERVICES_API)

@headers({"Ocp-Apim-Subscription-Key": key})
@retry(max_attempts=20, when=status_5xx())
class _Calculators(Consumer):
    """Inteface to Calculators resource for the RockyRoad API."""
    from .tco_calculator import _TCO

    def __init__(self, Resource, *args, **kw):
        self._base_url = Resource._base_url
        self._services_base_url = Resource._services_base_url
        base_url = Resource._services_base_url if USE_SERVICES_API else Resource._base_url
        super().__init__(base_url=base_url, *args, **kw)

    def tco(self):
        return self._TCO(self)
