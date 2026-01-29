from .module_imports import get_key
from uplink.retry.when import status_5xx
from uplink import (
    Consumer,
    delete,
    get as http_get,
    patch,
    post,
    returns,
    headers,
    retry,
    Body,
    json,
    Query,
)

# Module configuration
USE_SERVICES_API = True
key = get_key(use_services_api=USE_SERVICES_API)


@headers({"Ocp-Apim-Subscription-Key": key})
@retry(max_attempts=20, when=status_5xx())
class Price_Reviews(Consumer):
    """Interface to Price Reviews resource for the RockyRoad API."""

    def __init__(self, Resource, *args, **kw):
        self._base_url = Resource._services_base_url if USE_SERVICES_API else Resource._base_url
        super().__init__(base_url=self._base_url, *args, **kw)

    def requests(self):
        return self.__Requests(self)

    def parts(self):
        return self.__Parts(self)

    def logs(self):
        return self.__Logs(self)

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Requests(Consumer):
        """Interface to Price Review Requests resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("price-reviews/requests")
        def list(
            self,
            company_uid: Query = None,
            status: Query = None,
            created_date_from: Query = None,
            created_date_to: Query = None,
            part_number: Query = None,
            company_name: Query = None,
            request_site_uid: Query = None,
            part_site_uid: Query = None,
        ):
            """This call will return detailed price review requests information for the specified criteria."""

        @returns.json
        @http_get("price-reviews/requests/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed price review requests information for the specified criteria."""

        @delete("price-reviews/requests/{uid}")
        def delete(self, uid: str):
            """This call will delete the price review requests for the specified uid."""

        @returns.json
        @json
        @post("price-reviews/requests")
        def insert(self, price_review_request: Body):
            """This call will create a price review requests with the specified parameters."""

        @json
        @patch("price-reviews/requests/{uid}")
        def update(self, uid: str, price_review_request: Body):
            """This call will update the price review requests with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Parts(Consumer):
        """Interface to Price Review Parts resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("price-reviews/parts")
        def list(
            self,
            site_uid: Query = None,
        ):
            """This call will return detailed price review parts information for the specified criteria."""

        @returns.json
        @http_get("price-reviews/requests/{request_uid}/parts")
        def list_by_request(
            self,
            request_uid: str,
        ):
            """This call will return detailed price review parts information for the specified criteria."""

        @returns.json
        @http_get("price-reviews/parts/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed price review parts information for the specified criteria."""

        @delete("price-reviews/parts/{uid}")
        def delete(self, uid: str):
            """This call will delete the price review parts for the specified uid."""

        @returns.json
        @json
        @post("price-reviews/requests/{request_uid}/parts")
        def insert(self, request_uid: str, price_review_part: Body):
            """This call will create a price review parts with the specified parameters."""

        @json
        @patch("price-reviews/parts/{uid}")
        def update(self, uid: str, price_review_part: Body):
            """This call will update the price review parts with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Logs(Consumer):
        """Interface to Price Review Logs resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("price-reviews/logs")
        def list(
            self,
        ):
            """This call will return detailed price review logs information for the specified criteria."""

        @returns.json
        @http_get("price-reviews/requests/{request_uid}/logs")
        def list_by_request(
            self,
            request_uid: str,
        ):
            """This call will return detailed price review logs information for the specified criteria."""

        @returns.json
        @http_get("price-reviews/logs/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed price review logs information for the specified criteria."""

        @delete("price-reviews/logs/{uid}")
        def delete(self, uid: str):
            """This call will delete the price review logs for the specified uid."""

        @returns.json
        @json
        @post("price-reviews/requests/{request_uid}/logs")
        def insert(self, request_uid: str, price_review_log: Body):
            """This call will create a price review log with the specified parameters."""
