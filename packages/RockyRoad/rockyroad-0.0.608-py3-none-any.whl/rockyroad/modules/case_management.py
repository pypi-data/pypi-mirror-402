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
class Case_Management(Consumer):
    """Interface to Case Management resource for the RockyRoad API."""

    def __init__(self, Resource, *args, **kw):
        self._base_url = Resource._services_base_url if USE_SERVICES_API else Resource._base_url
        super().__init__(base_url=self._base_url, *args, **kw)

    def cases(self):
        return self.__Cases(self)

    def case_types(self):
        return self.__Case_Types(self)

    def case_priorities(self):
        return self.__Case_Priorities(self)

    def case_statuses(self):
        return self.__Case_Statuses(self)

    def case_origins(self):
        return self.__Case_Origins(self)
    
    def team_members(self):
        return self.__Team_Members(self)

    def contacts(self):
        return self.__Contacts(self)

    def timelines(self):
        return self.__Timelines(self)

    def attachments(self):
        return self.__Attachments(self)

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Cases(Consumer):
        """Interface to Cases resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/cases")
        def list(
            self,
            case_type_uid: Query = None,
            priority_uid: Query = None,
            status_uid: Query = None,
            origin_uid: Query = None,
            owner_team_member_uid: Query = None,
            customer_contact_uid: Query = None,
            customer_company_uid: Query = None,
            machine_uid: Query = None,
            is_escalated: Query = None,
        ):
            """This call will return detailed case information for the specified criteria."""

        @returns.json
        @http_get("case-management/cases/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed case information for the specified criteria."""

        @delete("case-management/cases/{uid}")
        def delete(self, uid: str):
            """This call will delete the case for the specified uid."""

        @returns.json
        @json
        @post("case-management/cases")
        def insert(self, case: Body):
            """This call will create a case with the specified parameters."""

        @json
        @patch("case-management/cases/{uid}")
        def update(self, uid: str, case: Body):
            """This call will update the case with the specified parameters."""
    
    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Case_Types(Consumer):
        """Interface to Case Types resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/case-types")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed case information for the specified criteria."""

        @returns.json
        @http_get("case-management/case-types/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed case type information for the specified criteria."""

        @delete("case-management/case-types/{uid}")
        def delete(self, uid: str):
            """This call will delete the case type for the specified uid."""

        @returns.json
        @json
        @post("case-management/case-types")
        def insert(self, case_type: Body):
            """This call will create a case type with the specified parameters."""

        @json
        @patch("case-management/case-types/{uid}")
        def update(self, uid: str, case_type: Body):
            """This call will update the case type with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Case_Priorities(Consumer):
        """Interface to Cases resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/case-priorities")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed case information for the specified criteria."""

        @returns.json
        @http_get("case-management/case-priorities/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed case priority information for the specified criteria."""

        @delete("case-management/case-priorities/{uid}")
        def delete(self, uid: str):
            """This call will delete the case priority for the specified uid."""

        @returns.json
        @json
        @post("case-management/case-priorities")
        def insert(self, case_priority: Body):
            """This call will create a case priority with the specified parameters."""

        @json
        @patch("case-management/case-priorities/{uid}")
        def update(self, uid: str, case_priority: Body):
            """This call will update the case priority with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Case_Origins(Consumer):
        """Interface to Cases resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/case-origins")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed case origin information for the specified criteria."""

        @returns.json
        @http_get("case-management/case-origins/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed case origin information for the specified criteria."""

        @delete("case-management/case-origins/{uid}")
        def delete(self, uid: str):
            """This call will delete the case origin for the specified uid."""

        @returns.json
        @json
        @post("case-management/case-origins")
        def insert(self, case_origin: Body):
            """This call will create a case origin with the specified parameters."""

        @json
        @patch("case-management/case-origins/{uid}")
        def update(self, uid: str, case_origin: Body):
            """This call will update the case origin with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Case_Statuses(Consumer):
        """Interface to Cases resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/case-statuses")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed case status information for the specified criteria."""

        @returns.json
        @http_get("case-management/case-statuses/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed case status information for the specified criteria."""

        @delete("case-management/case-statuses/{uid}")
        def delete(self, uid: str):
            """This call will delete the case status for the specified uid."""

        @returns.json
        @json
        @post("case-management/case-statuses")
        def insert(self, case_status: Body):
            """This call will create a case status with the specified parameters."""

        @json
        @patch("case-management/case-statuses/{uid}")
        def update(self, uid: str, case_status: Body):
            """This call will update the case status with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Team_Members(Consumer):
        """Interface to Team Members resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/team-members")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed team member information for the specified criteria."""

        @returns.json
        @http_get("case-management/team-members/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed team member information for the specified criteria."""

        @delete("case-management/team-members/{uid}")
        def delete(self, uid: str):
            """This call will delete the team member for the specified uid."""

        @returns.json
        @json
        @post("case-management/team-members")
        def insert(self, team_member: Body):
            """This call will create a team member with the specified parameters."""

        @json
        @patch("case-management/team-members/{uid}")
        def update(self, uid: str, team_member: Body):
            """This call will update the team member with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Contacts(Consumer):
        """Interface to Contacts resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/contacts")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed contact information for the specified criteria."""

        @returns.json
        @http_get("case-management/contacts/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed contact information for the specified criteria."""

        @delete("case-management/contacts/{uid}")
        def delete(self, uid: str):
            """This call will delete the contact for the specified uid."""

        @returns.json
        @json
        @post("case-management/contacts")
        def insert(self, contact: Body):
            """This call will create a contact with the specified parameters."""

        @json
        @patch("case-management/contacts/{uid}")
        def update(self, uid: str, contact: Body):
            """This call will update the contact with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Timelines(Consumer):
        """Interface to Timelines resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/timelines")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed timeline information for the specified criteria."""

        @returns.json
        @http_get("case-management/timelines/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed timeline information for the specified criteria."""

        @delete("case-management/timelines/{uid}")
        def delete(self, uid: str):
            """This call will delete the timeline for the specified uid."""

        @returns.json
        @json
        @post("case-management/cases/{case_uid}/timelines")
        def insert(self, case_uid: str, timeline: Body):
            """This call will create a timeline with the specified parameters."""

        @json
        @patch("case-management/timelines/{uid}")
        def update(self, uid: str, timeline: Body):
            """This call will update the timeline with the specified parameters."""

    @headers({"Ocp-Apim-Subscription-Key": key})
    @retry(max_attempts=20, when=status_5xx())
    class __Attachments(Consumer):
        """Interface to Attachments resource for the RockyRoad API."""

        def __init__(self, Resource, *args, **kw):
            self._base_url = Resource._base_url
            super().__init__(base_url=self._base_url, *args, **kw)

        @returns.json
        @http_get("case-management/attachments")
        def list(
            self,
            is_active: Query = None,
        ):
            """This call will return detailed attachment information for the specified criteria."""

        @returns.json
        @http_get("case-management/cases/{case_uid}/attachments")
        def list_by_case(
            self,
            case_uid: str,
            is_internal: Query = None,
        ):
            """This call will return detailed attachment information for the specified criteria."""

        @returns.json
        @http_get("case-management/timelines/{timeline_uid}/attachments")
        def list_by_timeline(
            self,
            timeline_uid: str,
            is_internal: Query = None,
        ):
            """This call will return detailed attachment information for the specified criteria."""

        @returns.json
        @http_get("case-management/attachments/{uid}")
        def get(
            self,
            uid: str,
        ):
            """This call will return detailed attachment information for the specified criteria."""

        @delete("case-management/attachments/{uid}")
        def delete(self, uid: str):
            """This call will delete the attachment for the specified uid."""

        @returns.json
        @json
        @post("case-management/cases/{case_uid}/attachments")
        def insert_by_case(self, case_uid: str, attachment: Body):
            """This call will create an attachment with the specified parameters."""

        @json
        @post("case-management/timelines/{timeline_uid}/attachments")
        def insert_by_timeline(self, timeline_uid: str, attachment: Body):
            """This call will create an attachment with the specified parameters."""

        @json
        @patch("case-management/attachments/{uid}")
        def update(self, uid: str, attachment: Body):
            """This call will update the attachment with the specified parameters."""