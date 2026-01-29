from .module_imports import get_key
from uplink.retry.when import status_5xx
from uplink import (
    Consumer,
    get as http_get,
    post,
    patch,
    delete,
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
class _TCO(Consumer):
    """Inteface to TCO resource for the RockyRoad API."""

    def __init__(self, Resource, *args, **kw):
        self._base_url = Resource._services_base_url if USE_SERVICES_API else Resource._base_url
        super().__init__(base_url=self._base_url, *args, **kw)

    def costModel(self):
        return self._Cost_Model(self)

    def maintenance(self):
        return self._Maintenance(self)

    def tasks(self):
        return self._Tasks(self)

    def parts(self):
        return self._Parts(self)

    def logs(self):
        return self._Logs(self)

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class _Cost_Model(Consumer):
        """Inteface to TCO Cost Model resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=Resource._base_url, *args, **kw)

        def machines(self):
            return self._Machines(self)

        @returns.json
        @http_get("calculators/tco/cost-models")
        def list(
                self, is_validated: Query = None, is_maintenance_calculator: Query = None):
            """This call will return list of TCO Cost Model."""

        @returns.json
        @http_get("calculators/tco/cost-models/{uid}")
        def get(self, uid: str):
            """This call will return the specified TCO Cost Model."""

        @delete("calculators/tco/cost-models/{uid}")
        def delete(self, uid: str):
            """This call will delete the TCO Cost Model."""

        @returns.json
        @json
        @post("calculators/tco/cost-models")
        def insert(self, tco_part: Body):
            """This call will create the TCO Cost Model."""

        @json
        @patch("calculators/tco/cost-models/{uid}")
        def update(self, uid: str, tco_part: Body):
            """This call will update the TCO Cost Model."""

        @headers({"Ocp-Apim-Subscription-Key": key})
        @retry(max_attempts=20, when=status_5xx())
        class _Machines(Consumer):
            """Inteface to TCO models resource for the RockyRoad API."""

            def __init__(self, Resource, *args, **kw):
                self._base_url = Resource._base_url
                super().__init__(base_url=Resource._base_url, *args, **kw)

            def catalogs(self):
                return self._Catalogs(self)

            @headers({"Ocp-Apim-Subscription-Key": key})
            @retry(max_attempts=20, when=status_5xx())
            class _Catalogs(Consumer):
                """Inteface to TCO models resource for the RockyRoad API."""

                def __init__(self, Resource, *args, **kw):
                    self._base_url = Resource._base_url
                    super().__init__(base_url=Resource._base_url, *args, **kw)

                @returns.json
                @http_get("calculators/tco/cost-models/machines/catalogs/{uid}")
                def get(self, uid: str):
                    """This call will return the TCO cost model for the specified machine catalog uid."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class _Maintenance(Consumer):
        """Inteface to TCO resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=Resource._base_url, *args, **kw)

        @returns.json
        @http_get("calculators/tco/maintenance")
        def list(self):
            """This call will return list of TCO Maintenances."""

        @returns.json
        @http_get("calculators/tco/cost-models/{tco_cost_model_uid}/maintenance")
        def list_by_cost_model(self, tco_cost_model_uid: str):
            """This call will return list of TCO Maintenances."""

        @returns.json
        @http_get("calculators/tco/maintenance/{uid}")
        def get(self, uid: str):
            """This call will return the specified TCO Maintenance."""

        @delete("calculators/tco/maintenance/{uid}")
        def delete(self, uid: str):
            """This call will delete the TCO Maintenance."""

        @returns.json
        @json
        @post("calculators/tco/cost-models/{tco_cost_model_uid}/maintenance")
        def insert(self, tco_cost_model_uid: str, tco_part: Body):
            """This call will create the TCO Maintenance."""

        @json
        @patch("calculators/tco/maintenance/{uid}")
        def update(self, uid: str, tco_part: Body):
            """This call will update the TCO Maintenance."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class _Parts(Consumer):
        """Inteface to TCO resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=Resource._base_url, *args, **kw)

        def parts(self):
            return self.TCO(self)

        @returns.json
        @http_get("calculators/tco/parts")
        def list(
            self,
            tco_task_uid: Query = None
        ):
            """This call will return list of TCO Parts."""

        @returns.json
        @http_get("calculators/tco/tasks/{tco_task_uid}/parts")
        def list_by_task(
            self,
            tco_task_uid: str
        ):
            """This call will return list of TCO Parts."""

        @returns.json
        @http_get("calculators/tco/parts/{uid}")
        def get(self, uid: str):
            """This call will return the specified TCO Part."""

        @delete("calculators/tco/parts/{uid}")
        def delete(self, uid: str):
            """This call will delete the TCO Part."""

        @returns.json
        @json
        @post("calculators/tco/tasks/{tco_task_uid}/parts")
        def insert(self, tco_task_uid: str, tco_part: Body):
            """This call will create the TCO Part."""

        @json
        @patch("calculators/tco/parts/{uid}")
        def update(self, uid: str, tco_part: Body):
            """This call will update the TCO Part."""


    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class _Tasks(Consumer):
        """Interface to TCO Tasks resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=Resource._base_url, *args, **kw)

        @returns.json
        @http_get("calculators/tco/tasks")
        def list(self, tco_cost_model_uid: Query = None):
            """This call will return list of TCO Tasks."""

        @returns.json
        @http_get("calculators/tco/cost-models/{tco_cost_model_uid}/tasks")
        def list_by_cost_model(self, tco_cost_model_uid: str):
            """This call will return list of TCO Tasks."""

        @returns.json
        @http_get("calculators/tco/tasks/{uid}")
        def get(self, uid: str):
            """This call will return the specified TCO Task."""
        
        @delete("calculators/tco/tasks/{uid}")
        def delete(self, uid: str):
            """This call will delete the TCO Task."""
        
        @returns.json
        @json
        @post("calculators/tco/cost-models/{tco_cost_model_uid}/tasks")
        def insert(self, tco_cost_model_uid: str, tco_task: Body):
            """This call will create the TCO Task."""
        
        @json
        @post("calculators/tco/cost-models/{tco_cost_model_uid}/tasks/batch")
        def insert_batch(self, tco_cost_model_uid: str, tco_tasks: Body):
            """This call will create multiple TCO Tasks."""

        @json
        @patch("calculators/tco/tasks/{uid}")
        def update(self, uid: str, tco_task: Body):
            """This call will update the TCO Task."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class _Logs(Consumer):
        """Interface to TCO Logs resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=Resource._base_url, *args, **kw)

        @returns.json
        @http_get("calculators/tco/logs")
        def list(self):
            """This call will return list of TCO Logs."""

        @returns.json
        @http_get("calculators/tco/cost-models/{tco_cost_model_uid}/logs")
        def list_by_cost_model(self, tco_cost_model_uid: str):
            """This call will return list of TCO Logs."""

        @returns.json
        @http_get("calculators/tco/logs/{uid}")
        def get(self, uid: str):
            """This call will return the specified TCO Log."""

        @delete("calculators/tco/logs/{uid}")
        def delete(self, uid: str):
            """This call will delete the TCO Log."""

        @returns.json
        @json
        @post("calculators/tco/cost-models/{tco_cost_model_uid}/logs")
        def insert(self, tco_cost_model_uid: str, tco_log: Body):
            """This call will create the TCO Log."""

    