from typing import List, Self

import httpx

from ...core.hco.hco_base import Hco, Property
from ...core.hco.link_hco import LinkHco
from ..known_relations import Relations
from ..model import WorkDataUsedTagsQueryResultEntityAdmin
from ..model.sirenentities import WorkDataUsedTagsQueryResultEntity


class WorkDataUsedTagsQueryResultHto(Hco[WorkDataUsedTagsQueryResultEntity]):
    tags: List[str] | None = Property()

    self_link: 'WorkDataUsedTagsLink'

    @classmethod
    def from_entity(cls, entity: WorkDataUsedTagsQueryResultEntity, client: httpx.Client) -> Self:
        instance = cls(client, entity)

        Hco.check_classes(instance._entity.class_, ["WorkDataUsedTagsQueryResult"])

        instance.self_link = WorkDataUsedTagsLink.from_entity(instance._client, instance._entity, Relations.SELF)

        return instance


class WorkDataUsedTagsLink(LinkHco):
    def navigate(self) -> WorkDataUsedTagsQueryResultHto:
        return WorkDataUsedTagsQueryResultHto.from_entity(self._navigate_internal(WorkDataUsedTagsQueryResultEntity), self._client)


class WorkDataUsedTagsQueryResultAdminHto(Hco[WorkDataUsedTagsQueryResultEntityAdmin]):
    tags: List[str] | None = Property()

    self_link: 'WorkDataUsedTagsAdminLink'

    @classmethod
    def from_entity(cls, entity: WorkDataUsedTagsQueryResultEntityAdmin, client: httpx.Client) -> Self:
        instance = cls(client, entity)

        Hco.check_classes(instance._entity.class_, ["WorkDataUsedTagsAdminQueryResult"])

        instance.self_link = WorkDataUsedTagsAdminLink.from_entity(instance._client, instance._entity, Relations.SELF)

        return instance


class WorkDataUsedTagsAdminLink(LinkHco):
    def navigate(self) -> WorkDataUsedTagsQueryResultAdminHto:
        return WorkDataUsedTagsQueryResultAdminHto.from_entity(self._navigate_internal(WorkDataUsedTagsQueryResultEntityAdmin), self._client)
