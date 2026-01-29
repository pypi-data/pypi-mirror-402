from typing import Self

import httpx

from ...core.hco.hco_base import Hco, Property
from ...core.hco.link_hco import LinkHco
from ..hcos.workdata_hco import WorkDataHco
from ..known_relations import Relations
from ..model.sirenentities import OutputDataSlotEntity, WorkDataEntity


class OutputDataSlotLink(LinkHco):
    def navigate(self) -> 'OutputDataSlotHco':
        return OutputDataSlotHco.from_entity(self._navigate_internal(OutputDataSlotEntity), self._pinexq.client)


class OutputDataSlotHco(Hco[OutputDataSlotEntity]):
    title: str | None = Property()
    description: str | None = Property()
    name: str | None = Property()
    media_type: str | None = Property()
    assigned_workdatas: list[WorkDataHco]

    @classmethod
    def from_entity(cls, entity: OutputDataSlotEntity, client: httpx.Client) -> Self:
        instance = cls(client, entity)
        Hco.check_classes(instance._entity.class_, ["OutputDataSlot"])

        instance._extract_workdata()

        return instance

    def _extract_workdata(self):
        self.assigned_workdatas = []

        workdatas: list[WorkDataEntity] = self._entity.find_all_entities_with_relation(Relations.ASSIGNED,
                                                                                       WorkDataEntity)
        if not workdatas:
            return

        self.assigned_workdatas = [WorkDataHco.from_entity(workdata, self._client)
                                   for workdata in workdatas]
