from typing import List

from frogml.core.automations import Automation
from frogml.core.clients.automation_management.client import AutomationsManagementClient

from frogml_cli.inner.file_registry import extract_class_objects
from frogml_cli.inner.tools.cli_tools import ask_yesno
from frogml_cli.tools.utils import frogml_spinner

DELIMITER = "----------------------------------------"


def register_automations(frogml_python_files: List[str], force: bool):
    """
    Register Automation Entities Objects

    Args:
        frogml_python_files: a list of python files containing frogml package imports
        force: to force
    """
    with frogml_spinner(
        begin_text="Finding Automations to register", print_callback=print
    ):
        frogml_automations: List[Automation] = extract_class_objects(
            frogml_python_files, Automation
        )
    client = AutomationsManagementClient()
    print(f"Found {len(frogml_automations)} Automations")
    for automation, source_file_path in frogml_automations:
        existing_automation = client.get_automation_by_name(automation.name)
        if existing_automation:
            if ask_yesno(
                f"Update existing Automation '{automation.name}' from source file '{source_file_path}'?",
                force,
            ):
                client.update_automation(existing_automation.id, automation.to_proto())
        else:
            if ask_yesno(
                f"Create new Automation '{automation.name}' from source file '{source_file_path}'?",
                force,
            ):
                client.create_automation(automation.to_proto())
    print(DELIMITER)
