from frogml._proto.qwak.models.models_pb2 import DeleteModelResponse
from frogml._proto.qwak.projects.projects_pb2 import GetProjectResponse
from frogml.core.clients.model_group_management import ModelGroupManagementClient
from frogml.core.clients.model_management import ModelsManagementClient
from frogml.core.exceptions import FrogmlException


def execute_model_delete(project_key: str, model_id: str) -> DeleteModelResponse:
    model_group_response: GetProjectResponse = (
        ModelGroupManagementClient().get_model_group(model_group_name=project_key)
    )
    is_model_exists: bool = any(
        m.model_id == model_id for m in model_group_response.project.models
    )
    if not is_model_exists:
        raise FrogmlException(f"No such model {model_id} for project {project_key}")

    model_group_id: str = model_group_response.project.spec.project_id

    return ModelsManagementClient().delete_model(model_group_id, model_id)
