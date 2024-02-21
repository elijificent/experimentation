# pylint: disable=missing-docstring

import uuid

import pytest

from src.database.models import ExperimentParticipant, ExperimentVariant
from src.database.repository import (
    ExperimentParticipantRepository,
    ExperimentVariantRepository,
)
from src.services import ExperimentVariantService

rando: ExperimentParticipant = ExperimentParticipantRepository.create()
variant_uuid = uuid.uuid4()
variant: ExperimentVariant = ExperimentVariantRepository.create(
    name="Southern Variant",
    description="The good ole south",
    variant_uuid=variant_uuid,
    participants=[rando.participant_uuid],
)


def test_update_allocation():
    misc_variant: ExperimentVariant = ExperimentVariantRepository.create(
        name="Misc Variant",
        description="The catch all",
        allocation=3,
    )

    new_variant = ExperimentVariantService.update_allocation(
        misc_variant.variant_uuid, 4.5
    )
    assert new_variant.allocation == 4.5
    assert (
        ExperimentVariantService.get_variant(misc_variant.variant_uuid).allocation
        == 4.5
    )

    with pytest.raises(Exception) as e_info:
        ExperimentVariantService.update_allocation(misc_variant.variant_uuid, -1)

    assert "Allocation must be a positive number" in str(e_info.value)


def test_participant_in_variant():
    assert ExperimentVariantService.participant_in_variant(
        variant_uuid, rando.participant_uuid
    )
    assert not ExperimentVariantService.participant_in_variant(
        variant.variant_uuid, uuid.uuid4()
    )
    assert not ExperimentVariantService.participant_in_variant(
        uuid.uuid4(), rando.participant_uuid
    )
    assert not ExperimentVariantService.participant_in_variant(
        uuid.uuid4(), uuid.uuid4()
    )


def test_add_participant_to_variant():
    with pytest.raises(Exception) as e_info:
        ExperimentVariantService.add_participant_to_variant(
            uuid.uuid4(), rando.participant_uuid
        )
    assert "Variant not found" in str(e_info.value)

    misc_variant: ExperimentVariant = ExperimentVariantRepository.create(
        name="Woohoo",
        description="ah ha",
    )

    new_participant: ExperimentParticipant = ExperimentParticipantRepository.create()
    assert ExperimentVariantService.add_participant_to_variant(
        misc_variant.variant_uuid, new_participant.participant_uuid
    )
    assert not ExperimentVariantService.add_participant_to_variant(
        misc_variant.variant_uuid, new_participant.participant_uuid
    )


def test_get_variant():
    assert ExperimentVariantService.get_variant(variant_uuid) == variant
    assert ExperimentVariantService.get_variant(uuid.uuid4()) is None
