from typing import Self

import httpx
from httpx import URL

from ...core import Link, MediaTypes, upload_json, raise_exception_on_error, ClientException
from ...core.hco.action_with_parameters_hco import ActionWithParametersHco
from ...core.hco.hco_base import Hco
from ...core.hco.link_hco import LinkHco
from ...core.hco.unavailable import UnavailableAction, UnavailableLink
from ..hcos.processing_step_hco import ProcessingStepHco, ProcessingStepLink
from ..hcos.processing_step_used_tags_hco import ProcessingStepUsedTagsAdminLink, ProcessingStepUsedTagsLink
from ..hcos.processingstep_query_result_hco import (
    ProcessingStepQueryResultHco,
    ProcessingStepQueryResultLink,
    ProcessingStepQueryResultPaginationLink,
)
from ..known_relations import Relations
from ..model import ProcessingStepQueryParameters
from ..model.sirenentities import ProcessingStepsRootEntity
from ...core.hco.upload_action_hco import UploadAction, UploadParameters


class ProcessingStepQueryAction(ActionWithParametersHco[ProcessingStepQueryParameters]):
    def execute(self, parameters: ProcessingStepQueryParameters) -> ProcessingStepQueryResultHco:
        url = self._execute_returns_url(parameters)
        link = Link.from_url(url, [str(Relations.CREATED_RESSOURCE)], "Created query", MediaTypes.SIREN)
        # resolve link immediately
        return ProcessingStepQueryResultLink.from_link(self._client, link).navigate()

    def default_parameters(self) -> ProcessingStepQueryParameters:
        return self._get_default_parameters(ProcessingStepQueryParameters, ProcessingStepQueryParameters())


class ProcessingStepRegisterNewAction(UploadAction):
    def execute(self, parameters: UploadParameters) -> ProcessingStepLink:
        url = upload_json(self._client, self._action, parameters.json_, parameters.filename)
        raise_exception_on_error(f"Error while uploading", url)

        if not isinstance(url, URL):
            raise ClientException("Upload did not respond with location")

        link = Link.from_url(url, [str(Relations.CREATED_RESSOURCE)], "Created processing-step", MediaTypes.SIREN)
        # resolve link immediately
        return ProcessingStepLink.from_link(self._client, link)


class ProcessingStepsRootLink(LinkHco):
    def navigate(self) -> 'ProcessingStepsRootHco':
        return ProcessingStepsRootHco.from_entity(self._navigate_internal(ProcessingStepsRootEntity), self._client)


class ProcessingStepsRootHco(Hco[ProcessingStepsRootEntity]):
    query_action: ProcessingStepQueryAction | UnavailableAction
    register_new_action: ProcessingStepRegisterNewAction | UnavailableAction

    self_link: ProcessingStepsRootLink
    all_link: ProcessingStepQueryResultPaginationLink | UnavailableLink
    used_tags_admin_link: ProcessingStepUsedTagsAdminLink | UnavailableLink
    used_tags_link: ProcessingStepUsedTagsLink | UnavailableLink

    @classmethod
    def from_entity(cls, entity: ProcessingStepsRootEntity, client: httpx.Client) -> Self:
        instance = cls(client, entity)
        Hco.check_classes(instance._entity.class_, ["ProcessingStepRoot"])

        instance.register_new_action = ProcessingStepRegisterNewAction.from_entity_optional(
            client, instance._entity, "RegisterNewProcessingStep")
        instance.query_action = ProcessingStepQueryAction.from_entity_optional(
            client, instance._entity, "CreateProcessingStepQuery")
        instance.used_tags_link = ProcessingStepUsedTagsLink.from_entity_optional(
            instance._client, instance._entity, Relations.USED_TAGS)
        instance.used_tags_admin_link = ProcessingStepUsedTagsAdminLink.from_entity_optional(
            instance._client, instance._entity, Relations.USED_TAGS_ADMIN)
        instance.self_link = ProcessingStepsRootLink.from_entity(
            instance._client, instance._entity, Relations.SELF)
        instance.all_link = ProcessingStepQueryResultPaginationLink.from_entity_optional(
            instance._client, instance._entity, Relations.ALL)

        return instance
