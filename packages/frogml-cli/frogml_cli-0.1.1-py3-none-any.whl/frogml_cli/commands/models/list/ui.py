from datetime import datetime
from typing import Literal

import click
from frogml._proto.qwak.projects.projects_pb2 import GetProjectResponse

from frogml_cli.commands.models.list._logic import execute_models_list
from frogml_cli.commands.ui_tools import output_as_json, output_as_table
from frogml_cli.inner.tools.cli_tools import FrogMLCommand


def parse_model(model):
    return [
        model.model_id,
        model.display_name,
        datetime.fromtimestamp(
            model.created_at.seconds + model.created_at.nanos / 1e9
        ).strftime("%A, %B %d, %Y %I:%M:%S"),
        datetime.fromtimestamp(
            model.last_modified_at.seconds + model.last_modified_at.nanos / 1e9
        ).strftime("%A, %B %d, %Y %I:%M:%S"),
    ]


@click.command("list", cls=FrogMLCommand)
@click.option("--project-key", metavar="NAME", required=True, help="JFrog project key")
@click.option(
    "--format",
    "output_format",
    default="text",
    show_default=True,
    type=click.Choice(["text", "json"], case_sensitive=True),
    metavar="FORMAT",
    required=False,
    help="The formatting style for commands output (choose from text, json)",
)
def model_list(project_key: str, output_format: Literal["text", "json"]):
    get_model_group_response: GetProjectResponse = execute_models_list(project_key)
    columns: list[str] = ["Model id", "Display name", "Creation date", "Last updated"]

    if output_format == "json":
        output_as_json(get_model_group_response)

    else:  # output_format == "text"
        output_as_table(
            get_model_group_response.project.models, parse_model, headers=columns
        )
