from typing import List, Self

import httpx

from ...core.hco.hco_base import Hco, Property
from ...core.hco.link_hco import LinkHco
from ..known_relations import Relations
from ..model import JobUsedTagsEntityAdmin
from ..model.sirenentities import JobUsedTagsEntity


class JobUsedTagsHco(Hco[JobUsedTagsEntity]):
    tags: List[str] | None = Property()

    self_link: 'JobUsedTagsLink'

    @classmethod
    def from_entity(cls, entity: JobUsedTagsEntity, client: httpx.Client) -> Self:
        instance = cls(client, entity)

        Hco.check_classes(instance._entity.class_, ["JobUsedTags"])

        instance.self_link = JobUsedTagsLink.from_entity(instance._client, instance._entity, Relations.SELF)

        return instance


class JobUsedTagsLink(LinkHco):
    def navigate(self) -> JobUsedTagsHco:
        return JobUsedTagsHco.from_entity(self._navigate_internal(JobUsedTagsEntity), self._client)


class JobUsedTagsAdminHco(Hco[JobUsedTagsEntityAdmin]):
    tags: List[str] | None = Property()

    self_link: 'JobUsedTagsAdminLink'

    @classmethod
    def from_entity(cls, entity: JobUsedTagsEntityAdmin, client: httpx.Client) -> Self:
        instance = cls(client, entity)

        Hco.check_classes(instance._entity.class_, ["JobUsedTagsAdmin"])

        instance.self_link = JobUsedTagsAdminLink.from_entity(instance._client, instance._entity, Relations.SELF)

        return instance


class JobUsedTagsAdminLink(LinkHco):
    def navigate(self) -> JobUsedTagsAdminHco:
        return JobUsedTagsAdminHco.from_entity(self._navigate_internal(JobUsedTagsEntityAdmin), self._client)

