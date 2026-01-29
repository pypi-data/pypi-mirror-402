from frogml._proto.qwak.models.models_pb2 import ListModelsMetadataResponse
from frogml._proto.qwak.projects.projects_pb2 import GetProjectResponse
from frogml.core.clients.model_group_management import ModelGroupManagementClient
from frogml.core.clients.model_management.client import ModelsManagementClient


def list_models_metadata(project_key: str) -> ListModelsMetadataResponse:
    model_group_response: GetProjectResponse = (
        ModelGroupManagementClient().get_model_group(model_group_name=project_key)
    )
    model_group_id: str = model_group_response.project.spec.project_id

    return ModelsManagementClient().list_models_metadata(model_group_id)
