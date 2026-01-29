from frogml._proto.qwak.projects.projects_pb2 import GetProjectResponse
from frogml.core.clients.model_group_management.client import ModelGroupManagementClient


def execute_models_list(project_key: str) -> GetProjectResponse:
    return ModelGroupManagementClient().get_model_group(model_group_name=project_key)
