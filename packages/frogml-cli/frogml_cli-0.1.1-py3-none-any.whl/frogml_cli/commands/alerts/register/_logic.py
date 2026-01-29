import os
from pathlib import Path
from typing import List

from frogml.core.clients.alerts_registry import AlertingRegistryClient
from frogml.core.clients.alerts_registry.channel import Channel

from frogml_cli.inner.file_registry import (
    extract_class_objects,
    list_frogml_python_files,
)
from frogml_cli.inner.tools.cli_tools import ask_yesno
from frogml_cli.tools.utils import frogml_spinner

FROGML_alerts_DELIMITER = "----------------------------------------"


def _register_channels(frogml_python_files, alerts_client, force):
    """
    Register Channels

    Args:
        frogml_python_files: a list of python files containing frogml package imports
        alerts_client: AlertingRegistryClient alerts service client
        force: boolean determining if to force register all encountered Channel objects
    """
    with frogml_spinner(
        begin_text="Looking for channels to register", print_callback=print
    ):
        frogml_channels: List[Channel] = extract_class_objects(
            frogml_python_files, Channel
        )

    print(f"👀 Found {len(frogml_channels)} Channels")
    for channel, source_file_path in frogml_channels:
        channel_id, existing_channel = alerts_client.get_alerting_channel(channel.name)
        if existing_channel:
            if ask_yesno(
                f"Update existing Channel '{channel.name}' from source file '{source_file_path}'?",
                force,
            ):
                alerts_client.update_alerting_channel(
                    channel_id=channel_id, channel=channel
                )
        else:
            if ask_yesno(
                f"Create new Channel '{channel.name}' from source file '{source_file_path}'?",
                force,
            ):
                alerts_client.create_alerting_channel(channel)
    print(FROGML_alerts_DELIMITER)


def execute_register_channel(path: Path, force: bool):
    if not path:
        path = Path.cwd()
    else:
        path = Path(path)

    if path.is_file():
        frogml_python_files = [(str(path), os.path.abspath(path))]
    elif Path.is_dir(path):
        with frogml_spinner(
            begin_text="Recursively looking for python files in input dir",
            print_callback=print,
        ) as sp:
            frogml_python_files = list_frogml_python_files(path, sp)
            print(frogml_python_files)
            print(sp)

    alerts_client = AlertingRegistryClient()
    _register_channels(
        frogml_python_files=frogml_python_files,
        alerts_client=alerts_client,
        force=force,
    )
