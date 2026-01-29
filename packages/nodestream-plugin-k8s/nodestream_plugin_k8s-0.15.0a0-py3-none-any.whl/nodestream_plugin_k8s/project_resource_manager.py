from dataclasses import asdict, dataclass, fields
from typing import Iterable, List, Optional

from nodestream.project import PipelineDefinition, Project

CRON_SCHEDULE_ANNOTATION_NAME = "nodestream_plugin_k8s_schedule"
PERPETUAL_CONCURRENCY_ANNOTATION_NAME = "nodestream_plugin_k8s_conccurency"

KUBERNETES_MANAGEMENT_ANNOTATIONS = {
    CRON_SCHEDULE_ANNOTATION_NAME,
    PERPETUAL_CONCURRENCY_ANNOTATION_NAME,
}


@dataclass
class PipelineDesiredState:
    pipeline_name: str
    cron_schedule: Optional[str] = None
    perpetual_concurrency: Optional[int] = None

    @classmethod
    def field_names(cls) -> List[str]:
        return [field.name for field in fields(cls)]

    def as_dict(self) -> dict:
        return asdict(self)


class PipelineResourceManager:
    def __init__(self, definition: PipelineDefinition) -> None:
        self.definition = definition

    @staticmethod
    def is_managable(definition: PipelineDefinition) -> bool:
        annotations = definition.configuration.effective_annotations.keys()
        return not annotations.isdisjoint(KUBERNETES_MANAGEMENT_ANNOTATIONS)

    @property
    def desired_state(self) -> PipelineDesiredState:
        cron_schedule = self.definition.configuration.effective_annotations.get(
            CRON_SCHEDULE_ANNOTATION_NAME
        )
        perpetual_concurrency = self.definition.configuration.effective_annotations.get(
            PERPETUAL_CONCURRENCY_ANNOTATION_NAME
        )
        return PipelineDesiredState(
            pipeline_name=self.definition.name,
            cron_schedule=cron_schedule,
            perpetual_concurrency=perpetual_concurrency,
        )


class ProjectResourceManager:
    def __init__(self, project: Project) -> None:
        self.project = project

    def get_managed_pipelines(
        self, scope_name: Optional[str] = None
    ) -> Iterable[PipelineResourceManager]:
        for scope in self.project.get_scopes_by_name(scope_name):
            for pipeline in scope.pipelines_by_name.values():
                if PipelineResourceManager.is_managable(pipeline):
                    yield PipelineResourceManager(pipeline)
