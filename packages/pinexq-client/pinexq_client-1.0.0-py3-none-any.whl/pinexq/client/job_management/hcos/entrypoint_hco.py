from enum import StrEnum
from typing import Self

import httpx

from ...core.hco.hco_base import Hco
from ...core.hco.link_hco import LinkHco
from ...core.hco.unavailable import UnavailableLink
from ..known_relations import Relations
from ..model.sirenentities import EntryPointEntity
from .info_hco import InfoLink
from .jobsroot_hco import JobsRootLink
from .processingsteproot_hco import ProcessingStepsRootLink
from .workdataroot_hco import WorkDataRootLink


class EntryPointLink(LinkHco):
    def navigate(self) -> 'EntryPointHco':
        return EntryPointHco.from_entity(self._navigate_internal(EntryPointEntity), self._client)


class EntrypointRelations(StrEnum):
    JOBS_ROOT = "JobsRoot"
    WORKDATA_ROOT = "WorkDataRoot"
    PROCESSINGSTEPS_ROOT = "ProcessingStepsRoot"
    API_EVENTS_ROOT = "ApiEvents"
    INFO = "Info"
    ADMIN = "Admin"


class EntryPointHco(Hco[EntryPointEntity]):
    self_link: EntryPointLink
    job_root_link: JobsRootLink
    work_data_root_link: WorkDataRootLink
    processing_step_root_link: ProcessingStepsRootLink
    info_link: InfoLink
    admin_link: LinkHco | UnavailableLink

    @classmethod
    def from_entity(cls, entity: EntryPointEntity, client: httpx.Client) -> Self:
        instance = cls(client, entity)
        Hco.check_classes(instance._entity.class_, ["EntryPoint"])

        instance.self_link = EntryPointLink.from_entity(
            instance._client, instance._entity, Relations.SELF)
        instance.info_link = InfoLink.from_entity(
            instance._client, instance._entity, EntrypointRelations.INFO)
        instance.job_root_link = JobsRootLink.from_entity(
            instance._client, instance._entity, EntrypointRelations.JOBS_ROOT)
        instance.work_data_root_link = WorkDataRootLink.from_entity(
            instance._client, instance._entity, EntrypointRelations.WORKDATA_ROOT)
        instance.processing_step_root_link = ProcessingStepsRootLink.from_entity(
            instance._client, instance._entity, EntrypointRelations.PROCESSINGSTEPS_ROOT)

        instance.admin_link = LinkHco.from_entity_optional(
            instance._client, instance._entity, EntrypointRelations.ADMIN)

        return instance
