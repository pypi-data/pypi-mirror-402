from typing import Literal

import click
from frogml._proto.qwak.models.models_pb2 import DeleteModelResponse

from frogml_cli.commands.models.delete._logic import execute_model_delete
from frogml_cli.commands.ui_tools import output_as_json
from frogml_cli.inner.tools.cli_tools import FrogMLCommand


@click.command("delete", cls=FrogMLCommand)
@click.option("--project-key", metavar="NAME", required=True, help="JFrog Project key")
@click.option("--model-id", metavar="NAME", required=True, help="Model name")
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
def model_delete(
    project_key: str, model_id: str, output_format: Literal["text", "json"]
):
    response: DeleteModelResponse = execute_model_delete(project_key, model_id)

    if output_format == "json":
        output_as_json(response)
    else:
        print(f"Model deleted\nmodel id : {model_id}")
