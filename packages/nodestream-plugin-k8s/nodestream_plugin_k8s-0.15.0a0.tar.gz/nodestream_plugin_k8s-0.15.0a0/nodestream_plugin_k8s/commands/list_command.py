import json
from typing import Iterable

from nodestream.cli import NodestreamCommand
from nodestream.cli.commands.shared_options import (
    JSON_OPTION,
    PROJECT_FILE_OPTION,
    SCOPE_NAME_OPTION,
)

from ..project_resource_manager import PipelineDesiredState, ProjectResourceManager


class ListCommand(NodestreamCommand):
    name = "k8s list"
    description = "List Nodestream Pipelines Under Kubernetes Management"
    options = [PROJECT_FILE_OPTION, SCOPE_NAME_OPTION, JSON_OPTION]

    def display_as_table(self, items_to_display: Iterable[PipelineDesiredState]):
        fields = PipelineDesiredState.field_names()
        table = self.table(
            fields,
            [
                [str(getattr(item, field_name)) for field_name in fields]
                for item in items_to_display
            ],
        )
        table.render()

    def display_as_json(self, items_to_display: Iterable[PipelineDesiredState]):
        json_string = json.dumps(
            [item.as_dict() for item in items_to_display], indent=4
        )
        self.line(json_string)

    async def handle_async(self):
        project_manager = ProjectResourceManager(self.get_project())
        scope_name = self.option(SCOPE_NAME_OPTION.name)
        items_to_display = (
            mgr.desired_state
            for mgr in project_manager.get_managed_pipelines(scope_name)
        )
        use_json = self.option(JSON_OPTION.name)
        render_method = self.display_as_json if use_json else self.display_as_table
        render_method(items_to_display)
