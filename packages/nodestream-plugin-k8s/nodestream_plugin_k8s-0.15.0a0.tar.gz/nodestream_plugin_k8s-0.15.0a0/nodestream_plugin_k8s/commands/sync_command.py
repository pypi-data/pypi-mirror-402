from nodestream.cli import NodestreamCommand
from nodestream.cli.commands.shared_options import (
    PROJECT_FILE_OPTION,
    SCOPE_NAME_OPTION,
)


class SyncCommand(NodestreamCommand):
    name = "k8s sync"
    description = "Sync Nodestream Kubernetes resources. This command will create, update, or delete resources as needed."
    options = [PROJECT_FILE_OPTION, SCOPE_NAME_OPTION]

    async def handle_async(self):
        self.line("k8s sync not yet implemented")
