import kolena_agents.types.agent as agent_types
from kolena_agents._generated.openapi_client import ApiClient  # type: ignore
from kolena_agents._generated.openapi_client.api import ClientApi  # type: ignore


class Workspace:
    def __init__(self, client: ApiClient) -> None:
        """Initialize the Workspace resource.

        Args:
            client: The configured API client instance.
        """
        self._api = ClientApi(client)

    def list(self) -> agent_types.ListWorkspacesResponse:
        """Get a list of workspaces."""
        return self._api.client_list_workspaces_api_v1_client_workspaces_get()
