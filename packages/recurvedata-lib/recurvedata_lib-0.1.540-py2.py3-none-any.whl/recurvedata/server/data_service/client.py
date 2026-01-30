from recurvedata.client.client import Client
from recurvedata.server.schemas import ConnectionAndVariables
from recurvedata.utils.helpers import get_env_id


class DataServiceClient(Client):
    def get_connection_and_variables(self, project_id: int, project_connection_id: int) -> ConnectionAndVariables:
        params = {
            "env_id": get_env_id(),
            "project_id": project_id,
            "project_connection_id": project_connection_id,
        }
        return self.request(
            "GET",
            path="/api/data-service/connection-and-variable",
            response_model_class=ConnectionAndVariables,
            params=params,
        )
