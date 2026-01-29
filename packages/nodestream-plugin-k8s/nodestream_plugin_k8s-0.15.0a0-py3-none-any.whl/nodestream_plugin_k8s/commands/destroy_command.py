from nodestream.cli import NodestreamCommand
from nodestream.cli.commands.shared_options import (
    PROJECT_FILE_OPTION,
    SCOPE_NAME_OPTION,
)


class DestroyCommand(NodestreamCommand):
    name = "k8s destroy"
    description = "Destroy Nodestream Kubernetes resources"
    options = [PROJECT_FILE_OPTION, SCOPE_NAME_OPTION]

    async def handle_async(self):
        self.line("k8s destroy not yet implemented")
